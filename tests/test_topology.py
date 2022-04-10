import os
import json
from shapely import geometry, wkt
import geopandas
import geojson
import fiona
import topojson
import pytest


# this test was added since geometries of only linestrings resulted in a topojson
# file that returns an empty geodataframe when reading
def test_topology_linestrings_parsed_to_gdf():
    data = [
        {"type": "LineString", "coordinates": [[4, 0], [2, 2], [0, 0]]},
        {"type": "LineString", "coordinates": [[0, 2], [1, 1], [2, 2], [3, 1], [4, 2]]},
    ]
    topo = topojson.Topology(data).to_gdf()

    assert topo["geometry"][0].wkt != "GEOMETRYCOLLECTION EMPTY"
    assert topo["geometry"][0].type == "LineString"


def test_topology_naturalearth_lowres_defaults():
    data = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
    topo = topojson.Topology(data).to_dict()

    assert len(topo["objects"]) == 1


# test winding order using TopoOptions object
def test_topology_winding_order_TopoOptions():
    data = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
    data = data[(data.name == "South Africa")]
    topo = topojson.Topology(data, winding_order="CW_CCW").to_dict(options=True)

    assert len(topo["objects"]) == 1
    assert len(topo["options"]) == 11


# test winding order using kwarg variables
def test_topology_winding_order_kwarg_vars():

    data = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
    data = data[(data.name == "South Africa")]
    topo = topojson.Topology(data, winding_order="CW_CCW").to_dict(options=True)

    assert len(topo["objects"]) == 1
    assert len(topo["options"]) == 11


def test_topology_computing_topology():
    data = [
        {"type": "LineString", "coordinates": [[4, 0], [2, 2], [0, 0]]},
        {"type": "LineString", "coordinates": [[0, 2], [1, 1], [2, 2], [3, 1], [4, 2]]},
    ]
    no_topo = topojson.Topology(data, topology=False, prequantize=False).to_dict()
    topo = topojson.Topology(data, topology=True, prequantize=False).to_dict()

    assert len(topo["arcs"]) == 4
    assert len(no_topo["arcs"]) == 2


# test prequantization without computing topology
def test_topology_prequantization():

    data = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
    data = data[
        (data.name == "Botswana")
        | (data.name == "South Africa")
        | (data.name == "Zimbabwe")
        | (data.name == "Mozambique")
        | (data.name == "Zambia")
    ]
    topo = topojson.Topology(data, topology=False, prequantize=1e4).to_dict()

    assert "transform" in topo.keys()


# test prequantization without computing topology
def test_topology_prequantization_including_delta_encoding():

    data = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
    data = data[
        (data.name == "Botswana")
        | (data.name == "South Africa")
        | (data.name == "Zimbabwe")
        | (data.name == "Mozambique")
        | (data.name == "Zambia")
    ]
    topo = topojson.Topology(data, topology=False, prequantize=1e4).to_dict()

    assert "transform" in topo.keys()


def test_topology_toposimplify_set_in_options():
    data = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
    data = data[(data.name == "Antarctica")]
    topo = topojson.Topology(
        data, prequantize=True, simplify_with="shapely", toposimplify=4
    ).to_dict()

    assert "transform" in topo.keys()


def test_topology_toposimplify_as_chaining():
    data = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
    data = data[(data.name == "Antarctica")]
    topo = topojson.Topology(data, prequantize=True, simplify_with="shapely")
    topos = topo.toposimplify(2).to_dict()

    assert "transform" in topos.keys()


def test_topology_topoquantize_as_chaining():
    data = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
    data = data[(data.name == "Antarctica")]
    topo = topojson.Topology(data, prequantize=False, simplify_with="shapely")
    topos = topo.topoquantize(1e2).to_dict()

    assert "transform" in topos.keys()


def test_topology_prequantize_topoquantize_as_chaining():
    data = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
    data = data[(data.name == "Antarctica")]
    topo = topojson.Topology(data, prequantize=1e6, topology=True)
    topos = topo.topoquantize(1e5).to_dict()

    assert "transform" in topos.keys()


def test_topology_to_svg():
    data = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
    data = data[(data.name == "Antarctica")]
    topo = topojson.Topology(data, prequantize=1e6, presimplify=50, topology=True)

    assert topo.to_svg() == None


