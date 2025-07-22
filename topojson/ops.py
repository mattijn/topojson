import copy
import itertools
import logging
import pprint

import numpy as np
from shapely import geometry
from shapely import wkt
from shapely.ops import linemerge
from shapely.strtree import STRtree

try:
    from shapely.ops import orient
except ImportError:
    from shapely.geometry.base import BaseMultipartGeometry
    from shapely.geometry.polygon import orient as orient_
    from shapely.geometry import Polygon

    def orient(geom, sign=1.0):
        if isinstance(geom, BaseMultipartGeometry):
            return geom.__class__(
                list(map(lambda geom: orient(geom, sign), geom.geoms))
            )
        if isinstance(geom, (Polygon,)):
            return orient_(geom, sign)
        return geom


import contextlib
import shapely
import warnings

from packaging.version import Version
from importlib.metadata import version as importlib_version

shapely_version = importlib_version("shapely")

SHAPELY_GE_20 = Version(shapely_version) >= Version("2.0")

try:
    from shapely.errors import ShapelyDeprecationWarning as shapely_warning
except ImportError:
    shapely_warning = None
if shapely_warning is not None and not SHAPELY_GE_20:

    @contextlib.contextmanager
    def ignore_shapely2_warnings():
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=shapely_warning)
            yield

else:

    @contextlib.contextmanager
    def ignore_shapely2_warnings():
        yield


def asvoid(arr):
    """
    Utility function to create a 1-dimensional numpy void object (bytes)
    of a 2-dimensional array. This is useful for the function numpy.in1d(),
    since it only accepts 1-dimensional objects.

    Parameters
    ----------
    arr : numpy.array
        2-dimensional numpy array

    Returns
    -------
    numpy.void
        1-dimensional numpy void object
    """

    arr = np.ascontiguousarray(arr)
    if np.issubdtype(arr.dtype, np.floating):
        """Care needs to be taken here since
        np.array([-0.]).view(np.void) != np.array([0.]).view(np.void)
        Adding 0. converts -0. to 0.
        """
        arr += 0.0
    return arr.view(np.dtype((np.void, arr.dtype.itemsize * arr.shape[-1])))


def strtree_query_geoms(tree, arc):
    # get junctions that contain within bbox line
    if hasattr(tree, "geometries"):
        # shapely version >= 1.8.3
        tree_index = tree.query(arc)
        tree_geom = tree.geometries.take(tree_index)
    elif hasattr(tree, "query_geoms"):
        # 1.8.0 <= shapely version < 1.8.3
        tree_geom = tree.query_geoms(arc)
    else:
        # shapely version < 1.8.0
        tree_geom = tree.query(arc)
    return tree_geom  # pts_within_bbox


def strtree_query_index(tree, arc, geoms):
    if hasattr(tree, "geometries"):
        # shapely version >= 1.8.3
        tree_index = tree.query(arc)
    elif hasattr(tree, "query_items"):
        # 1.8.0 <= shapely version < 1.8.3
        tree_index = tree.query_items(arc)
    else:
        # shapely version < 1.8.0
        tree_geom = tree.query(arc)
        if isinstance(tree_geom, shapely.geometry.base.BaseGeometry):
            tree_geom = [tree_geom]
        tree_index = [geoms.index(tree_g) for tree_g in tree_geom]
        return tree_index
        # raise AttributeError("This version is not supported within topojson")
    return tree_index


def explode(segments):
    if not isinstance(segments, list):
        segments = [segments]
    list_explode = [
        list(geom.geoms) if hasattr(geom, "geoms") else [geom] for geom in segments
    ]
    return list(itertools.chain.from_iterable(list_explode))


def linemerge_ext(geom: geometry.base.BaseGeometry) -> geometry.base.BaseGeometry:
    line = extract_lines(geom)
    if isinstance(line, geometry.MultiLineString):
        return linemerge(line)
    else:
        return line


