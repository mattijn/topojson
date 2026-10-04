"""
Write the data of the figures on the pages Example usage, Types of input data,
Settings and tuning, Retrieval data types, Incremental updates and Quantization
(docs/json/fig_*.json),
by running the examples shown on the pages. Each figure is a list of panels with
lines, filled rings, points and labels, drawn by docs/js/steps.js. Run from the
root of the repository:

    python generate/make-docs-figures.py
"""

import json

import fiona
import geopandas as gpd
import numpy as np
import shapefile
import shapely
from shapely import geometry

import topojson as tp


def coords(geom):
    """The lines of a geometry: its rings for polygons."""
    geom = shapely.boundary(geom) if geom.area > 0 else geom
    return [
        np.round(shapely.get_coordinates(g), 6).tolist()
        for g in shapely.get_parts(geom)
    ]


def arcs(topo):
    """The arcs of a Topology, as `to_svg` draws them."""
    xy = tp.ops.arc_coordinates(topo.output["arcs"], topo.output.get("transform"))
    return [np.round(a, 6).tolist() for a in xy]


def rings(geoms):
    """The rings of polygons, to fill."""
    return [
        [
            np.round(shapely.get_coordinates(r), 6).tolist()
            for r in [p.exterior, *p.interiors]
        ]
        for g in geoms
        for p in shapely.get_parts(g)
    ]


def separate(topo):
    """One panel per arc, the other arcs faint, as `to_svg(separate=True)`."""
    every = arcs(topo)
    return [
        {"title": f"arc {i}", "lines": [a], "faint": every, "ends": True}
        for i, a in enumerate(every)
    ]


figures = {}

# example/input-types.md
gdf = gpd.GeoDataFrame(
    {"name": ["abc", "def"]},
    geometry=[
        geometry.Polygon([[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]),
        geometry.Polygon([[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]),
    ],
)
figures["input_geodataframe"] = [
    {
        "fills": rings(gdf.geometry),
        "texts": [[*g.centroid.coords[0], n] for g, n in zip(gdf.geometry, gdf.name)],
    }
]

with open("tests/files_topojson/naturalearth_lowres_africa.topojson") as f:
    africa = tp.Topology(json.load(f), object_name="data")
figures["input_topojson"] = [{"lines": arcs(africa.toposimplify(4))}]

with fiona.open("tests/files_geojson/mesh2d.geojson") as collection:
    figures["input_fiona"] = [{"lines": arcs(tp.Topology(collection))}]

shared = geometry.MultiLineString(
    [
        [(0, 0), (10, 0), (10, 5), (20, 5)],
        [(5, 0), (25, 0), (25, 5), (16, 5), (16, 10), (14, 10), (14, 5), (0, 5)],
    ]
)
figures["input_shapely"] = [{"lines": arcs(tp.Topology(shared)), "ends": True}]

reader = shapefile.Reader("tests/files_shapefile/southamerica.shp")
figures["input_geo_interface"] = [{"lines": arcs(tp.Topology(reader).toposimplify(4))}]

gdf_1 = gpd.GeoDataFrame(
    {"uniq_name": ["abc", "def"], "shrd_name": ["rect", "rect"]},
    geometry=[
        geometry.Polygon([[1, 1], [2, 1], [2, 2], [1, 2], [1, 1]]),
        geometry.Polygon([[0, 1], [1, 1], [1, 2], [0, 2], [0, 1]]),
    ],
)
gdf_2 = gdf_1.dissolve(by="shrd_name", as_index=False)
topo = tp.Topology(
    data=[gdf_1, gdf_2], object_name=["geom_1", "geom_2"], prequantize=False
)
figures["input_list_of_geodataframes"] = [
    {
        "title": f"{name}, by {column}",
        "fills": rings(g.geometry),
        "texts": [[*p.centroid.coords[0], v] for p, v in zip(g.geometry, g[column])],
    }
    for name, column in [("geom_2", "shrd_name"), ("geom_1", "uniq_name")]
    for g in [topo.to_gdf(object_name=name)]
]

# example/settings-tuning.md
squares = geometry.MultiLineString(
    [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]], [[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]]
)
figures["settings_topology_input"] = [{"lines": coords(squares)}]

apart = geometry.MultiLineString(
    [
        [[0, 0], [0.97, 0], [0.97, 1], [0, 1], [0, 0]],
        [[1.03, 0], [2, 0], [2, 1], [1.03, 1], [1.03, 0]],
    ]
)
figures["settings_prequantize_input"] = [{"lines": coords(apart)}]
figures["settings_prequantize_33"] = [
    {"lines": arcs(tp.Topology(apart, prequantize=33)), "ends": True}
]

lines = geometry.MultiLineString(
    [[(0, 0), (10, 0), (10, 5), (20, 5)], [(5, 0), (20, 0), (20, 5), (10, 5), (0, 5)]]
)
figures["settings_shared_coords_input"] = [{"lines": coords(lines), "arrows": True}]
for value in (True, False):
    topo = tp.Topology(lines, shared_coords=value, prequantize=False)
    figures[f"settings_shared_coords_{str(value).lower()}"] = separate(topo)

circle = geometry.Point(0, 0).buffer(1)
figures["settings_prevent_oversimplify_input"] = [{"lines": coords(circle)}]
figures["settings_prevent_oversimplify"] = [
    {
        "title": f"prevent_oversimplify={value}",
        "lines": arcs(topo),
        "faint": coords(circle),
        "ends": True,
    }
    for value in (False, True)
    for topo in [tp.Topology(circle, toposimplify=2, prevent_oversimplify=value)]
]

square = geometry.shape(
    {"type": "Polygon", "coordinates": [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]]}
)
figures["settings_winding_order_input"] = [{"lines": coords(square), "arrows": True}]

