from topojson import extract, join, cut, dedup, hashmap, topology

extract = extract._extracter
join = join._joiner
cut = cut._cutter
dedup = dedup._deduper
hashmap = hashmap._hashmapper
topology = topology._topology


"""
# https://bost.ocks.org/mike/simplify/
# https://github.com/urschrei/simplification

# testing
# https://github.com/topojson/topojson-client/blob/master/test/feature-test.js

# links
# https://github.com/geopandas/geopandas/blob/master/geopandas/tools/sjoin.py
# https://geoffboeing.com/2016/10/r-tree-spatial-index-python/
# http://toblerity.org/rtree/performance.html
# https://snorfalorpagus.net/blog/2014/05/12/using-rtree-spatial-indexing-with-ogr/

# rtree indexing example:

from rtree import index
from collections import namedtuple
import numpy as np

def insertor(geoms):
    "
    generator function to use stream loading of geometries for creating a rtree index
    "

    for i, obj in enumerate(geoms):
        yield (i, obj.bounds, None)

def get_matches(geoms, tree_idx):
    "
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
    "
    
    matches = []
    for idx_ls, obj in enumerate(geoms):
        idx_js = list(tree_idx.intersection(obj.bounds))
        if len(idx_js):
            matches.append(Match(idx_ls, idx_js))
    return matches   

# create namedtuple
Match = namedtuple('Match', ['idx_ls','idx_js'])

# create spatial index on junctions including performance properties
p = index.Property()
p.leaf_capacity = 1000
p.fill_factor = 0.9
tree_idx = index.Index(insertor(jo["junctions"]), properties=p)

# get the matching junction index of each linestring (returns matches only)
idxmatch = dict(get_matches(jo['linestrings'], tree_idx))

# list of linestrings and junctions. 
# ls_idx contains linestrings that has matching junctions in js_idx
# len(ls_idx) == len(js_idx)

# ls_idx = np.array(list(idxmatch.keys()))[None].T
ls_idx = list(idxmatch.keys())
js_idx = [v for v in idxmatch.values()]

line = geometry.LineString(jo["linestrings"][ls_idx[11]])
mpt = geometry.MultiPoint([jo["junctions"][i] for i in js_idx[11]])

splitter_distances = [line.project(pt) for pt in mpt.geoms]
"""