def extract_lines(geom: geometry.base.BaseGeometry) -> geometry.base.BaseGeometry:
    if isinstance(geom, geometry.LineString):
        return geom
    elif isinstance(geom, geometry.MultiLineString):
        return geom
    elif isinstance(geom, geometry.GeometryCollection):
        geoms = [
            geom
            for geom in geom.geoms
            if (
                not geom.is_empty
                and (
                    isinstance(geom, geometry.LineString)
                    or isinstance(geom, geometry.MultiLineString)
                )
            )
        ]
        if len(geoms) == 0:
            return geometry.LineString()
        elif len(geoms) == 1:
            return geoms[0]
        else:
            return geometry.MultiLineString(geoms)
    return geometry.LineString()


def np_array_bbox_points_line(line, tree_splitter):
    """
    Get junctions within bbox of line and return both as numpy array

    Parameters
    ----------
    line : numpy.array
        numpy array with coordinates representing a line segment
    tree_splitter : STRtree
        a STRtree splitter object

    Returns
    -------
    numpy.array
        `ls_xy`, numpy array from coordinates, if any, representing a line segment
    numpy.array
        `pts_xy_bbox`, numpy array with coordinates that near or on the line
    """

    # get junctions that contain within bbox line
    pts_within_bbox = strtree_query_geoms(tree_splitter, line)

    if len(pts_within_bbox) == 0:
        # no point near bbox, nothing to insert, nothing to split
        return None, None
    # convert shapely linestring and multipoint to np.array if there are points on line
    ls_xy = np.array(line.coords)
    pts_xy_bbox = np.array([x for pt in pts_within_bbox for x in pt.coords])

    return ls_xy, pts_xy_bbox


def insert_coords_in_line(line, tree_splitter):
    """
    Insert coordinates that are on the line, but where no vertices exists

    Parameters
    ----------
    line : numpy.array
        numpy array with coordinates representing a line segment
    tree_splitter : STRtree
        a STRtree splitter object

    Returns
    -------
    (numpy.array)
        `new_ls_xy` is an array with inserted coordinates, if any, representing a line
        segment
    (numpy.array)
        `pts_xy_on_line` is an array with coordinates that are on the line
    """

    # get junctions that contain within bbox line
    pts_within_bbox = strtree_query_geoms(tree_splitter, line)

    # select junctions that are within tolerance of line
    tol_dist = 1e-8
    pts_on_line = list(
        itertools.compress(
            pts_within_bbox, [line.distance(pt) < tol_dist for pt in pts_within_bbox]
        )
    )

    if len(pts_on_line) == 0:
        # no point on line, nothing to insert, nothing to split
        return None, None
    # convert shapely linestring and multipoint to np.array if there are points on line
    ls_xy = np.array(line.coords)
    pts_xy_on_line = np.array([x for pt in pts_on_line for x in pt.coords])

    # select junctions having non existing vertices in linestring
    tol_float_prc = 1e8
    pts_xy_nonexst = pts_xy_on_line[
        ~np.isin(
            asvoid(np.around(pts_xy_on_line * tol_float_prc).astype(np.int64))[:, 0],
            asvoid(np.around(ls_xy * tol_float_prc).astype(np.int64))[:, 0],
        )
    ]
    if pts_xy_nonexst.size == 0:
        return ls_xy, pts_xy_on_line
    # compute the distance from the beginning of the linestring for each junction on line
    splitter_dist = np.array(
        [line.project(pt) for pt in geometry.MultiPoint(pts_xy_nonexst).geoms]
    )
    splitter_dist = splitter_dist[splitter_dist > 0]

    # sort distance of non-existing junctions and apply sorting to the splitter distance
    # and corresponding junction coordinates to be inserted.
    sort_idx = splitter_dist.argsort()
    splitter_dist = splitter_dist[sort_idx]
    pts_xy_nonexst = pts_xy_nonexst[sort_idx]

    # get euclidean distance of all coords of line
    ls_xy_roll = np.roll(ls_xy, 1, axis=0)
    roll_min_ls = ls_xy_roll - ls_xy
    eucl_dist = np.sqrt(np.einsum("ij,ij->i", roll_min_ls, roll_min_ls))

    # the first distance is computed from the first point to the last point, set to 0
    eucl_dist[0] = 0
    ls_cumsum = eucl_dist.cumsum()

    # include junctions in linestring
    insert_idx = np.searchsorted(ls_cumsum, splitter_dist)
    new_ls_xy = np.insert(ls_xy, insert_idx, pts_xy_nonexst, axis=0)

    return new_ls_xy, pts_xy_on_line


