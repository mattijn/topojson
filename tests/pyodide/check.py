"""
Compute topologies of the GeoJSON test files and print a hash of each output. The
same script runs in Python and in Pyodide (WebAssembly, where numpy is 32-bit), so
the outputs can be compared. Runs that depend on the GEOS version
(`prequantize=False`) are left out, as Pyodide comes with another GEOS.
"""
import hashlib
import json

import topojson as tp

FILES = [
    "sample",
    "mesh2d",
    "nybb",
    "naturalearth_lowres",
    "naturalearth_alb_grc",
    "multipolygon_with_hole",
    "shared_arc_on_top_of_arc",
]
RUNS = {
    "default": lambda d: tp.Topology(d).to_json(),
    "prequantize=1e4": lambda d: tp.Topology(d, prequantize=1e4).to_json(),
    "shared_coords": lambda d: tp.Topology(d, shared_coords=True).to_json(),
    "toposimplify": lambda d: tp.Topology(d).toposimplify(0.01).to_json(),
    "topoquantize": lambda d: tp.Topology(d).topoquantize(1e3).to_json(),
    "to_geojson": lambda d: tp.Topology(d).to_geojson(),
}

for name in FILES:
    with open(f"tests/files_geojson/{name}.geojson") as f:
        data = json.load(f)
    for run, compute in RUNS.items():
        digest = hashlib.sha256(compute(data).encode()).hexdigest()[:16]
        print(f"{name:26} {run:16} {digest}")
