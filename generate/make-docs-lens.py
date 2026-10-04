"""
Write the data of the lens on the overview page of the documentation
(docs/json/lens_africa.json): the arcs of Africa and the Douglas-Peucker weight of
each vertex. Inside the lens, the figure keeps a vertex where its weight is above
the tolerance and moves it to the nearest point of a grid of whole degrees; as neighbours share their
arcs, the borders stay matched. Run from the root of the repository:

    python generate/make-docs-lens.py
"""

import json

import geopandas as gpd
import numpy as np

import topojson as tp

countries = gpd.read_file(
    "https://d2ad6b4ur7yvpq.cloudfront.net/naturalearth-3.3.0/"
    "ne_50m_admin_0_countries.geojson"
)
africa = countries.query("continent == 'Africa'")[["name", "geometry"]]
africa = africa.clip((-26, -36, 64, 38))  # without islands far off the coast
topo = tp.Topology(africa, prequantize=2e4)

arcs = tp.ops.arc_coordinates(topo.output["arcs"], topo.output["transform"])
count = np.fromiter(map(len, arcs), np.intp)
ends = np.cumsum(count) - 1
weight = tp.ops.dp_weights(np.concatenate(arcs), ends - count + 1, ends)

# weights in thousandths of a degree, -1 for the ends of an arc (always kept)
weight = np.where(np.isfinite(weight), np.round(weight * 1000), -1).astype(int)
lens = {
    "transform": topo.output["transform"],
    "arcs": [np.ravel(arc).tolist() for arc in topo.output["arcs"]],
    "weights": [w.tolist() for w in np.split(weight, np.cumsum(count)[:-1])],
}
with open("docs/json/lens_africa.json", "w") as f:
    json.dump(lens, f, separators=(",", ":"))
