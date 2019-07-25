import itertools
import numpy as np
from shapely import geometry
from shapely import wkt
from shapely.ops import transform
from shapely.strtree import STRtree
import pprint
import copy


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
        """ Care needs to be taken here since
        np.array([-0.]).view(np.void) != np.array([0.]).view(np.void)
        Adding 0. converts -0. to 0.
        """
        arr += 0.
    return arr.view(np.dtype((np.void, arr.dtype.itemsize * arr.shape[-1])))


def fast_split(line, splitter):
    """
    Split a LineString (numpy.array) with a Point or MultiPoint. 
    This function is a replacement for the shapely.ops.split function, but faster.
    
    Parameters
    ----------
    line : numpy.array 
        numpy array with coordinates that you like to be split
    splitter : numpy.array
        numpy array with coordates on wich the line should be tried splitting
    
    Returns
    -------
    list of numpy.array
        If more than 1 item, the line was split. Each item in the list is a 
        array of coordinates. 

    TODO: Check how this: https://stackoverflow.com/a/328110/2459096 can help
    """

    # previously did convert geometries of coordinates from LineString and (Multi)Point
    # to numpy arrays. This function now expect this as input to save time.
    # line = np.array(line.xy).T
    # splitter = np.squeeze(np.array([pt.xy for pt in splitter]), axis=(2,))

    # locate index of splitter coordinates in linestring
    # TODO: maybe a r-tree indexer on the `splitter` can improve the timings
    tol = 1e8
    splitter_indices = np.flatnonzero(
        np.in1d(
            asvoid(np.around(line * tol).astype(int)),
            asvoid(np.around(splitter * tol).astype(int)),
        )
    )

    # compute the indices on wich to split the line
    # cannot split on first or last index of linestring
    splitter_indices = splitter_indices[
        (splitter_indices < (line.shape[0] - 1)) & (splitter_indices > 0)
    ]

    # split the linestring where each sub-array includes the split-point
    # create a new array with the index elements repeated
    tmp_indices = np.zeros(line.shape[0], dtype=int)
    tmp_indices[splitter_indices] = 1
    tmp_indices += 1
    ls_xy = np.repeat(line, tmp_indices, axis=0)

    # update indices to account for the changed array
    splitter_indices = splitter_indices + np.arange(1, len(splitter_indices) + 1)

    # split using the indices as usual
    slines = np.split(ls_xy, splitter_indices, axis=0)

    return slines


