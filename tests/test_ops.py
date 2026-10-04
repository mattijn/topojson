import numpy as np
import pytest
from shapely import geometry

import topojson.ops
import topojson.utils
from topojson.core.extract import Extract


def test_ops_remove_colinear_points():

    test = np.array([[0, 0], [0, 1], [0, 2]])
    result = topojson.ops.remove_collinear_points(test)
    assert result.tolist() == [[0, 0], [0, 2]]

    test = np.array([[0, 0], [1, 1], [0, 2]])
    result = topojson.ops.remove_collinear_points(test)
    assert result.tolist() == test.tolist()


def test_ops_remove_spikes():
    # ring that turns back at (0, 0)
    ring = np.array([[3, 0], [0, 0], [2, 0], [2, 2], [3, 2], [3, 0]])
    result = topojson.ops.remove_spikes(ring)
    assert result.tolist() == [[3, 0], [2, 0], [2, 2], [3, 2], [3, 0]]

    # ring with the spike at the closing vertex
    ring = np.array([[0, 0], [2, 0], [2, 2], [1, 0], [0, 0]])
    result = topojson.ops.remove_spikes(ring)
    assert result.tolist() == [[2, 0], [2, 2], [1, 0], [2, 0]]

    # open line: end points are kept
    line = np.array([[0, 0], [5, 0], [3, 0], [3, 3]])
    result = topojson.ops.remove_spikes(line)
    assert result.tolist() == [[0, 0], [3, 0], [3, 3]]

    # a line that would collapse is returned unchanged
    line = np.array([[0, 0], [5, 0], [0, 0]])
    assert topojson.ops.remove_spikes(line).tolist() == line.tolist()


def pairwise_shared_path_ends(lines):
    pairs = [
        (a, b)
        for i, a in enumerate(lines)
        for b in lines[i + 1 :]
        if a.envelope.intersects(b.envelope)
    ]
    return topojson.ops.shared_path_ends(pairs)


@pytest.mark.parametrize(
    "lines",
    [
        # equal lines share no path, also with an extra vertex or reversed
        [[(0, 0), (10, 0)], [(0, 0), (5, 0), (10, 0)]],
        [[(0, 0), (10, 0)], [(10, 0), (0, 0)], [(5, 0), (10, 0), (10, 5)]],
        # vertices of one line inside a segment of the other
        [
            [(0, 0), (4, 0), (4, 4), (0, 4), (0, 0)],
            [(4, 1), (8, 1), (8, 3), (4, 3), (4, 1)],
        ],
        [[(0, 0), (6, 0)], [(3, 0), (9, 0)]],
        [[(0, 0), (6, 6)], [(2, 2), (4, 4), (4, 8)]],
        # collinear without overlap, crossing, and the end of a line on a path
        [[(0, 0), (2, 0)], [(3, 0), (5, 0)]],
        [[(0, 0), (4, 4)], [(0, 4), (4, 0)]],
        [[(0, 0), (10, 0)], [(2, 0), (6, 0), (6, 6)]],
        # a closed line continues into its start, also when it is not a ring
        [[(0, 0), (4, 0), (4, 4), (0, 0)], [(4, 0), (4, 4), (0, 0), (4, 0)]],
        [[(0, 0), (4, 0), (4, 4), (0, 0)], [(0, 0), (4, 0)]],
        # a line that passes a vertex twice, and a ring that lies on it
        [
            [(0, 0), (2, 0), (2, 2), (0, 2), (0, 0)],
            [(-2, -2), (2, -2), (2, 0), (0, 0), (0, 2), (2, 2), (2, 0), (4, 0)],
        ],
    ],
)
def test_ops_shared_path_ends_on_grid_cases(lines):
    lines = [geometry.LineString(line) for line in lines]
    expected = pairwise_shared_path_ends(lines)
    assert topojson.ops.shared_path_ends_on_grid(lines) == expected


@pytest.mark.parametrize("quant_factor", [50, 75, 100, 1e5])
def test_ops_shared_path_ends_on_grid_equals_pairwise(quant_factor):
    # coarse grids give rings that touch themselves and lie on each other
    data = topojson.utils.example_data_africa()
    extracted = Extract(data).output
    linestrings = extracted["linestrings"]
    bbox = topojson.ops.bounds(linestrings)
    lines, _ = topojson.ops.quantize(linestrings, bbox, quant_factor)
    expected = pairwise_shared_path_ends(lines)
    assert topojson.ops.shared_path_ends_on_grid(lines) == expected


