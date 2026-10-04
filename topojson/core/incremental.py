"""
Add and remove features of a computed Topology without recomputing it.

The arcs are edited as a dict {arc index: (n, 2) integer array}: `decode` reads them
from `Topology.output`, `encode` writes them back and renumbers all references. The
junctions follow a full build with `shared_coords=False`: a junction is the start or
end of a path shared by two lines, and every line through a junction is cut there.
"""

import itertools
from collections import Counter, defaultdict

import numpy as np
import shapely
from shapely import geometry
from shapely.strtree import STRtree

from ..ops import (
    bounds,
    compare_bounds,
    cut_line,
    delta_decoding,
    delta_encoding,
    hash_paths,
    quantize,
    remove_collinear_points,
    shared_path_ends,
)


def decode(output):
    return dict(enumerate(delta_decoding(output["arcs"])))


def encode(output, arcs):
    """Write `arcs` to `output` as arcs 0..n-1 and update all references."""
    order = sorted(arcs)
    new = {old: i for i, old in enumerate(order)}
    for seq, _ in _all_sequences(output):
        seq[:] = [new[r] if r >= 0 else ~new[~r] for r in seq]
    output["arcs"] = delta_encoding([arcs[i] for i in order])


def drop_collapsed_rings(output, area):
    """
    Drop the rings without area on the grid (#243): a hole from its polygon, a
    polygon whose exterior collapsed from its geometry. A geometry with nothing left
    becomes a null geometry and keeps its properties. `area` is twice the signed area
    of each arc (`ops.arc_areas`).
    """
    rings = [seq for seq, ring in _all_sequences(output) if ring]
    if not rings:
        return
    refs = np.concatenate(rings)
    signed = np.where(refs >= 0, area[refs], -area[~refs])
    size = np.fromiter(map(len, rings), np.intp, len(rings))
    zero = np.add.reduceat(signed, np.cumsum(size) - size) == 0
    flat = {id(r) for r, z in zip(rings, zero) if z}
    if not flat:
        return

    def drop(geom):
        """Drop the collapsed rings of `geom`; True when nothing is left of it."""
        t = geom.get("type")
        if t == "Feature":
            return drop(geom["geometry"])
        if t == "GeometryCollection":
            parts = geom["geometries"]
            geom["geometries"] = left = [g for g in parts if not drop(g)]
        elif t in ("Polygon", "MultiPolygon"):
            parts = [geom["arcs"]] if t == "Polygon" else geom["arcs"]
            left = [
                [p[0], *(r for r in p[1:] if id(r) not in flat)]
                for p in parts
                if p and id(p[0]) not in flat
            ]
            geom["arcs"] = left if t == "MultiPolygon" else (left or [[]])[0]
        else:
            return False
        if any(parts) and not left:
            geom["type"] = None
            geom.pop("arcs", None)
            geom.pop("geometries", None)
            return True
        return False

    for o in output["objects"].values():
        for g in o["geometries"]:
            drop(g)
    # renumber the arcs that are still used
    arcs = decode(output)
    used = {_arc(r) for seq, _ in _all_sequences(output) for r in seq}
    encode(output, {i: arcs[i] for i in used})


# ---------------------------------------------------------------------------
# geometries
# ---------------------------------------------------------------------------
def _sequences(geom):
    """(arc references, is_ring) of each line and ring; the lists are the ones in the
    geometry, so they can be changed in place."""
    t, arcs = geom.get("type"), geom.get("arcs")
    if t == "Feature":
        return _sequences(geom["geometry"])
    if t == "GeometryCollection":
        return [s for g in geom.get("geometries", []) for s in _sequences(g)]
    if arcs is None:
        return []
    if t == "LineString":
        return [(arcs, False)]
    if t in ("MultiLineString", "Polygon"):
        return [(seq, t == "Polygon") for seq in arcs]
    if t == "MultiPolygon":
        return [(seq, True) for polygon in arcs for seq in polygon]
    raise NotImplementedError(f"geometry type {t!r} is not supported")


