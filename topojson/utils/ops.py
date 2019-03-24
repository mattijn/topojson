import itertools
import numpy as np
from shapely import geometry
from shapely.strtree import STRtree


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
    Split a LineString with a Point or MultiPoint. 
    This function is a replacement for the shapely.ops.split function, but faster.
    
    Parameters
    ----------
    line : LineString
        LineString that you like to be split
    splitter : Point or MultiPoint
        A single or multiple points on wich the line should be tried splitting
    
    Returns
    -------
    list of numpy.array
        If more than 1 item, the line was split. Each item in the list is a 
        array of coordinates. 
    """

    if isinstance(splitter, geometry.Point):
        splitter = geometry.MultiPoint([splitter])

    # convert geometries of coordinates to numpy arrays
    ls_xy = np.array(line.xy).T
    sp_xy = np.squeeze(np.array([pt.xy for pt in splitter]), axis=(2,))

    # locate index of splitter coordinates in linestring
    # use tolerance parameter to select very nearby junctions to linestring
    tol = 1e8
    splitter_indices = np.flatnonzero(
        np.in1d(
            asvoid(np.around(ls_xy * tol).astype(int)),
            asvoid(np.around(sp_xy * tol).astype(int)),
        )
    )

    # compute the indices on wich to split the line
    # cannot split on first or last index of linestring
    splitter_indices = splitter_indices[
        (splitter_indices < (ls_xy.shape[0] - 1)) & (splitter_indices > 0)
    ]

    # split the linestring where each sub-array includes the split-point
    # create a new array with the index elements repeated
    tmp_indices = np.zeros(ls_xy.shape[0], dtype=int)
    tmp_indices[splitter_indices] = 1
    tmp_indices += 1
    ls_xy = np.repeat(ls_xy, tmp_indices, axis=0)

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