def fast_split(line, splitter, is_ring):
    """
    Split a LineString (numpy.array) with a Point or MultiPoint.
    This function is a replacement for the shapely.ops.split function, but faster.

    Parameters
    ----------
    line : numpy.array
        numpy array with coordinates that you like to be split
    splitter : numpy.array
        numpy array with coordinates on which the line should be tried splitting
    is_ring : bool
        True if the line represents a ring. In this case, for the first point found, the
        linestring will be rotated rather than split. For consecutive points it will be
        split.

    Returns
    -------
    list of numpy.array
        If more than 1 item, the line was split. Each item in the list is an
        array of coordinates.
    """

    # previously did convert geometries of coordinates from LineString and (Multi)Point
    # to numpy arrays. This function now expect this as input to save time.
    # line = np.array(line.coords)
    # splitter = np.array([x for pt in splitter for x in pt.coords])

    # locate index of splitter coordinates in linestring
    tol = 1e8
    splitter_indices = np.flatnonzero(
        np.isin(
            asvoid(np.around(line * tol).astype(np.int64))[:, 0],
            asvoid(np.around(splitter * tol).astype(np.int64))[:, 0],
        )
    )

    # For a ring, rotate rather than split for the first splitter_index
    # Remark: the start and end coordinate of a ring are the same, so keep it that way
    if is_ring and len(splitter_indices) > 0 and splitter_indices[0] != 0:
        first_index = splitter_indices[0]
        line = line[:-1]
        line = np.roll(line, -first_index, axis=0)
        line = np.append(line, [line[0]], axis=0)
        splitter_indices = splitter_indices[1:]
        splitter_indices = splitter_indices - first_index
    # compute the indices on which to split the line
    # cannot split on first or last index of linestring
    splitter_indices = splitter_indices[
        (splitter_indices < (line.shape[0] - 1)) & (splitter_indices > 0)
    ]

    # split the linestring where each sub-array includes the split-point
    # create a new array with the index elements repeated
    tmp_indices = np.zeros(line.shape[0], dtype=np.int64)
    tmp_indices[splitter_indices] = 1
    tmp_indices += 1
    ls_xy = np.repeat(line, tmp_indices, axis=0)

    # update indices to account for the changed array
    splitter_indices = splitter_indices + np.arange(1, len(splitter_indices) + 1)

    # split using the indices as usual
    slines = np.split(ls_xy, splitter_indices, axis=0)

    return slines


def signed_area(ring):
    """
    Compute the signed area of a ring (polygon)

    Note: implementation is numpy variant of shapely's version:
    https://github.com/Toblerity/Shapely/blob/master/shapely/algorithms/cga.py

    Parameters
    ----------
    ring : numpy.array
        coordinates representing an exterior or inner ring

    Returns
    -------
    float
        the signed area
    """
    xs, ys = ring.T
    signed_area = (xs * (np.roll(ys, -1) - np.roll(ys, +1))).sum() / 2
    return signed_area


def is_ccw(ring):
    """
    Provide information if a given ring is clockwise or counterclockwise.

    Parameters
    ----------
    ring : numpy.array
        coordinates representing an exterior or inner ring

    Returns
    -------
    boolean
        True if ring is counterclockwise and False if ring is clockwise
    """
    return signed_area(ring) >= 0.0


