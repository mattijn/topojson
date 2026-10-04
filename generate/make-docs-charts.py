"""
Regenerate the Vega-Lite charts embedded in the documentation (docs/json) by running
the examples shown on the pages. Run from the root of the repository:

    python generate/make-docs-charts.py
"""

import altair as alt
import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from shapely import geometry

import topojson as tp

data = tp.utils.example_data_africa()
polygon = geometry.Polygon([[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]])
quantized = tp.Topology(data, prequantize=200)
topo = tp.Topology(data, toposimplify=4)

# example/quantization.md
countries = gpd.read_file(
    "https://d2ad6b4ur7yvpq.cloudfront.net/naturalearth-3.3.0/"
    "ne_50m_admin_0_countries.geojson"
)
chile = countries.query("name == 'Chile'")[["name", "geometry"]]
chile = chile.clip((-80, -60, -60, -15))  # the mainland, without Easter Island
x0, y0, x1, y1 = chile.total_bounds
k = 0.5
square = {
    "scale": [k / np.cos(np.radians((y0 + y1) / 2)), k],
    "translate": [x0, y0],
}
line = geometry.LineString(
    [(0, 1), (2.6, 4.6), (5.3, 3.9), (7.1, 6), (9.6, 0), (12, 3.4)]
)
rectangles = gpd.GeoDataFrame(
    {"name": ["a1", "a2", "b1", "b2"]},
    geometry=[
        geometry.box(0, 0, 1.0, 1),
        geometry.box(1.04, 0, 2, 1),
        geometry.box(0, 1.2, 1.04, 2.2),
        geometry.box(1.06, 1.2, 2, 2.2),
    ],
)


def on_grid(topo, title, projection="mercator", **kwargs):
    """The topology with the lines through the points of its grid on top."""
    (kx, ky), (tx, ty) = topo.output["transform"].values()
    bx0, by0, bx1, by1 = topo.output["bbox"]
    xs = tx + kx * np.arange(np.floor((bx0 - tx) / kx), np.ceil((bx1 - tx) / kx) + 1)
    ys = ty + ky * np.arange(np.floor((by0 - ty) / ky), np.ceil((by1 - ty) / ky) + 1)
    lines = [geometry.LineString([(x, ys[0]), (x, ys[-1])]) for x in xs]
    lines += [geometry.LineString([(xs[0], y), (xs[-1], y)]) for y in ys]
    grid = (
        alt.Chart(gpd.GeoDataFrame(geometry=lines))
        .mark_geoshape(filled=False, stroke="gray", strokeWidth=0.5, opacity=0.5)
        .project(type=projection, reflectY=projection == "identity")
    )
    shapes = topo.to_alt(projection=projection, **kwargs)
    if "color" in kwargs:
        shapes = shapes.encode(color=alt.Color(kwargs["color"], legend=None))
    size = {"height": 420, "width": 170} if projection == "mercator" else {}
    return alt.layer(shapes, grid).properties(title=title, **size)


BLUE, AMBER, GREY = "#378ADD", "#BA7517", "#888780"