def test_topology_with_arcs_without_linestrings():
    data = [
        {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
        {"type": "Polygon", "coordinates": [[[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]]},
    ]
    topo = topojson.Topology(data, prequantize=False, topology=True).to_dict()

    assert "linestrings" not in topo.keys()


def test_topology_widget():
    data = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
    data = data[(data.continent == "Africa")]
    topo = topojson.Topology(data, prequantize=1e6, topology=True)
    widget = topo.to_widget()

    assert len(widget.widget.children) == 4  # pylint: disable=no-member


def test_topology_simplification_vw():
    data = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
    data = data[(data.continent == "South America")]
    topo = topojson.Topology(
        data,
        prequantize=False,
        topology=True,
        toposimplify=1,
        simplify_with="simplification",
        simplify_algorithm="vw",
    ).to_dict()

    assert len(topo["arcs"][0]) == 4


def test_topology_simplification_dp():
    data = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
    data = data[(data.continent == "South America")]
    topo = topojson.Topology(
        data,
        prequantize=False,
        topology=True,
        toposimplify=1,
        simplify_with="simplification",
        simplify_algorithm="dp",
    ).to_dict()

    assert len(topo["arcs"][0]) == 3


def test_topology_polygon_point():
    data = [
        {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
        {"type": "Point", "coordinates": [-0.5, 1.5]},
    ]
    topo = topojson.Topology(data, topoquantize=True).to_dict()

    assert len(topo["arcs"]) == 1
    assert topo["objects"]["data"]["geometries"][1]["coordinates"] == [0, 999999]


# changed test since, quantization process catch zero-division
def test_topology_point():
    data = [{"type": "Point", "coordinates": [0.5, 0.5]}]
    topo = topojson.Topology(data, topoquantize=True).to_dict()

    assert len(topo["arcs"]) == 0


def test_topology_multipoint():
    data = [{"type": "MultiPoint", "coordinates": [[0.5, 0.5], [1.0, 1.0]]}]
    topo = topojson.Topology(data, topoquantize=True).to_dict()

    assert len(topo["arcs"]) == 0
    assert topo["objects"]["data"]["geometries"][0]["coordinates"] == [
        [0, 0],
        [999999, 999999],
    ]
    assert topo["transform"]["translate"] == [0.5, 0.5]


def test_topology_polygon():
    data = [
        {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]}
    ]
    topo = topojson.Topology(data, topoquantize=True).to_dict()

    assert topo["transform"]["translate"] == [0.0, 0.0]


def test_topology_point_multipoint():
    data = [
        {"type": "Point", "coordinates": [0.5, 0.5]},
        {"type": "MultiPoint", "coordinates": [[0.5, 0.5], [1.0, 1.0]]},
        {"type": "Point", "coordinates": [2.5, 3.5]},
    ]
    topo = topojson.Topology(data, topoquantize=True).to_dict()

    assert topo["objects"]["data"]["geometries"][0]["coordinates"] == [0, 0]
    assert topo["objects"]["data"]["geometries"][2]["coordinates"] == [999999, 999999]


def test_topology_to_geojson_nested_geometrycollection():
    data = {
        "collection": {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[0.1, 0.2], [0.3, 0.4]],
                    },
                },
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "GeometryCollection",
                        "geometries": [
                            {
                                "type": "Polygon",
                                "coordinates": [[[0.5, 0.6], [0.7, 0.8], [0.9, 1.0]]],
                            },
                            {
                                "type": "LineString",
                                "coordinates": [[0.1, 0.2], [0.3, 0.4]],
                            },
                        ],
                    },
                },
            ],
        }
    }
    topo = topojson.Topology(data).to_geojson()

    assert "]]}]}}]}" in topo


def test_topology_to_geojson_polygon_geometrycollection():
    data = {
        "bar": {"type": "Polygon", "coordinates": [[[0, 0], [1, 1], [2, 0]]]},
        "foo": {
            "type": "GeometryCollection",
            "geometries": [
                {"type": "LineString", "coordinates": [[0.1, 0.2], [0.3, 0.4]]}
            ],
        },
    }
    topo = topojson.Topology(data).to_geojson()

    assert "]]}}]}" in topo


def test_topology_to_geojson_linestring_polygon():
    data = {
        "foo": {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": [[0.1, 0.2], [0.3, 0.4]]},
        },
        "bar": {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[0.5, 0.6], [0.7, 0.8], [0.9, 1.0]]],
            },
        },
    }
    topo = topojson.Topology(data).to_geojson()

    assert "]]}}]}" in topo