def _all_sequences(output):
    geoms = (g for o in output["objects"].values() for g in o["geometries"])
    return [s for g in geoms for s in _sequences(g)]


def _points(geom, mapping=None):
    """Indices into `output["coordinates"]` used by a geometry. With `mapping`, the
    indices are renumbered in place instead."""
    if geom.get("type") == "GeometryCollection":
        return [i for g in geom.get("geometries", []) for i in _points(g, mapping)]
    if not geom.get("reset_coords"):
        return []
    if mapping is None:
        return np.ravel(geom["coordinates"]).tolist()

    def renumber(x):
        return [renumber(y) for y in x] if isinstance(x, list) else mapping[x]

    geom["coordinates"] = renumber(geom["coordinates"])
    return []


def _arc(ref):
    return ref if ref >= 0 else ~ref


def _junctions(arcs, sequences):
    """Points where a line or ring continues from one arc into the next, i.e. where
    it has been cut. Ends of lines are not junctions."""
    points = set()
    for seq, is_ring in sequences:
        nxt = seq[1:] + seq[:1] if is_ring and len(seq) > 1 else seq[1:]
        points.update(
            tuple(arcs[_arc(a)][-1 if a >= 0 else 0]) for a, _ in zip(seq, nxt)
        )
    return points


def _quantized_bbox(output, arcs):
    """Bbox of the quantized arcs and points, in input coordinates."""
    points = [np.reshape(c, (-1, 2)) for c in output["coordinates"]]
    for o in output["objects"].values():
        for g in o["geometries"]:
            # points of a topology read from file hold their coordinates directly
            if g.get("type") in ("Point", "MultiPoint") and not g.get("reset_coords"):
                points.append(np.reshape(g["coordinates"], (-1, 2)))
    bbox = compare_bounds(bounds(list(arcs.values())), bounds(points))
    if not len(bbox):
        return output.get("bbox")
    (kx, ky), (x0, y0) = output["transform"]["scale"], output["transform"]["translate"]
    return tuple(
        float(v) for v in [*np.multiply(bbox, [kx, ky, kx, ky]), x0, y0, x0, y0]
    )


# ---------------------------------------------------------------------------
# remove
# ---------------------------------------------------------------------------
def _replace_pair(seq, is_ring, first, second, new):
    """Replace each consecutive pair (first, second) in `seq` by `new`, for a ring
    also across its end. Returns the number of replacements."""
    if is_ring and len(seq) > 1 and (seq[-1], seq[0]) == (first, second):
        seq[:] = seq[-1:] + seq[:-1]
    out = []
    for ref in seq:
        if out and (out[-1], ref) == (first, second):
            out[-1] = new
        else:
            out.append(ref)
    n = len(seq) - len(out)
    seq[:] = out
    return n


def _merge_redundant_nodes(arcs, sequences, candidates):
    """
    Merge arcs at the `candidates` points that are no longer junctions. As junctions
    are global, a point stops being one only if *all* arc ends there pair up with a
    partner used by exactly the same lines and rings, and every use of the one arc
    continues into the other.
    """
    usage = defaultdict(Counter)
    for s, (seq, _) in enumerate(sequences):
        for ref in seq:
            usage[_arc(ref)][s] += 1
    ends = defaultdict(set)
    for i, c in arcs.items():
        ends[tuple(c[0])].add((i, 0))
        ends[tuple(c[-1])].add((i, -1))

    next_idx = max(arcs, default=-1) + 1
    work = list(candidates)
    # after a merge, its point and the ends of the new arc are appended to `work`;
    # iterating over a list also visits the items appended during the loop
    for pt in work:
        items = sorted(ends.get(pt, ()))
        groups = Counter(frozenset(usage[i].items()) for i, _ in items)
        if any(n % 2 for n in groups.values()):
            continue  # some line diverges here
        for (a, end_a), (b, end_b) in itertools.combinations(items, 2):
            if a == b or usage[a] != usage[b]:
                continue
            ref_a = a if end_a == -1 else ~a  # runs into pt
            ref_b = b if end_b == 0 else ~b  # runs out of pt
            touched = list(usage[a])
            backup = {s: list(sequences[s][0]) for s in touched}
            n = sum(
                _replace_pair(*sequences[s], ref_a, ref_b, next_idx)
                + _replace_pair(*sequences[s], ~ref_b, ~ref_a, ~next_idx)
                for s in touched
            )
            if n != sum(usage[a].values()):
                for s, seq in backup.items():
                    sequences[s][0][:] = seq
                continue
            ca = arcs[a] if ref_a >= 0 else arcs[a][::-1]
            cb = arcs[b] if ref_b >= 0 else arcs[b][::-1]
            merged = remove_collinear_points(np.vstack([ca, cb[1:]]))
            for i in (a, b):
                c = arcs.pop(i)
                ends[tuple(c[0])].discard((i, 0))
                ends[tuple(c[-1])].discard((i, -1))
            arcs[next_idx] = merged
            ends[tuple(merged[0])].add((next_idx, 0))
            ends[tuple(merged[-1])].add((next_idx, -1))
            usage[next_idx] = usage.pop(a)
            del usage[b]
            next_idx += 1
            work += [pt, tuple(merged[0]), tuple(merged[-1])]
            break


