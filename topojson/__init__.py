from shapely import speedups
from topojson import extract, join, cut
if speedups.available:
    speedups.enable()

extract = extract._extracter
join = join._joiner
cut = cut._cutter