def get_matches(geoms, tree_idx):
    """
    Function to return the indici of the rtree that intersects with the input geometries
    
    Parameters
    ----------
    geoms : list
        list of geometries to compare against the STRtree
    tree_idx: STRtree
        a STRtree indexing object
        
    Returns
    -------
    list
        list of tuples, where the key of each tuple is the linestring index and the 
        value of each key is a list of junctions intersecting bounds of linestring.
    """

    # find near linestrings by querying tree
    matches = []
    for idx_ls, obj in enumerate(geoms):
        intersect_ls = tree_idx.query(obj)
        if len(intersect_ls):
            matches.extend([[[idx_ls], [ls.i for ls in intersect_ls]]])

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
    Given a set of inpit linestrings will create unique couple combinations.
    Each combination created contains a couple of two linestrings where the enveloppe
    overlaps each other.
    Linestrings with non-overlapping enveloppes are not returned as combination.
    
    Parameters
    ----------
    linestrings : list of LineString
        list where each item is a shapely LineString
    
    Returns
    -------
    numpy.array
        2 dimensional array, with on each row the index combination
        of a unique couple LineString with overlapping enveloppe
    """

    # create spatial index and add idx as attribute
    for i, ls in enumerate(linestrings):
        ls.i = i
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

    return uniq_line_combs


def prequantize(linestrings, quant_factor=1e6):
    """
    Function that applies quantization prior computing topology. Quantization removes 
    information by reducing the precision of each coordinate, effectively snapping each 
    point to a regular grid.

    Parameters
    ----------
    linestrings: list of shapely.geometry.LineStrings
        LineStrings that will be quantized
    quant_factor : int
        Quantization factor. Normally this varies between 1e4, 1e5, 1e6. Where a 
        higher number means a bigger grid where the coordinates can snap to. 

    Returns
    -------
    kx, ky, x0, y0 : int
        Scale (kx, ky) and translation (x0, y0) values
    linestrings : list of shapely.geometry.LineStrings    
        LineStrings that are quantized 
    """

    x0, y0, x1, y1 = geometry.MultiLineString(linestrings).bounds
    kx = 1 / ((quant_factor - 1) / (x1 - x0))
    ky = 1 / ((quant_factor - 1) / (y1 - y0))

    for ls in linestrings:
        ls_xy = np.array(ls.xy)
        ls_xy = (
            np.array([(ls_xy[0] - x0) / kx, (ls_xy[1] - y0) / ky]).T.round().astype(int)
        )
        ls.coords = ls_xy[
            np.insert(np.absolute(np.diff(ls_xy, 1, axis=0)).sum(axis=1), 0, 1) != 0
        ]

    return {"scale": [kx, ky], "translate": [x0, y0]}


def simplify(linestrings, epsilon, algorithm="dp", package="simplification"):
    """
    Function that simplifies linestrings. The goal of line simplification is to reduce 
    the number of points by deleting some trivial points, but without destroying the 
    essential shape of the lines in the process.
    
    One can choose between the Douglas-Peucker ["dp"] algorithm (which simplifies 
    a line based upon vertical interval) and Visvalingam–Whyatt ["vw"] (which 
    progressively removes points with the least-perceptible change).
    
    https://pdfs.semanticscholar.org/9877/cdf50a15367bcb86649b67df8724425c5451.pdf

    Parameters
    ----------
    linestrings: list of shapely.geometry.LineStrings
        LineStrings that will be simplified
    epsilon : int
        Simplification factor. Normally this varies 1.0, 0.1 or 0.001 for "rdp" and 
        30-100 for "vw". 
    algorithm : str, optional
        Choose between `dp` for Douglas-Peucker and `vw` for Visvalingam–Whyatt.
        Defaults to `rdp`, as its evaluation maintains to be good (Song & Miao, 2016).
    package : str, optional
        Choose between `simplification` or `shapely`. Both pachakges contains 
        simplification algorithms (`shapely` only `rdp`, and `simplification` both `rdp`
        and `vw` but quicker).

    Returns
    -------
    simp_linestrings: list of shapely.geometry.LineStrings
        LineStrings that are simplified

    Docs
    * https://observablehq.com/@lemonnish/minify-topojson-in-the-browser
    * https://github.com/topojson/topojson-simplify#planarTriangleArea
    * https://www.jasondavies.com/simplify/
    * https://bost.ocks.org/mike/simplify/
    """
    return


def winding_order(geom, order="CW_CCW"):
    """
    Function that force a certain winding order on the resulting output geometries. One 
    can choose between "CCW_CW" and "CW_CCW".
    
    "CW_CCW" implies clockwise for exterior polygons and counterclockwise for interior 
    polygons (aka the geographical right-hand-rule where the right hand is in the area 
    of interest as you walk the line).

    "CCW_CW" implies counterclockwise for exterior polygons and clockwise for interior 
    polygons (aka the mathematical right-hand-rule where the right hand curls around 
    the polygon's exterior with your thumb pointing "up" (toward space), signing a 
    positive area for the polygon in the signed area sense).

    TopoJSON, and so this package, defaults to "CW_CCW"*, but depending on the 
    application you might decide differently.
    
    * https://bl.ocks.org/mbostock/a7bdfeb041e850799a8d3dce4d8c50c8

    Only applies to Polygons and MultiPolygons.

    Parameters
    ----------
    geom : geometry or shapely.geometry.GeometryCollection
        Geometry objects where the winding order will be forced upon.
    order : str, optional
        Choose "CW_CCW" for clockwise for exterior- and counterclockwise for 
        interior polygons or "CCW_CW" for counterclockwise for exterior- and clockwise 
        for interior polygons, by default "CW_CCW".

    Returns
    -------
    geom : geometry or shapely.geometry.GeometryCollection
        Geometry objects where the chosen winding order is forced upon.
    """

    # CW_CWW will orient the outer polygon clockwise and the inner polygon to be
    # counterclockwise to conform TopoJSON standard
    if order == "CW_CCW":
        geom = geometry.polygon.orient(geom, sign=-1.0)
    elif order == "CCW_CW":
        geom = geometry.polygon.orient(geom, sign=1.0)
    else:
        raise NameError("parameter {} was not recognized".format(order))

    return geom


def round_coordinates(linestrings, rounding_precision):
    """
    Round all coordinates to a specified precision, e.g. rounding_precision=3 will round
    to 3 decimals on the resulting output geometries (after the topology is computed).

    Parameters
    ----------
    linestrings: list of shapely.geometry.LineStrings
        LineStrings of which the coordinates will be rounded
    rounding_precision : int
        Precision value. Up till how many decimales the coordinates should be rounded.
    
    Returns
    -------
    linestrings: list of shapely.geometry.LineStrings
        LineStrings of which the coordinates will be rounded
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
        [description]

    Returns
    -------
    topojson_object : topojson.Topojson
        pretty printed JSON variant of the topoloy object
    """
    return pprint.pprint(topojson_object)


def properties_level(topojson_object, position="nested"):
    """
    Define where the attributes of the geometry object should be placed. Choose between
    "nested" or "foreign. Default is "nested" where the attribute information is placed
    within the "properties" ditctionary, part of the geometry.
    "foreign", tries to place the attributes on the same level as the geometry.
    
    Parameters
    ----------
    topojson_object : topojson.Topojson
        [description]
    position : str, optional
        [description], by default "nested"
    """

    import warnings

    warnings.warn(("\nNot yet implemened."), DeprecationWarning, stacklevel=2)


def delta_encoding(linestrings, prequantized=True):
    """
    Function to apply delta-encoding to linestrings. Delta-encoding is a technique ..

    Replace in Hashmapper class.
    
    Parameters
    ----------
    linestrings : list of shapely.geometry.LineStrings
        LineStrings that will be delta-encoded
    quantized : bool, optional
        set to True if the linestrings are prequantized , by default True

    Returns
    -------
    linestrings : list of shapely.geometry.LineStrings
        LineStrings that are delta-encoded 
    """

    for idx, ls in enumerate(linestrings):
        if prequantized:
            ls = ls.astype(int)
        else:
            ls = np.array(ls).astype(int)
        ls_p1 = copy.copy(ls[0])
        ls -= np.roll(ls, 1, axis=0)
        ls[0] = ls_p1
        linestrings[idx] = ls.tolist()

    return linestrings

