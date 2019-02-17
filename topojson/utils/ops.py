import itertools
import numpy as np
from shapely import geometry


def asvoid(arr):
    """
    View the array as dtype np.void (bytes). The items along the last axis are
    viewed as one value. This allows comparisons to be performed which treat
    entire rows as one value.
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


def insertor(geoms):
    """
    generator function to use stream loading of geometries for creating a rtree index
    """

    for i, obj in enumerate(geoms):
        yield (i, obj.bounds, None)


def get_matches(geoms, tree_idx):
    """
    Function to return the indici of the rtree that intersects with the input geometries
    
    Parameters
    ----------
    geoms : list
        list of geometries to compare against the rtree index
    tree_idx: rtree.index.Index
        an rtree indexing object
        
    Returns
    -------
    matches: list
        list of tuples, where the key of each tuple is the linestring index and the 
        value of each key is a list of junctions intersecting bounds of linestring.
    """

    matches = []
    for idx_ls, obj in enumerate(geoms):
        intersect_idx = list(tree_idx.intersection(obj.bounds))
        if len(intersect_idx):
            matches.append([[idx_ls], intersect_idx])
    return matches


def select_unique(data):
    sorted_data = data[np.lexsort(data.T), :]
    row_mask = np.append([True], np.any(np.diff(sorted_data, axis=0), 1))

    return sorted_data[row_mask]


def select_unique_combs(linestrings):
    try:
        from rtree import index
    except:
        all_line_combs = list(itertools.combinations(range(len(linestrings)), 2))
        return all_line_combs
    # create spatial index on junctions including performance properties
    p = index.Property()
    p.leaf_capacity = 1000
    p.fill_factor = 0.9
    tree_idx = index.Index(insertor(linestrings), properties=p)

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