# example/example-usage.md
africa = tp.Topology(tp.utils.example_data_africa())
figures["usage_africa"] = [{"lines": arcs(africa.toposimplify(10))}]

# example/output-types.md
two = [
    geometry.Polygon([[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]),
    geometry.Polygon([[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]),
]
figures["output_two_polygons"] = [{"fills": rings(two)}]
topo_two = tp.Topology(
    [
        {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
        {"type": "Polygon", "coordinates": [[[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]]},
    ]
)
figures["output_to_svg"] = [{"lines": arcs(topo_two), "ends": True}]
figures["output_to_svg_separate"] = separate(topo_two)
figures["output_to_gdf"] = [{"fills": rings(africa.to_gdf().geometry)}]

# example/incremental-updates.md
cells = gpd.GeoDataFrame(
    geometry=[
        geometry.box(0, 1, 1, 2),
        geometry.box(1, 1, 2, 2),
        geometry.box(0, 0, 1, 1),
        geometry.box(1, 0, 2, 1),
        geometry.box(2, 1, 3, 2),
    ],
    index=list("ABCDE"),
)
added, window_add = cells.loc[["D"]], [-0.2, 2.2, -0.2, 2.2]
base = tp.Topology(cells.loc[["A", "B", "C"]])
grown = tp.Topology(cells.loc[["A", "B", "C"]]).add(added)
back = tp.Topology(cells.loc[["A", "B", "C"]]).add(added).remove(["D"])


def named(gdf):
    """A label at the centroid of each feature."""
    return [
        [float(g.centroid.x), float(g.centroid.y), str(i)]
        for i, g in gdf.geometry.items()
    ]


def mesh(topo, title, window, fill=None, names=None):
    """The arcs of a Topology, with a filled feature when one was just added."""
    panel = {"title": title, "lines": arcs(topo), "ends": True, "window": window}
    if fill is not None:
        panel["fills"] = rings(fill.geometry)
    if names is not None:
        panel["texts"] = named(names)
    return panel


figures["incremental_add_remove"] = [
    mesh(base, "Topology(A, B, C)", window_add, names=cells.loc[["A", "B", "C"]]),
    mesh(grown, "add(D)", window_add, added, cells.loc[["A", "B", "C", "D"]]),
    mesh(back, "remove(D)", window_add, names=cells.loc[["A", "B", "C"]]),
]

first = cells.loc[["A", "B", "C", "D"]]
second = cells.loc[["B", "C", "D", "E"]].copy()
second.loc["C", "geometry"] = geometry.box(0, 0, 1, 1).buffer(0.2)
synced = tp.Topology(first).sync(second)
window_sync = [-0.35, 3.35, -0.35, 2.35]


figures["incremental_sync"] = [
    {
        "title": "first run",
        "fills": rings(first.geometry),
        "texts": named(first),
        "window": window_sync,
    },
    {
        "title": "next run",
        "fills": rings(second.geometry),
        "faint": coords(cells.loc["A"].geometry),
        "texts": [[*cells.loc["A"].geometry.centroid.coords[0], "A"], *named(second)],
        "window": window_sync,
    },
    mesh(synced, "sync", window_sync),
]

# example/quantization.md
line = geometry.LineString(
    [(0, 1), (2.6, 4.6), (5.3, 3.9), (7.1, 6), (9.6, 0), (12, 3.4)]
)
snap_window = [-0.5, 12.5, -0.5, 6.5]


def lattice(transform, x0, x1, y0, y1):
    """The points of a transform inside a window."""
    (kx, ky), (tx, ty) = transform["scale"], transform["translate"]
    xs = tx + kx * np.arange(np.ceil((x0 - tx) / kx - 1e-9), (x1 - tx) / kx + 1e-9)
    ys = ty + ky * np.arange(np.ceil((y0 - ty) / ky - 1e-9), (y1 - ty) / ky + 1e-9)
    return [[float(x), float(y)] for y in ys for x in xs]


def grid_lines(transform, x0, x1, y0, y1):
    """The lines of a transform through a window."""
    (kx, ky), (tx, ty) = transform["scale"], transform["translate"]
    xs = tx + kx * np.arange(np.ceil((x0 - tx) / kx - 1e-9), (x1 - tx) / kx + 1e-9)
    ys = ty + ky * np.arange(np.ceil((y0 - ty) / ky - 1e-9), (y1 - ty) / ky + 1e-9)
    return [[[float(x), y0], [float(x), y1]] for x in xs] + [
        [[x0, float(y)], [x1, float(y)]] for y in ys
    ]


def on_fine(xy, transform):
    """Vertices that lie on a point of the transform."""
    (kx, ky), (tx, ty) = transform["scale"], transform["translate"]
    steps = (np.asarray(xy) - [tx, ty]) / [kx, ky]
    return np.isclose(steps, np.round(steps), atol=1e-6).all(1)


def snap_panel(topo, title):
    """The input line faint, the grid as dots, the quantized line dashed."""
    t = topo.output["transform"]
    quantized = arcs(topo)
    xy = [p for a in quantized for p in a]
    return {
        "title": title,
        "subtitle": f"cells of {t['scale'][0]:g} × {t['scale'][1]:g}",  # noqa: RUF001
        "faint": coords(line),
        "dashed": quantized,
        "grid": lattice(t, *snap_window),
        "filled": [p for p, ok in zip(xy, on_fine(xy, t)) if ok],
        "dots": [p for p, ok in zip(xy, on_fine(xy, t)) if not ok],
        "window": snap_window,
    }


figures["quantization_snap"] = [
    snap_panel(tp.Topology(line, prequantize=5), "prequantize=5"),
    snap_panel(
        tp.Topology(line, prequantize={"scale": [2, 2], "translate": [0, 0]}),
        "square cells",
    ),
]

fine = {"scale": [1, 1], "translate": [0, 0]}
on_grid = tp.Topology(line, prequantize=fine)
source = [c for g in on_grid.to_gdf().geometry for c in coords(g)]


def nested_panel(topo, title):
    """The fine line faint, the coarse grid as lines, vertices filled when they
    lie on the fine grid."""
    t = topo.output["transform"]
    quantized = arcs(topo)
    xy = [p for a in quantized for p in a]
    ok = on_fine(xy, fine)
    return {
        "title": title,
        "subtitle": f"{int(ok.sum())} of {len(xy)} on the fine grid",
        "faint": source,
        "dashed": quantized,
        "grid": lattice(fine, *snap_window),
        "rules": grid_lines(t, *snap_window),
        "filled": [p for p, hit in zip(xy, ok) if hit],
        "dots": [p for p, hit in zip(xy, ok) if not hit],
        "window": snap_window,
    }


figures["quantization_nested"] = [
    nested_panel(on_grid.topoquantize(6), "topoquantize(6)"),
    nested_panel(
        on_grid.topoquantize({"scale": [3, 3], "translate": [0, 0]}),
        "topoquantize with cells of 3",
    ),
]

countries = gpd.read_file(
    "https://d2ad6b4ur7yvpq.cloudfront.net/naturalearth-3.3.0/"
    "ne_50m_admin_0_countries.geojson"
)
chile = countries.query("name == 'Chile'")[["name", "geometry"]]
chile = chile.clip((-80, -60, -60, -15))
x0, y0, x1, y1 = chile.total_bounds
k_cell = 0.5
square = {
    "scale": [k_cell / np.cos(np.radians((y0 + y1) / 2)), k_cell],
    "translate": [x0, y0],
}


def chile_panel(topo, title):
    """Mainland Chile and the lines of its grid."""
    t = topo.output["transform"]
    bx0, by0, bx1, by1 = topo.output["bbox"]
    return {
        "title": title,
        "fills": rings(topo.to_gdf().geometry),
        "rules": grid_lines(t, bx0, bx1, by0, by1),
    }


figures["quantization_cells"] = [
    chile_panel(tp.Topology(chile, prequantize=40), "prequantize=40"),
    chile_panel(tp.Topology(chile, prequantize=square), "square cells of 0.5°"),
]

rectangles = gpd.GeoDataFrame(
    {"name": ["a1", "a2", "b1", "b2"]},
    geometry=[
        geometry.box(0, 0, 1.0, 1),
        geometry.box(1.04, 0, 2, 1),
        geometry.box(0, 1.2, 1.04, 2.2),
        geometry.box(1.06, 1.2, 2, 2.2),
    ],
)
gap = tp.Topology(rectangles, prequantize=21)
gap_xy = [p for a in arcs(gap) for p in a]
gap_t = gap.output["transform"]


def gap_panel(title, window):
    """A zoom on the gap, with the input faint and the quantized rectangles filled."""
    return {
        "title": title,
        "fills": rings(gap.to_gdf().geometry),
        "faint": [c for g in rectangles.geometry for c in coords(g)],
        "grid": lattice(gap_t, *window),
        "filled": [p for p, ok in zip(gap_xy, on_fine(gap_xy, gap_t)) if ok],
        "texts": [
            [*g.centroid.coords[0], n]
            for g, n in zip(rectangles.geometry, rectangles.name)
        ],
        "window": window,
    }


figures["quantization_gap"] = [
    gap_panel("a gap of 0.04 closes", [0.55, 1.5, -0.12, 1.12]),
    gap_panel("a gap of 0.02 stays open", [0.55, 1.5, 1.08, 2.32]),
]


def rounded(panels):
    """Round the coordinates to a ten-thousandth of the extent of the figure, far
    finer than a pixel, to keep the files small."""

    def points(x):
        if isinstance(x[0], (int, float)):
            yield x[:2]
        else:
            for v in x:
                yield from points(v)

    keys = (
        "lines",
        "faint",
        "dashed",
        "fills",
        "dots",
        "grid",
        "filled",
        "rules",
        "texts",
        "window",
    )
    xy = np.array([q for p in panels for k in keys if p.get(k) for q in points(p[k])])
    decimals = max(0, int(np.ceil(-np.log10(np.ptp(xy, 0).max() / 1e4))))

    def walk(x):
        if isinstance(x, list):
            return [walk(v) for v in x]
        return round(x, decimals) if isinstance(x, float) else x

    return [{k: walk(v) if k in keys else v for k, v in p.items()} for p in panels]


for name, panels in figures.items():
    with open(f"docs/json/fig_{name}.json", "w") as f:
        json.dump({"panels": rounded(panels)}, f, separators=(",", ":"))