def _restart_ring(ring, start, second):
    """Rotate a closed arc to start at `start`, at the occurrence followed (in either
    direction) by `second` if the ring touches itself there. A start that had been
    dropped as collinear is put back on its segment first."""
    body = ring[:-1]
    hit = np.flatnonzero((body == start).all(axis=1))
    if not len(hit):
        ab = np.roll(body, -1, axis=0) - body
        ap, bp = start - body, start - np.roll(body, -1, axis=0)
        cross = ab[:, 0] * ap[:, 1] - ab[:, 1] * ap[:, 0]
        on = np.flatnonzero((cross == 0) & (np.einsum("ij,ij->i", ap, bp) <= 0))
        if not len(on):
            return ring
        body, hit = np.insert(body, on[0] + 1, start, axis=0), [on[0] + 1]
    nxt, prv = np.roll(body, -1, axis=0), np.roll(body, 1, axis=0)
    follows = [h for h in hit if (nxt[h] == second).all() or (prv[h] == second).all()]
    body = np.roll(body, -(follows or hit)[0], axis=0)
    return remove_collinear_points(np.vstack([body, body[:1]]))


def remove_features(output, arcs, ids, object_name, ring_starts=None):
    """
    Remove the features with `ids`, in place. With `ring_starts` ({feature id: [(first
    point, second point), ...]} per ring, on the grid), a ring that is no longer cut
    starts where its input started, as in a full build.
    """
    ids = set(ids)
    obj = output["objects"][object_name]
    removed = [g for g in obj["geometries"] if g.get("id") in ids]
    obj["geometries"] = [g for g in obj["geometries"] if g.get("id") not in ids]
    sequences = _all_sequences(output)

    touched = {_arc(r) for g in removed for seq, _ in _sequences(g) for r in seq}
    candidates = {tuple(arcs[i][e]) for i in touched for e in (0, -1)}
    for i in set(arcs) - {_arc(r) for seq, _ in sequences for r in seq}:
        del arcs[i]
    first_merged = max(arcs, default=-1) + 1
    _merge_redundant_nodes(arcs, sequences, candidates)

    if ring_starts:
        junctions = _junctions(arcs, sequences)
        users = Counter(_arc(r) for seq, _ in sequences for r in seq)
        for g in obj["geometries"]:
            rings = [seq for seq, is_ring in _sequences(g) if is_ring]
            starts = ring_starts.get(g.get("id"), [])
            for seq, start in zip(rings, starts) if len(starts) == len(rings) else ():
                i = _arc(seq[0])
                if (
                    len(seq) == 1
                    and i >= first_merged
                    and users[i] == 1
                    and tuple(arcs[i][0]) not in junctions
                ):
                    arcs[i] = _restart_ring(arcs[i], *np.asarray(start))

    # points: keep the used ones
    geoms = [g for o in output["objects"].values() for g in o["geometries"]]
    used = sorted({i for g in geoms for i in _points(g)})
    output["coordinates"] = [output["coordinates"][i] for i in used]
    mapping = {old: new for new, old in enumerate(used)}
    for g in geoms:
        _points(g, mapping)
    output["bbox"] = _quantized_bbox(output, arcs)