def properties_foreign(objects):
    """
    Try to parse the object properties as foreign members. Reserved keys are:
    [`type`, `bbox`, `coordinates`, `geometries`, `geometry`, `properties`, `features`]

    If these keys are detected they will not be set as a foreign member and will remain
    nested within properties.

    Only if the

    Parameters
    ----------
    objects : [type]
        [description]
    """
    reserved_keys = [
        "type",
        "bbox",
        "coordinates",
        "geometries",
        "geometry",
        "properties",
        "features",
        "arcs",
    ]
    reserved_keys_used = bool(
        set(objects[0]["properties"].keys()).intersection(reserved_keys)
    )

    for obj in objects:
        reserved_keys = False
        for k, v in list(obj["properties"].items()):
            if not reserved_keys_used or k in reserved_keys:
                obj[k] = v
                obj["properties"].pop(k, None)
        if not reserved_keys_used:
            obj.pop("properties", None)
    return objects


def bounds(arr):
    """
    Returns a (minx, miny, maxx, maxy) tuple (float values) that bounds the object.

    Parameters
    ----------
    arr : np.array
        array to get bounds from

    Returns
    -------
    tuple
        (minx, miny, maxx, maxy)
    """
    if len(arr):
        if hasattr(arr[0], "coords"):
            arr = np.vstack([a.coords for a in arr]).T
        else:
            arr = np.vstack(arr).T
        bounds = (
            np.nanmin(arr[0]),
            np.nanmin(arr[1]),
            np.nanmax(arr[0]),
            np.nanmax(arr[1]),
        )
    else:
        bounds = []
    return bounds


def compare_bounds(b0, b1):
    """
    Function that compares two bounds with each other. Returns the max bound.

    Parameters
    ----------
    b0 : tuple
        tuple of xmin, ymin, xmax, ymax
    b1 : tuple
        tuple of xmin, ymin, xmax, ymax

    Returns
    -------
    tuple
        min of mins and max of maxs
    """

    if len(b0) and len(b1):
        bounds = (
            min(b0[0], b1[0]),
            min(b0[1], b1[1]),
            max(b0[2], b1[2]),
            max(b0[3], b1[3]),
        )
    elif len(b0) and not len(b1):
        bounds = b0
    elif not len(b0) and len(b1):
        bounds = b1
    else:
        bounds = []
    return bounds


def np_array_from_lists(nested_lists):
    """
    Function to create numpy array from nested lists. The shape of the numpy array
    are the number of nested lists (rows) x the length of the longest nested list
    (columns). Rows that contain less values are filled with np.nan values.

    Parameters
    ----------
    nested_lists : list of lists
        list containing nested lists of different sizes.

    Returns
    -------
    numpy.ndarray
        array created from nested lists, np.nan is used to fill the array
    """

    np_array = np.array(list(itertools.zip_longest(*nested_lists, fillvalue=np.nan))).T
    return np_array


def lists_from_np_array(np_array):
    """
    Function to convert numpy array to list, where elements set as np.nan
    are filtered
    """

    nested_lists = [obj[~np.isnan(obj)].astype(np.int64).tolist() for obj in np_array]
    return nested_lists


def np_array_from_arcs(arcs):
    max_len_arc = len(max(arcs, key=len))
    no_arcs = len(arcs)
    np_array = np.empty((no_arcs, max_len_arc, 2))
    np_array.fill(np.nan)
    for idx in range(no_arcs):
        np_array[idx, 0 : len(arcs[idx])] = arcs[idx]
    return np_array


def dequantize(np_arcs, scale, translate):
    dequantized_arcs = np_arcs.cumsum(axis=1) * scale + translate
    return dequantized_arcs


def get_matches(geoms, tree_idx):
    """
    Function to return the indices of the rtree that intersects with the input geometries

    Parameters
    ----------
    geoms : list
        list of geometries to compare against the STRtree
    tree_idx : STRtree
        a STRtree indexing object

    Returns
    -------
    list
        list of tuples, where the key of each tuple is the linestring index and the
        value of each key is a list of junctions intersecting bounds of linestring.
    """

    # find near linestrings by querying tree and use query items to collect indices.
    matches = []
    for idx_ls, obj in enumerate(geoms):
        intersect_ls = strtree_query_index(tree_idx, obj, geoms)
        if len(intersect_ls):
            matches.extend([[[idx_ls], intersect_ls]])
    return matches


