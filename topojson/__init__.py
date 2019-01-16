from topojson import extract, join, cut, dedup, hashmap, topology

__doc__ = """Encode geometric data into the TopoJSON format"""
__version__ = "0.8rc1"

extract = extract._extracter
join = join._joiner
cut = cut._cutter
dedup = dedup._deduper
hashmap = hashmap._hashmapper
topology = topology._topology
