"""
Write the data of the figures on the pages Types of input data and Settings and
tuning (docs/json/fig_*.json), by running the examples shown on the pages. Each
figure is a list of panels with lines, filled rings, points and labels, drawn by
docs/js/steps.js. Run from the root of the repository:

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


def rounded(panels):
    """Round the coordinates to a ten-thousandth of the extent of the figure, far
    finer than a pixel, to keep the files small."""

    def points(x):
        if isinstance(x[0], (int, float)):
            yield x[:2]
        else:
            for v in x:
                yield from points(v)

    keys = ("lines", "faint", "fills", "dots", "texts")
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