def select_unique(data):
    """
    Function to return unique pairs within a numpy array.
    Example: input as [[1,2], [2,1]] will return as [[1,2]]

    Parameters
    ----------
    data : numpy.array
        2 dimensional array, where each row is a couple

    Returns
    -------
    numpy.array
        2 dimensional array, where each row is unique.
    """

    sorted_data = data[np.lexsort(data.T), :]
    row_mask = np.append([True], np.any(np.diff(sorted_data, axis=0), 1))

    return sorted_data[row_mask]


def select_unique_combs(linestrings):
    """
    Given a set of input linestrings will create unique couple combinations.
    Each combination created contains a couple of two linestrings where the envelope
    overlaps each other.
    Linestrings with non-overlapping envelopes are not returned as combination.

    Parameters
    ----------
    linestrings : list of LineString
        list where each item is a shapely LineString

    Returns
    -------
    numpy.array
        2 dimensional array, with on each row the index combination
        of a unique couple LineString with overlapping envelope
    """

    # create spatial index
    with ignore_shapely2_warnings():
        tree_idx = STRtree(linestrings)
    # get index of linestrings intersecting each linestring
    idx_match = get_matches(linestrings, tree_idx)

    # make combinations of unique possibilities
    combs = []
    for idx_comb in idx_match:
        combs.extend(list(itertools.product(*idx_comb)))
    combs = np.array(combs)
    combs.sort(axis=1)
    combs = select_unique(combs)

    uniq_line_combs = combs[(np.diff(combs, axis=1) != 0).flatten()]

    return uniq_line_combs, tree_idx


def quantize(linestrings, bbox, quant_factor=1e5):
    """
    Function that applies quantization. Quantization removes information by reducing
    the precision of each coordinate, effectively snapping each point to a regular grid.

    Parameters
    ----------
    linestrings : list of shapely.geometry.LineStrings
        LineStrings that will be quantized
    quant_factor : int
        Quantization factor. Normally this varies between 1e4, 1e5, 1e6. Where a
        higher number means a bigger grid where the coordinates can snap to.

    Returns
    -------
    dict
        `transform`, scale (`kx`, `ky`) and translation (`x0`, `y0`) values
    array
        `bbox`, bounding box of all linestrings
    """

    x0, y0, x1, y1 = bbox

    try:
        kx = 1 if (x1 - x0) == 0 else (x1 - x0) / (quant_factor - 1)
        ky = 1 if (y1 - y0) == 0 else (y1 - y0) / (quant_factor - 1)
    except ZeroDivisionError:
        kx, ky = 1, 1
    for idx, ls in enumerate(linestrings):
        if hasattr(ls, "coords"):
            ls_xy = np.array(ls.coords).T
        else:
            ls_xy = np.asarray(ls).T
        ls_xy = (
            np.array([(ls_xy[0] - x0) / kx, (ls_xy[1] - y0) / ky])
            .round()
            .astype(np.int64)
            .T
        )
        # get boolean slice where consecutive repeating coordinates are filtered
        bool_slice = (
            np.insert(np.absolute(np.diff(ls_xy, 1, axis=0)).sum(axis=1), 0, 1) != 0
        )

        # only remove repeating coordinates when possible
        # linestring should not become a single point
        if not bool_slice.sum() == 1 or len(ls_xy) == bool_slice.sum():
            if hasattr(ls, "coords"):
                linestrings[idx] = geometry.LineString(ls_xy[bool_slice])
            else:
                linestrings[idx] = ls_xy[bool_slice].tolist()
        else:
            if hasattr(ls, "coords"):
                linestrings[idx] = geometry.LineString(ls_xy)
            else:
                linestrings[idx] = ls_xy.tolist()
    transform_ = {"scale": [kx, ky], "translate": [x0, y0]}

    return linestrings, transform_