def panel(topo, source, title, window, fine=None, px=22):
    """The input (blue), the points of the grid (grey) and the quantized result
    (dashed). With `fine`, the dots are the points of that finer grid, the lines
    those of the grid of `topo`, and a vertex is filled when it lies on a dot."""
    x0, x1, y0, y1 = window
    transform = topo.output["transform"]
    (kx, ky), (tx, ty) = (fine or transform).values()
    i, j = np.meshgrid(
        np.arange(np.ceil((x0 - tx) / kx), (x1 - tx) / kx + 1e-9),
        np.arange(np.ceil((y0 - ty) / ky), (y1 - ty) / ky + 1e-9),
    )
    dots = pd.DataFrame({"x": tx + kx * i.ravel(), "y": ty + ky * j.ravel()})

    def paths(geoms):
        geoms = np.array(list(geoms), dtype=object)
        geoms = np.where(shapely.area(geoms) > 0, shapely.boundary(geoms), geoms)
        xy, part = shapely.get_coordinates(shapely.get_parts(geoms), return_index=True)
        return pd.DataFrame({"x": xy[:, 0], "y": xy[:, 1], "part": part,
                             "o": np.arange(len(xy))})  # fmt: skip

    result = paths(topo.to_gdf().geometry)
    steps = (result[["x", "y"]] - [tx, ty]) / [kx, ky]
    result["on"] = np.isclose(steps, np.round(steps), atol=1e-6).all(1)
    on = int(result.drop_duplicates(["x", "y"])["on"].sum())
    n = len(result.drop_duplicates(["x", "y"]))

    x = alt.X("x:Q", scale=alt.Scale(domain=[x0, x1]), axis=None)
    y = alt.Y("y:Q", scale=alt.Scale(domain=[y0, y1]), axis=None)
    base = alt.Chart().encode(x=x, y=y)
    layers = [
        base.mark_circle(size=6, color=GREY, opacity=1).properties(data=dots),
        base.mark_line(color=BLUE, strokeWidth=1.5, clip=True)
        .encode(detail="part:N", order="o:Q")
        .properties(data=paths(gpd.GeoSeries(source))),
        base.mark_line(color=AMBER, strokeWidth=2, strokeDash=[5, 3], clip=True)
        .encode(detail="part:N", order="o:Q")
        .properties(data=result),
        base.mark_point(size=60, color=AMBER, strokeWidth=1.5, opacity=1, clip=True)
        .encode(fill=alt.condition("datum.on", alt.value(AMBER), alt.value(None)))
        .properties(data=result),
    ]
    if fine:
        (cx, cy), (ox, oy) = transform.values()
        lines = [
            {"x": v, "x2": v, "y": y0, "y2": y1}
            for v in ox + cx * np.arange(np.ceil((x0 - ox) / cx), (x1 - ox) / cx)
        ]
        lines += [
            {"x": x0, "x2": x1, "y": v, "y2": v}
            for v in oy + cy * np.arange(np.ceil((y0 - oy) / cy), (y1 - oy) / cy)
        ]
        layers.insert(
            0,
            base.mark_rule(color=AMBER, strokeWidth=0.5, opacity=0.6)
            .encode(x2="x2", y2="y2")
            .properties(data=pd.DataFrame(lines)),
        )
        subtitle = f"{on} of {n} vertices on a point of the fine grid"
    else:
        subtitle = f"cells of {kx:g} × {ky:g}"  # noqa: RUF001 a multiplication sign
    return alt.layer(*layers).properties(
        title=alt.Title(title, subtitle=subtitle),
        width=(x1 - x0) * px,
        height=(y1 - y0) * px,
    )  # fmt: skip


gap = tp.Topology(rectangles, prequantize=21)
fine = {"scale": [1, 1], "translate": [0, 0]}
on_fine = tp.Topology(line, prequantize=fine)

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
    # example/quantization.md
    "quantization_snap": panel(
        tp.Topology(line, prequantize=5), line, "prequantize=5", (-0.5, 12.5, -0.5, 6.5)
    )
    | panel(
        tp.Topology(line, prequantize={"scale": [2, 2], "translate": [0, 0]}),
        line,
        "square cells",
        (-0.5, 12.5, -0.5, 6.5),
    ),
    "quantization_nested": panel(
        on_fine.topoquantize(6),
        on_fine.to_gdf().geometry,
        "topoquantize(6)",
        (-0.5, 12.5, -0.5, 6.5),
        fine=fine,
    )
    | panel(
        on_fine.topoquantize({"scale": [3, 3], "translate": [0, 0]}),
        on_fine.to_gdf().geometry,
        "topoquantize with cells of 3",
        (-0.5, 12.5, -0.5, 6.5),
        fine=fine,
    ),
    "quantization_cells": on_grid(tp.Topology(chile, prequantize=40), "prequantize=40")
    | on_grid(tp.Topology(chile, prequantize=square), "square cells of 0.5°"),
    "quantization_gap": panel(
        gap,
        rectangles.geometry,
        "a gap of 0.04 closes",
        (0.55, 1.5, -0.12, 1.12),
        px=150,
    )
    | panel(
        gap,
        rectangles.geometry,
        "a gap of 0.02 stays open",
        (0.55, 1.5, 1.08, 2.32),
        px=150,
    ),
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
