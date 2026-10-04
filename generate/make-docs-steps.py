"""
Write the data of the figures on the page How it works (docs/json/steps.json): what
each step of the computation gives for the toy example of that page. Run from the
root of the repository:

    python generate/make-docs-steps.py
"""

import json

import numpy as np
from shapely import geometry

import topojson as tp
from topojson.core.cut import Cut
from topojson.core.dedup import Dedup
from topojson.core.extract import Extract
from topojson.core.hashmap import Hashmap
from topojson.core.join import Join

data = geometry.MultiLineString(
    [[(0, 0), (10, 0), (5, 5), (15, 5)], [(15, 0), (15, 5), (5, 5), (0, 5)]]
)


def coords(lines):
    return [np.asarray(getattr(line, "coords", line), float).tolist() for line in lines]


cut = Cut(data).output
dedup = Dedup(data).output
hashmap = Hashmap(data).output
topology = tp.Topology(data)
steps = {
    "extract": {"lines": coords(Extract(data).output["linestrings"])},
    "join": {
        "lines": coords(Join(data).output["linestrings"]),
        "junctions": [list(p.coords[0]) for p in Join(data).output["junctions"]],
    },
    # the parts of each line, in the order of the lines
    "cut": {
        "parts": coords(cut["linestrings"]),
        "line": [
            int(i)
            for i, row in enumerate(cut["bookkeeping_linestrings"])
            for j in row
            if j == j
        ],
    },
    "dedup": {
        "arcs": coords(dedup["linestrings"]),
        "shared": [int(i) for i in dedup["bookkeeping_shared_arcs"]],
    },
    # each line as references to the arcs, ~i for an arc used backward
    "hashmap": {
        "arcs": coords(hashmap["linestrings"]),
        "lines": hashmap["objects"]["data"]["geometries"][0]["arcs"],
    },
    # the arcs of the topology, quantized as by default
    "topology": {
        "arcs": coords(
            tp.ops.arc_coordinates(
                topology.output["arcs"], topology.output["transform"]
            )
        ),
    },
}
with open("docs/json/steps.json", "w") as f:
    json.dump(steps, f, separators=(",", ":"))
