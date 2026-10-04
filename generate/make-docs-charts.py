"""
Regenerate the Vega-Lite charts embedded in the documentation (docs/json) by running
the examples shown on the pages. Run from the root of the repository:

    python generate/make-docs-charts.py
"""

import altair as alt
import numpy as np
import pandas as pd
from shapely import geometry

import topojson as tp

data = tp.utils.example_data_africa()
polygon = geometry.Polygon([[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]])
quantized = tp.Topology(data, prequantize=200)
topo = tp.Topology(data, toposimplify=4)

BLUE, AMBER, GREY = "#378ADD", "#BA7517", "#888780"

# example/settings-tuning.md
wavy = np.array(
    [(0, 1), (1.2, 2.9), (2.6, 4.6), (3.8, 4.1), (5.3, 3.9), (6.2, 5.2), (7.1, 6),
     (8.0, 3.1), (9.6, 0), (10.7, 1.6), (12, 3.4)]
)  # fmt: skip


def kept(line, keep, px=22):
    """A line (blue) with the Douglas-Peucker weight of each inner vertex, and the
    line simplified to a share of its inner vertices (dashed): the vertices with the
    largest weights are kept (filled)."""
    weight = tp.ops.dp_weights(line, [0], [len(line) - 1])
    (simple,), epsilon = tp.ops.simplify_keep([line], keep)
    df = pd.DataFrame({"x": line[:, 0], "y": line[:, 1], "o": range(len(line))})
    df["kept"] = weight > epsilon
    df["label"] = [f"{w:.2f}" if np.isfinite(w) else "" for w in weight]
    # labels on the outer side of each bend
    out = line - (np.roll(line, 1, 0) + np.roll(line, -1, 0)) / 2
    out /= np.hypot(*out.T)[:, None]
    df["lx"], df["ly"] = (line + 1.1 * out).T
    base = alt.Chart(df).encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[-0.5, 12.5]), axis=None),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[-1.4, 7.4]), axis=None),
        order="o:Q",
    )
    inner = len(line) - 2
    return alt.layer(
        base.mark_line(color=BLUE, strokeWidth=1.5),
        base.transform_filter("datum.kept").mark_line(
            color=AMBER, strokeWidth=2, strokeDash=[5, 3]
        ),
        base.mark_point(size=60, color=AMBER, strokeWidth=1.5, opacity=1).encode(
            fill=alt.condition("datum.kept", alt.value(AMBER), alt.value(None))
        ),
        base.mark_text(color=GREY).encode(x="lx:Q", y="ly:Q", text="label:N"),
    ).properties(
        title=alt.Title(
            f"keep={keep}",
            subtitle=f"{len(simple) - 2} of {inner} inner vertices, as epsilon "
            f"{epsilon:.2f}",
        ),
        width=13 * px,
        height=8.8 * px,
    )


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
    "toposimplify_keep": kept(wavy, 0.25) | kept(wavy, 0.5),
    # example/output-types.md and example/input-types.md
    "mesh": topo.to_alt(),
    "color_mark": topo.to_alt(color="properties.name:N", projection="equalEarth"),
}

# transparent, so the charts follow the background of the page
for name, chart in charts.items():
    chart = chart.properties(background="transparent").configure_view(
        fill="transparent", continuousWidth=400, continuousHeight=300
    )
    chart.save(f"docs/json/example_{name}.vl.json")