def simplify(
    linestrings,
    epsilon,
    algorithm="dp",
    package="simplification",
    input_as="linestring",
    prevent_oversimplify=True,
):
    """
    Function that simplifies linestrings. The goal of line simplification is to reduce
    the number of points by deleting some trivial points, but without destroying the
    essential shape of the lines in the process.

    One can choose between the Douglas-Peucker ["dp"] algorithm (which simplifies
    a line based upon vertical interval) and Visvalingam–Whyatt ["vw"] (which
    progressively removes points with the least-perceptible change).


    Docs
    * https://observablehq.com/@lemonnish/minify-topojson-in-the-browser
    * https://github.com/topojson/topojson-simplify#planarTriangleArea
    * https://www.jasondavies.com/simplify/
    * https://bost.ocks.org/mike/simplify/
    * https://pdfs.semanticscholar.org/9877/cdf50a15367bcb86649b67df8724425c5451.pdf

    Parameters
    ----------
    linestrings : list of shapely.geometry.LineStrings
        LineStrings that will be simplified
    epsilon : int
        Simplification factor. Normally this varies 1.0, 0.1 or 0.001 for "rdp" and
        30-100 for "vw".
    algorithm : str, optional
        Choose between `dp` for Douglas-Peucker and `vw` for Visvalingam–Whyatt.
        Defaults to `dp`, as its evaluation maintains to be good (Shi, W. &
        Cheung, C., 2006).
    package : str, optional
        Choose between `simplification` or `shapely`. Both packages contains
        simplification algorithms (`shapely` only `dp`, and `simplification` both `dp`
        and `vw`).
    input_as : str, optional
        Choose between `linestring` or `array`. This function is being called from
        different locations with different input types. Choose `linestring` if the input
        type are shapely.geometry.LineString or `array` if the input are numpy.array
        coordinates

    Returns
    -------
    list of shapely.geometry.LineStrings or ndarrays, depending on the type of the input
        LineStrings that are simplified
    """
    list_arcs = None

    if package == "shapely":
        if algorithm == "vw":
            msg = (
                "You need to set `simplify_with='simplification'` to use the ",
                "Visvalingam–Whyatt (`vw`) algorithm. This package is optional and ",
                "if not installed, install with `pip install simplification`. ",
                "Continue with Douglas-Peucker (`dp`) algorithm instead.",
            )
            logging.warning("".join(msg))
        if input_as == "array":
            list_arcs = []
            for ls in linestrings:
                coords_to_simp = ls[~np.isnan(ls)[:, 0]]
                simple_ls = geometry.LineString(coords_to_simp)
                simple_ls = simple_ls.simplify(
                    epsilon, preserve_topology=prevent_oversimplify
                )
                list_arcs.append(np.array(simple_ls.coords).tolist())
        elif input_as == "linestring":
            for idx, ls in enumerate(linestrings):
                linestrings[idx] = ls.simplify(
                    epsilon, preserve_topology=prevent_oversimplify
                )
            list_arcs = linestrings
    elif package == "simplification":
        from simplification import cutil

        if algorithm == "vw" and prevent_oversimplify:
            alg = cutil.simplify_coords_vwp
        elif algorithm == "vw" and not prevent_oversimplify:
            alg = cutil.simplify_coords_vw
        elif algorithm == "dp" and prevent_oversimplify:
            msg = (
                "The Douglas–Peucker algorithm from the `simplification` package ",
                "has no options to prevent oversimplification. Use Visvalingam–",
                "Whyatt (`vw`) algorithm when using the simplification package if ",
                "oversimplification should be prevented or use the Douglas-Peucker ",
                "algorithm from `shapely` package to prevent oversimplification. ",
                "Continue without prevention of oversimplification.",
            )
            logging.warning("".join(msg))
            alg = cutil.simplify_coords
        else:
            alg = cutil.simplify_coords
        if input_as == "array":
            list_arcs = []
            for ls in linestrings:
                coords_to_simp = ls[~np.isnan(ls)[:, 0]]
                simple_ls = alg(coords_to_simp, epsilon)
                list_arcs.append(simple_ls.tolist())
        elif input_as == "linestring":
            for idx, ls in enumerate(linestrings):
                coords_to_simp = np.array(ls.coords)
                simple_ls = alg(coords_to_simp, epsilon)
                linestrings[idx] = geometry.LineString(simple_ls)
            list_arcs = linestrings
    else:
        raise NameError(
            "Could not recognize parameter for `simplify_with`. Choose between \
                'shapely' or 'simplification'. '{}' was given".format(
                package
            )
        )
    return list_arcs