def ring_starts(data, transform):
    """{feature id: [(first point, second point), ...]}: the start of each ring of the
    (multi)polygons in `data` on the grid of `transform`, in the order of the
    topology."""
    parts, part_idx = shapely.get_parts(data.geometry.values, return_index=True)
    rings, ring_idx = shapely.get_rings(parts, return_index=True)
    (kx, ky), (x0, y0) = transform["scale"], transform["translate"]
    xy = [
        np.round(
            (shapely.get_coordinates(shapely.get_point(rings, i)) - [x0, y0]) / [kx, ky]
        )
        .astype(np.int64)
        .tolist()
        for i in (0, 1)
    ]
    out = defaultdict(list)
    for fid, first, second in zip(data.index[part_idx[ring_idx]], *xy):
        out[fid].append((first, second))
    return out


# ---------------------------------------------------------------------------
# add
# ---------------------------------------------------------------------------
def _ref(piece, arc, idx):
    """Reference to arc `idx` in the direction of `piece`."""
    if tuple(piece[0]) != tuple(piece[-1]):
        return idx if tuple(piece[0]) == tuple(arc[0]) else ~idx

    def orientation(c):  # sign of the shoelace sum
        x, y = c[:, 0], c[:, 1]
        return np.sign(
            np.einsum("i,i->", x[:-1], y[1:]) - np.einsum("i,i->", x[1:], y[:-1])
        )

    return idx if orientation(piece) == orientation(arc) else ~idx


def _new_junctions(lines, arcs):
    """Ends of the paths that the new `lines` share with existing arcs and with each
    other (as in Join). Also returns the arcs near the new lines."""
    pairs, near = [], []
    if arcs:
        ids = list(arcs)
        lengths = np.fromiter((len(arcs[i]) for i in ids), dtype=np.intp)
        xy = np.concatenate([arcs[i] for i in ids])
        starts = np.cumsum(lengths) - lengths
        lo, hi = np.minimum.reduceat(xy, starts), np.maximum.reduceat(xy, starts)
        li, ai = STRtree(shapely.box(lo[:, 0], lo[:, 1], hi[:, 0], hi[:, 1])).query(
            lines
        )
        near = sorted({ids[a] for a in ai.tolist()})
        shapes = {i: geometry.LineString(arcs[i]) for i in near}
        pairs += [(lines[n], shapes[ids[a]]) for n, a in zip(li.tolist(), ai.tolist())]
    li, lj = STRtree(lines).query(lines)
    pairs += [(lines[a], lines[b]) for a, b in zip(li.tolist(), lj.tolist()) if a < b]
    return {tuple(map(int, p)) for p in shared_path_ends(pairs)}, near


def _leaves(objects):
    """The geometries of extracted objects, with geometry collections flattened."""
    for o in objects:
        if o["type"] == "GeometryCollection":
            yield from _leaves(o["geometries"])
        else:
            yield o


def _resolve_arcs(obj, bookkeeping, refs):
    """Nested arc references of an extracted object, as the Hashmap builds them."""
    lines = [bookkeeping[b] for b in obj["arcs"]]
    t = obj["type"]
    if t == "LineString":
        return refs[lines[0][0]]
    if t == "MultiLineString":
        return [refs[line[0]] for line in lines]
    if t == "Polygon":
        return [refs[ring] for ring in lines[0]]
    return [[refs[ring] for ring in polygon] for polygon in lines]