@pytest.mark.parametrize("quant_factor", [50, 100, 1e5])
def test_ops_cut_lines_on_grid_equals_cut_line(quant_factor):
    data = topojson.utils.example_data_africa()
    extracted = Extract(data).output
    linestrings = extracted["linestrings"]
    bbox = topojson.ops.bounds(linestrings)
    lines, _ = topojson.ops.quantize(linestrings, bbox, quant_factor)
    ends = sorted(topojson.ops.shared_path_ends_on_grid(lines))
    junctions = [geometry.Point(p) for p in ends]
    # a line through a junction that is not one of its vertices
    (x, y) = ends[0]
    lines.append(geometry.LineString([(x - 1, y - 1), (x + 1, y + 1)]))
    is_ring = np.array([line.is_closed for line in lines])

    parts, n_parts = topojson.ops.cut_lines_on_grid(lines, junctions, is_ring)
    tree = topojson.ops.STRtree(junctions)
    expected = [
        topojson.ops.cut_line(line, tree, ring) for line, ring in zip(lines, is_ring)
    ]
    assert n_parts.tolist() == [len(p) for p in expected]
    assert [p.tolist() for p in parts] == [p.tolist() for e in expected for p in e]


def test_ops_hash_paths():
    line = np.array([[0, 0], [1, 0], [1, 1]])
    ring = np.array([[0, 0], [1, 0], [1, 1], [0, 0]])
    rotated = np.array([[1, 0], [1, 1], [0, 0], [1, 0]])
    h = topojson.ops.hash_paths([line, line[::-1], ring, ring[::-1], rotated, line[:2]])
    assert h[0] == h[1]
    assert h[2] == h[3] == h[4]
    assert len({h[0], h[2], h[5]}) == 3


# simplifying with epsilon keeps the vertices with a weight > epsilon (#223)
def test_ops_dp_weights_reproduce_shapely_simplify():
    import geopandas
    import shapely

    import topojson

    data = geopandas.read_file("tests/files_shapefile/static_natural_earth.gpkg")
    topo = topojson.Topology(data)
    arcs = topojson.ops.arc_coordinates(topo.output["arcs"], topo.output["transform"])
    count = np.array([len(a) for a in arcs])
    xy = np.concatenate(arcs)
    ends = np.cumsum(count) - 1
    weight = topojson.ops.dp_weights(xy, ends - count + 1, ends)
    lines = shapely.linestrings(xy, indices=np.repeat(np.arange(len(arcs)), count))

    inner = weight[np.isfinite(weight)]
    # also exactly on a weight, where equal values decide
    for epsilon in [*np.quantile(inner, [0.1, 0.5, 0.9]), *inner[::97]]:
        simple = shapely.simplify(lines, epsilon, preserve_topology=False)
        np.testing.assert_array_equal(
            shapely.get_coordinates(simple), xy[weight > epsilon]
        )


def test_ops_dp_weights_are_nested():
    xy = np.array([[0, 1], [2.6, 4.6], [5.3, 3.9], [7.1, 6], [9.6, 0], [12, 3.4]])
    weight = topojson.ops.dp_weights(xy, [0], [5])
    # (7.1, 6) splits first; (9.6, 0) is farther from its section, but is kept only
    # as long as (7.1, 6) is kept
    assert weight[3] == weight[4]
    assert np.isinf(weight[[0, 5]]).all()


def test_ops_simplify_keep():
    lines = [
        np.array([[0, 1], [2.6, 4.6], [5.3, 3.9], [7.1, 6], [9.6, 0], [12, 3.4]]),
        np.array([[0, 0], [5, 0]]),
    ]
    none, _ = topojson.ops.simplify_keep(lines, 0)
    assert none == [[[0, 1], [12, 3.4]], [[0, 0], [5, 0]]]
    every, _ = topojson.ops.simplify_keep(lines, 1)
    assert every == [line.tolist() for line in lines]
    half, epsilon = topojson.ops.simplify_keep(lines, 0.5)
    # 2 of the 4 inner vertices; (7.1, 6) and (9.6, 0) have the same weight
    assert half[0] == [[0, 1], [7.1, 6], [9.6, 0], [12, 3.4]]
    assert half == topojson.ops.simplify(
        lines, epsilon, input_as="array", prevent_oversimplify=False
    )


# Visvalingam-Whyatt: a search of the tolerance of the package simplification
@pytest.mark.parametrize("keep", [0, 0.02, 0.1, 0.5, 1])
def test_ops_simplify_keep_vw(keep):
    import geopandas

    import topojson

    data = geopandas.read_file("tests/files_shapefile/static_natural_earth.gpkg")
    topo = topojson.Topology(data)
    arcs = topojson.ops.arc_coordinates(topo.output["arcs"], topo.output["transform"])
    inner = sum(len(a) - 2 for a in arcs)
    simple, epsilon = topojson.ops.simplify_keep(arcs, keep, "vw")

    # the result of the tolerance, with the share of vertices asked for
    assert simple == topojson.ops.simplify(
        arcs,
        epsilon,
        algorithm="vw",
        package="simplification",
        input_as="array",
        prevent_oversimplify=False,
    )
    assert abs(sum(len(a) - 2 for a in simple) - keep * inner) <= 0.001 * inner