def winding_order(geom, order="CW_CCW"):
    """
    Function that force a certain winding order on the resulting output geometries. One
    can choose between `CCW_CW` and `CW_CCW`.

    `CW_CCW` implies clockwise for exterior polygons and counterclockwise for interior
    polygons (aka the geographical right-hand-rule where the right hand is in the area
    of interest as you walk the line).

    `CCW_CW` implies counterclockwise for exterior polygons and clockwise for interior
    polygons (aka the mathematical right-hand-rule where the right hand curls around
    the polygon's exterior with your thumb pointing "up" (toward space), signing a
    positive area for the polygon in the signed area sense).

    TopoJSON, and so this package, defaults to `CW_CCW`, but depending on the
    application you might decide differently.

    * https://bl.ocks.org/mbostock/a7bdfeb041e850799a8d3dce4d8c50c8

    Only applies to Polygons and MultiPolygons.

    Parameters
    ----------
    geom : geometry or shapely.geometry.GeometryCollection
        Geometry objects where the winding order will be forced upon.
    order : str, optional
        Choose `CW_CCW` for clockwise for exterior- and counterclockwise for
        interior polygons or `CCW_CW` for counterclockwise for exterior- and clockwise
        for interior polygons, by default `CW_CCW`.

    Returns
    -------
    geometry or shapely.geometry.GeometryCollection
        Geometry objects where the chosen winding order is forced upon.
    """

    # CW_CWW will orient the outer polygon clockwise and the inner polygon counter-
    # clockwise to conform TopoJSON standard

    if order == "CW_CCW":
        geom = orient(geom, sign=-1.0)
    elif order == "CCW_CW":
        geom = orient(geom, sign=1.0)
    else:
        raise NameError("parameter {} was not recognized".format(order))
    return geom


def round_coordinates(linestrings, rounding_precision):
    """
    Round all coordinates to a specified precision, e.g. `rounding_precision=3` will round
    to 3 decimals on the resulting output geometries (after the topology is computed).

    Parameters
    ----------
    linestrings : list of shapely.geometry.LineStrings
        LineStrings of which the coordinates will be rounded
    rounding_precision : int
        Precision value. Up till how many decimals the coordinates should be rounded.

    Returns
    -------
    list of shapely.geometry.LineStrings
        LineStrings of which the coordinates are rounded
    """
    for idx, geom in enumerate(linestrings):
        linestrings[idx] = wkt.loads(
            wkt.dumps(geom, rounding_precision=rounding_precision)
        )
    return linestrings


def prettify(topojson_object):
    """
    prettify TopoJSON Format output for readability.

    Parameters
    ----------
    topojson_object : topojson.Topojson
        object to be pretty printed

    Returns
    -------
    topojson.Topojson
        pretty printed JSON variant of the topology object
    """
    return pprint.pprint(topojson_object)


def properties_level(topojson_object, position="nested"):
    """
    Define where the attributes of the geometry object should be placed. Choose between
    `nested` or `foreign`. Default is `nested` where the attribute information is placed
    within the "properties" dictionary, part of the geometry.
    `foreign`, tries to place the attributes on the same level as the geometry.

    Parameters
    ----------
    topojson_object : topojson.Topojson
        [description]
    position : str, optional
        [description], by default "nested"
    """

    import warnings

    warnings.warn(("\nNot yet implemented."), DeprecationWarning, stacklevel=2)


def delta_encoding(linestrings):
    """
    Function to apply delta-encoding to linestrings.

    Parameters
    ----------
    linestrings : list of shapely.geometry.LineStrings
        LineStrings that will be delta-encoded

    Returns
    -------
    list of shapely.geometry.LineStrings
        LineStrings that are delta-encoded
    """

    for idx, ls in enumerate(linestrings):
        if hasattr(ls, "coords"):
            ls = np.array(ls.coords).astype(np.int64)
        else:
            ls = np.array(ls).astype(np.int64)
        ls_p1 = copy.copy(ls[0])
        ls -= np.roll(ls, 1, axis=0)
        ls[0] = ls_p1
        linestrings[idx] = ls.tolist()
    return linestrings