def test_topology_to_geojson_polygon_point():
    data = [
        {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
        {"type": "Point", "coordinates": [0.5, 0.5]},
    ]
    topo = topojson.Topology(data).to_geojson()

    assert "]]]}}" in topo  # feat 1
    assert "]}}]}" in topo  # feat 2


def test_topology_to_geojson_quantized_points_only():
    data = [{"type": "MultiPoint", "coordinates": [[0.5, 0.5], [1.0, 1.0]]}]
    geo = topojson.Topology(data, prequantize=False).to_geojson()

    gj = json.loads(geo)
    assert gj["type"] == "FeatureCollection"
    assert gj["features"][0]["geometry"]["coordinates"] == [[0.5, 0.5], [1.0, 1.0]]


def test_topology_double_toposimplify_points_only():
    data = [{"type": "MultiPoint", "coordinates": [[0.5, 0.5], [1.0, 1.0]]}]
    topo = topojson.Topology(data, prequantize=True)
    topo = topo.toposimplify(True, inplace=False)
    geo = topo.to_geojson()

    gj = json.loads(geo)
    assert gj["type"] == "FeatureCollection"
    assert gj["features"][0]["geometry"]["coordinates"][0] == [0.5, 0.5]
    assert gj["features"][0]["geometry"]["coordinates"][1] == [1.0, 1.0]


def test_topology_to_json(tmp_path):
    topo_file = os.path.join(tmp_path, "topo.json")
    data = [
        {"type": "LineString", "coordinates": [[4, 0], [2, 2], [0, 0]]},
        {"type": "LineString", "coordinates": [[0, 2], [1, 1], [2, 2], [3, 1], [4, 2]]},
    ]
    topo = topojson.Topology(data)
    topo.to_json(topo_file)

    with open(topo_file) as f:
        topo_reloaded = json.load(f)
    assert topo_reloaded


def test_topology_to_json_pretty_and_null():
    data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "end_date": None,
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
                },
            }
        ],
    }
    data = geopandas.GeoDataFrame.from_features(data)
    topo = topojson.Topology(data).to_json(pretty=True)

    assert '"end_date": null' in topo


def test_topology_topoquantize():
    data = [
        {"type": "LineString", "coordinates": [[4, 0], [2, 2], [0, 0]]},
        {"type": "LineString", "coordinates": [[0, 2], [1, 1], [2, 2], [3, 1], [4, 2]]},
    ]
    tp = topojson.Topology(data, prequantize=1e4)
    topo = tp.topoquantize(1e4).to_dict()

    assert topo["transform"]["translate"] == [0.0, 0.0]
    assert topo["arcs"][0] == [[9999, 0], [-4999, 9999]]


def test_topology_fiona_gpkg_to_geojson():
    with fiona.open("tests/files_shapefile/rivers.gpkg", driver="Geopackage") as f:
        data = [f[24], f[25]]
    topo = topojson.Topology(data)
    gj = geojson.loads(topo.to_geojson())

    assert gj["type"] == "FeatureCollection"


def test_topology_fiona_shapefile_to_geojson():
    with fiona.open("tests/files_shapefile/southamerica.shp") as f:
        data = [f[0], f[1]]
    topo = topojson.Topology(data)
    gj = geojson.loads(topo.to_geojson())

    assert gj["type"] == "FeatureCollection"


def test_topology_topojson_winding_order():
    data = geometry.MultiLineString(
        [
            [[0, 0], [0.97, 0], [0.97, 1], [0, 1], [0, 0]],
            [[1.03, 0], [2, 0], [2, 1], [1.03, 1], [1.03, 0]],
        ]
    )
    topo = topojson.Topology(data, prequantize=False, winding_order="CW_CCW")
    gj = geojson.loads(topo.to_geojson())

    assert gj["type"] == "FeatureCollection"


def test_topology_geojson_winding_order():
    data = geopandas.GeoDataFrame(
        {
            "name": ["P1", "P2"],
            "geometry": [
                geometry.Polygon(
                    [(0, 0), (0, 3), (3, 3), (3, 0), (0, 0)],
                    [[(1, 1), (2, 1), (2, 2), (1, 2), (1, 1)]],
                ),
                geometry.Polygon([(1, 1), (1, 2), (2, 2), (2, 1), (1, 1)]),
            ],
        }
    )
    topo = topojson.Topology(data, prequantize=False)
    gj = topo.to_geojson()

    assert gj


def test_topology_geodataframe_valid():
    data = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
    topo = topojson.Topology(data)
    gdf = topo.toposimplify(10, prevent_oversimplify=False).to_gdf()

    assert gdf.shape[0] == 177


def test_topology_geojson_duplicates():

    p0 = wkt.loads("POLYGON ((0 0, 0 1, 1 1, 2 1, 2 0, 1 0, 0 0))")
    p1 = wkt.loads("POLYGON ((0 1, 0 2, 1 2, 1 1, 0 1))")
    p2 = wkt.loads("POLYGON ((1 0, 2 0, 2 -1, 1 -1, 1 0))")
    data = geopandas.GeoDataFrame(
        {"name": ["abc", "def", "ghi"], "geometry": [p0, p1, p2]}
    )
    topo = topojson.Topology(data, prequantize=False)
    p0_wkt = topo.to_gdf().geometry[0].wkt

    assert p0_wkt == "POLYGON ((0 1, 0 0, 1 0, 2 0, 2 1, 1 1, 0 1))"


# test for https://github.com/mattijn/topojson/issues/110
def test_topology_topoquantization_dups():
    gdf = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
    gdf = gdf[gdf.name.isin(["France", "Belgium", "Netherlands"])]
    topo = topojson.Topology(data=gdf, prequantize=False).toposimplify(4)
    topo = topo.topoquantize(50).to_dict()

    assert topo["arcs"][6] == [[44, 47], [0, 0]]


