import itertools
import numpy as np
import bisect
from shapely import geometry


def fast_split(line, splitter):
    """
    Split a LineString with a Point or MultiPoint. 
    This function is a replacement for the shapely.ops.split function, but much faster.
    """

    if isinstance(splitter, geometry.Point):
        splitter = geometry.MultiPoint([splitter])

    # compute the distance from the beginning of the linestring for each point on line
    pts_on_line = list(
        itertools.compress(splitter, [line.distance(pt) < 1e-8 for pt in splitter])
    )
    splitter_distances = np.array([line.project(pt) for pt in pts_on_line])
    splitter_distances = splitter_distances[splitter_distances > 0]

    # compute accumulated distances from point-to-point on line of all
    # linestring coordinates
    ls_xy = np.array(line.xy).T
    ls_xy_roll = np.roll(ls_xy, 1, axis=0)
    eucl_dist = np.sqrt(
        (ls_xy_roll[:, 0] - ls_xy[:, 0]) ** 2 + (ls_xy_roll[:, 1] - ls_xy[:, 1]) ** 2
    )
    # the first distance is computed from the first point to the last point, set to 0
    eucl_dist[0] = 0
    ls_cumsum = eucl_dist.cumsum()

    # compute the indices on wich to split the line
    splitter_indices = np.unique(
        [bisect.bisect_left(ls_cumsum, splitter) for splitter in splitter_distances]
    ).astype(int)
    splitter_indices = splitter_indices[splitter_indices < (ls_xy.shape[0] - 1)]

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
        list of tuples, where the key of each tuple is the linestring index 
        and the value of each key is a list of junctions intersecting bounds of linestring
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