def cart(arr):
    """
    Function that returns all combinations as a 2D array
    [3, 152,  62, 52] is returned as [[152,  62], [152,  52], [152,   3]]
    """
    arr = -np.sort(-arr)
    arr = np.array(np.meshgrid(arr[0], arr[1:])).T.reshape(-1, 2)
    return arr


def find_duplicates(segments_list, type="array"):
    """
    Function for solely detecting and recording duplicate LineStrings. The function
    converts and sorts the coordinates of each linestring and gets the hash. Using the
    hashes it can quickly detect duplicates and return the indices.

    Parameters
    ----------
    segments_list : list of paths
        list of valid paths
    type : str
        set if paths is `array` or `linestring`

    """

    # get hash of sorted linestring coordinates
    hash_segments = []

    if type != "array":
        segments_list = [
            np.array(list(linestring.coords)) for linestring in segments_list
        ]
    for coordinates in segments_list:
        # If start and end points are the same, remove end point before sorting
        # Rmark: check if it was originally a ring is not relevant, because lines with
        # equal start and end point are no probem to be deduplicated with rings.
        if np.array_equal(coordinates[0], coordinates[-1]):
            coordinates = coordinates[0:-1]
            coordinates = np.sort(coordinates, axis=0)
            coordinates = np.append(coordinates[0:2], coordinates)
        else:
            coordinates = np.sort(coordinates, axis=0)
        hash_segments.append(hash(bytes(coordinates)))
    hash_segments = np.array(hash_segments, dtype=np.int64)

    # get split locations of dups
    idx_sort = np.argsort(hash_segments)
    sorted_hashes = hash_segments[idx_sort]
    _, idx_start, count = np.unique(
        sorted_hashes, return_counts=True, return_index=True
    )
    if count.max() > 1:
        # split on indices that occurs > 1
        idx_dups = np.split(idx_sort, idx_start[1:])
        list_dups = []
        for dup in idx_dups:
            if dup.size > 2:
                list_dups.append(cart(dup))
            elif dup.size > 1:
                list_dups.append(dup)
        idx_dups = np.vstack(list_dups)

        # apply sorting on duplicate-pairs
        # pylint: disable=invalid-unary-operand-type
        idx_dups = -np.sort(-idx_dups, axis=1)
        idx_dups = idx_dups[np.argsort(idx_dups[:, 0])]
        return idx_dups
    else:
        return []


def map_values(arr, search_vals, replace_vals):
    """
    This function replace values element-wise in a numpy array.
    Its quick and avoids a np.where-loop (which is slow).
    The result is a new array, not inplace.

    Parameters
    ----------
    arr : np.array
        input array
    search_vals : list or 1D np.array
        array with 'bad' values
    replace_vals : list or 1D np.array
        array with 'good' values

    Returns
    -------
    np.array
        new array with replaced values
    """
    N = max(arr.max(), max(search_vals)) + 1
    maparr = np.empty(N, dtype=np.int64)

    maparr[arr] = arr
    maparr[search_vals] = replace_vals

    arr_upd = maparr[arr]
    return arr_upd


def remove_collinear_points(line: np.ndarray) -> np.ndarray:
    # If only 2 points, no use checking
    if len(line) <= 2:
        return line
    # Prepare "points"
    p1_x = line[:-2, 0]
    p1_y = line[:-2, 1]
    p2_x = line[1:-1, 0]
    p2_y = line[1:-1, 1]
    p3_x = line[2:, 0]
    p3_y = line[2:, 1]

    # Calculate
    collinear_mask = (p2_x - p1_x) * (p3_y - p1_y) == (p3_x - p1_x) * (p2_y - p1_y)  # type: ignore
    collinear_mask = np.concatenate([[False], collinear_mask, [False]])
    return line[~np.array(collinear_mask)]