# parse topojson from file
def test_topology_topojson_from_file():
    with open("tests/files_topojson/naturalearth.topojson", "r") as f:
        data = json.load(f)

    topo = topojson.Topology(data).to_dict()

    assert len(topo["objects"]) == 1


# parse topojson file and plot with altair
def test_topology_topojson_to_alt():
    # load topojson file into dict
    with open("tests/files_topojson/naturalearth_lowres_africa.topojson", "r") as f:
        data = json.load(f)

    # parse topojson file using `object_name`
    topo = topojson.Topology(data, object_name="data")
    # apply toposimplify and serialize to altair
    chart = topo.toposimplify(1).to_alt()

    assert len(chart.__dict__.keys()) == 2


# Object of type int64 is not JSON serializable
def test_topology_topojson_to_alt_int64():
    # load topojson file into dict
    with open("tests/files_topojson/mesh2d.topojson", "r") as f:
        data = json.load(f)

    # parse topojson file using `object_name`
    topo = topojson.Topology(data, object_name="mesh2d_flowelem_bl")
    # apply toposimplify and serialize to altair
    chart = topo.toposimplify(1).to_alt()

    assert len(chart.__dict__.keys()) == 2


def test_topology_nested_list_properties():
    from geojson import Feature, Polygon, FeatureCollection

    feat_1 = Feature(
        geometry=Polygon([[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]),
        bbox=[-7.45337, 8.36618, -7.2835, 8.47532],
        properties={
            "name": "abc",
            "geo.neighbors": [
                "bi_ssu_2",
                "bi_ssu_3",
                "bi_ssu_5",
                "bi_ssu_9",
                "bi_ssu_11",
                "bi_ssu_12",
                "bi_ssu_13",
            ],
        },
    )
    feat_2 = Feature(
        geometry=Polygon([[[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]]),
        bbox=[-7.45337, 8.36618, -7.2835, 8.47532],
        properties={
            "name": "def",
            "geo.neighbors": [
                "bi_ssu_2",
                "bi_ssu_3",
                "bi_ssu_5",
                "bi_ssu_9",
                "bi_ssu_11",
                "bi_ssu_12",
                "bi_ssu_13",
            ],
        },
    )
    fc = FeatureCollection([feat_1, feat_2])
    topo = topojson.Topology(fc, prequantize=False).to_dict()

    assert len(topo) == 4


def test_topology_update_bbox_topoquantize_toposimplify():
    # load example data representing continental Africa
    data = topojson.utils.example_data_africa()
    # compute the topology
    topo = topojson.Topology(data)
    # apply simplification on the topology and render as SVG
    bbox = topo.topoquantize(10).to_dict()["bbox"]

    assert round(bbox[0], 1) == -17.6


def test_topology_bbox_no_delta_transform():
    data = {
        "foo": {"type": "LineString", "coordinates": [[0, 0], [1, 0], [2, 0]]},
        "bar": {"type": "LineString", "coordinates": [[0, 0], [1, 0], [2, 0]]},
    }
    topo_1 = topojson.Topology(data, object_name="topo_1").to_dict()
    topo_2 = topojson.Topology(topo_1, object_name="topo_1").to_dict()

    assert topo_1["bbox"] == topo_2["bbox"]


# test for https://github.com/mattijn/topojson/issues/140
def test_topology_toposimplify_on_topojson_data():
    # load topojson file into dict
    with open("tests/files_topojson/gm.topo.json", "r") as f:
        data = json.load(f)

    # read as topojson and as geojson
    topo_0 = topojson.Topology(data, object_name="gm_features")
    gdf_0 = topo_0.toposimplify(10).to_gdf()

    topo_1 = topojson.Topology(
        topo_0.to_geojson(), prequantize=False, object_name="out"
    )
    gdf_1 = topo_1.toposimplify(10).to_gdf()

    assert gdf_0.iloc[0].geometry.is_valid == gdf_1.iloc[0].geometry.is_valid


def test_topology_round_coordinates_geojson():
    # load example data representing continental Africa
    data = topojson.utils.example_data_africa()
    # compute the topology
    topo = topojson.Topology(data)
    # apply simplification on the topology and render as SVG
    gjson = topo.topoquantize(10).to_geojson(decimals=2)
    coord_0 = json.loads(gjson)["features"][0]["geometry"]["coordinates"][0][0]
    assert coord_0 == [35.85, -2.74]


def test_topology_topoquantize():
    # load example data representing continental Africa
    data = topojson.utils.example_data_africa()
    # compute the topology
    topo = topojson.Topology(data, topoquantize=9).to_dict()

    assert len(topo["arcs"]) == 149
