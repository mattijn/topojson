__version__ = "0.8rc1"

from . import extract, join, cut, dedup, hashmap, topology

extract = extract._extracter
join = join._joiner
cut = cut._cutter
dedup = dedup._deduper
hashmap = hashmap._hashmapper
topology = topology._topology