def add_features(output, arcs, extracted, object_name):
    """Add the features of an `Extract` result, in place."""
    objects = extracted["objects"]
    transform = output["transform"]
    sequences = _all_sequences(output)

    # the bbox of a full build is the extent of the input
    new = compare_bounds(
        bounds(extracted["linestrings"]), bounds(extracted["coordinates"])
    )
    output["bbox"] = tuple(
        float(v) for v in compare_bounds(output.get("bbox") or [], new)
    )

    # new lines on the grid of the topology; rings are the lines of (multi)polygons
    is_ring = np.zeros(len(extracted["linestrings"]), dtype=bool)
    for o in _leaves(objects.values()):
        if o["type"] in ("Polygon", "MultiPolygon"):
            for b in o["arcs"]:
                is_ring[extracted["bookkeeping_geoms"][b]] = True
    lines, _ = quantize(list(extracted["linestrings"]), None, transform=transform)
    lines = np.asarray(lines, dtype=object)

    # cut existing arcs at the new junctions
    new_junctions, near = _new_junctions(lines, arcs) if len(lines) else (set(), [])
    next_idx = max(arcs, default=-1) + 1
    pieces = {}
    if new_junctions:
        tree = STRtree([geometry.Point(p) for p in new_junctions])
        ring_arcs = {_arc(r) for seq, ring in sequences if ring for r in seq}
        for i in near:
            closed = i in ring_arcs and tuple(arcs[i][0]) == tuple(arcs[i][-1])
            parts = cut_line(geometry.LineString(arcs[i]), tree, closed)
            parts = [p.astype(np.int64) for p in parts]
            if len(parts) > 1:
                del arcs[i]
                pieces[i] = list(range(next_idx, next_idx + len(parts)))
                next_idx += len(parts)
            arcs.update(zip(pieces.get(i, [i]), parts))
    for seq, _ in sequences:
        if any(_arc(r) in pieces for r in seq):
            seq[:] = [
                q
                for r in seq
                for q in (
                    pieces[r] if r in pieces
                    else [~p for p in reversed(pieces[~r])] if r < 0 and ~r in pieces
                    else [r]
                )
            ]  # fmt: skip

    # cut the new lines at all junctions; deduplicate the parts against the arcs near
    # them and against each other, as Cut does
    junctions = _junctions(arcs, sequences) | new_junctions
    tree = STRtree([geometry.Point(p) for p in junctions]) if junctions else None
    parts = [
        [p.astype(np.int64) for p in cut_line(line, tree, ring)]
        for line, ring in zip(lines, is_ring)
    ]
    existing = [j for i in near for j in pieces.get(i, [i])]
    new_parts = [p for line in parts for p in line]
    candidates = [arcs[j] for j in existing] + new_parts
    index, first = {}, {}  # candidate -> arc, hash -> first candidate
    for k, h in enumerate(hash_paths(candidates).tolist()):
        if h in first:
            index[k] = index[first[h]]
        elif k < len(existing):
            index[k] = existing[k]
        else:
            arcs[next_idx], index[k] = candidates[k], next_idx
            next_idx += 1
        first.setdefault(h, k)
    ks = iter(range(len(existing), len(candidates)))
    refs = [
        [_ref(p, arcs[index[k]], index[k]) for p, k in zip(line, ks)] for line in parts
    ]

    # new geometries; points go into the shared coordinate list
    points, _ = quantize(list(extracted["coordinates"]), None, transform=transform)
    offset = len(output["coordinates"])
    output["coordinates"].extend(points)
    point_index = [[offset + i for i in b] for b in extracted["bookkeeping_coords"]]

    def build(o):
        t = o["type"]
        if t == "GeometryCollection":
            return {"type": t, "geometries": [build(g) for g in o["geometries"]]}
        if t in ("Point", "MultiPoint"):
            nested = [[point_index[b]] for b in o["coordinates"]]
            coords = nested if t == "MultiPoint" else nested[0]
            return {"type": t, "coordinates": coords, "reset_coords": True}
        return {
            "type": t,
            "arcs": _resolve_arcs(o, extracted["bookkeeping_geoms"], refs),
        }

    geoms = output["objects"][object_name]["geometries"]
    for fid, o in objects.items():
        geoms.append({"properties": o.get("properties", {}), **build(o), "id": fid})
