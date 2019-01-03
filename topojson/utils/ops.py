import itertools
import numpy as np
import bisect

def fast_split(line, splitter):
    """
    Split a LineString with a Point or MultiPoint. 
    This function is a replacement for the shapely.ops.split function, but much faster.
    """

    # compute the distance from the beginning of the linestring for each point on line
    pts_on_line = list(itertools.compress(splitter, [line.distance(pt)>1e-8 for pt in splitter]))
    splitter_distances = [line.project(pt) for pt in pts_on_line]

    # compute accumulated distances from point-to-point on line of all linestring coordinates
    ls_xy = np.array(line.xy).T
    ls_xy_roll = np.roll(ls_xy, 1, axis=0)
    eucl_dist = np.sqrt((ls_xy_roll[:,0] - ls_xy[:,0])**2 + (ls_xy_roll[:,1] - ls_xy[:,1])**2)
    ls_cumsum = eucl_dist.cumsum()

    # compute the indices on wich to split the line
    splitter_indices = np.unique([bisect.bisect_left(ls_cumsum, splitter) for splitter in splitter_distances])
    splitter_indices = splitter_indices[(splitter_indices>1) & (splitter_indices < (ls_xy.shape[0] - 1))]

    # split the linestring where each sub-array includes the split-point
    # create a new array with the index elements repeated
    tmp_indices = np.zeros(ls_xy.shape[0], dtype = int)
    tmp_indices[splitter_indices] = 1
    tmp_indices += 1
    ls_xy = np.repeat(ls_xy, tmp_indices, axis = 0)

    # update indices to account for the changed array
    splitter_indices = splitter_indices + np.arange(1, len(splitter_indices)+1)

    # split using the indices as usual
    slines = np.split(ls_xy, splitter_indices, axis=0)

    return slines