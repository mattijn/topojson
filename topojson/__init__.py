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

"""
