"""
Regenerate the Vega-Lite charts embedded in the documentation (docs/json) by running
the examples shown on the pages. Run from the root of the repository:

    python generate/make-docs-charts.py
"""
from shapely import geometry

import topojson as tp

data = tp.utils.example_data_africa()
polygon = geometry.Polygon([[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]])
quantized = tp.Topology(data, prequantize=200)
topo = tp.Topology(data, toposimplify=4)

charts = {
    # example/settings-tuning.md
    "presimplify": tp.Topology(data, presimplify=4)
    .to_alt()
    .properties(title="presimplify"),
    "toposimplify": topo.to_alt().properties(title="toposimplify"),
    "simplify_with": quantized.toposimplify(
        epsilon=1,
        simplify_algorithm="dp",
        simplify_with="simplification",
        prevent_oversimplify=False,
    )
    .to_alt()
    .properties(title="Douglas-Peucker (package simplification)"),
    "simplify_with_geos": tp.Topology(data, presimplify=1)
    .to_alt()
    .properties(title="presimplify=1")
    | tp.Topology(data, presimplify=1, simplify_with="geos")
    .to_alt()
    .properties(title='presimplify=1, simplify_with="geos"'),
    "simplify_alg": quantized.toposimplify(
        epsilon=1,
        simplify_algorithm="vw",
        simplify_with="simplification",
        prevent_oversimplify=True,
    )
    .to_alt()
    .properties(title="Visvalingam-Whyatt (package simplification)"),
    "winding_order": tp.Topology(polygon, winding_order="CW_CCW", prequantize=False)
    .to_alt(projection="equalEarth", color="type:N")
    .properties(title="CW_CCW")
    & tp.Topology(polygon, winding_order="CCW_CW", prequantize=False)
    .to_alt(projection="equalEarth", color="type:N")
    .properties(title="CCW_CW"),
    # example/output-types.md and example/input-types.md
    "mesh": topo.to_alt(),
    "color_mark": topo.to_alt(color="properties.name:N", projection="equalEarth"),
}

for name, chart in charts.items():
    chart.save(f"docs/json/example_{name}.vl.json")
