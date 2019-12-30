import json
from shapely import geometry
import geopandas
import geojson
import topojson
import pytest


# this test was added since geometries of only linestrings resulted in a topojson
# file that returns an empty geodataframe when reading
def test_linestrings_parsed_to_gdf():
    data = [
        {"type": "LineString", "coordinates": [[4, 0], [2, 2], [0, 0]]},
        {"type": "LineString", "coordinates": [[0, 2], [1, 1], [2, 2], [3, 1], [4, 2]]},
    ]
    topo = topojson.Topology(data).to_gdf()

    assert topo["geometry"][0].wkt != "GEOMETRYCOLLECTION EMPTY"
    assert topo["geometry"][0].type == "LineString"


# test winding order using TopoOptions object
def test_winding_order_TopoOptions():
    data = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
    data = data[(data.name == "South Africa")]
    topo = topojson.Topology(data, winding_order="CW_CCW").to_dict(options=True)

    assert len(topo["objects"]) == 1
    assert len(topo["options"]) == 8


# test winding order using kwarg variables
def test_winding_order_kwarg_vars():

    data = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
    data = data[(data.name == "South Africa")]
    topo = topojson.Topology(data, winding_order="CW_CCW").to_dict(options=True)

    assert len(topo["objects"]) == 1
    assert len(topo["options"]) == 8


def test_computing_topology():
    data = [
        {"type": "LineString", "coordinates": [[4, 0], [2, 2], [0, 0]]},
        {"type": "LineString", "coordinates": [[0, 2], [1, 1], [2, 2], [3, 1], [4, 2]]},
    ]
    no_topo = topojson.Topology(data, topology=False, prequantize=False).to_dict()
    topo = topojson.Topology(data, topology=True, prequantize=False).to_dict()

    assert len(topo["arcs"]) == 5
    assert len(no_topo["arcs"]) == 2


# test prequantization without computing topology
def test_prequantization():

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
def test_prequantization_including_delta_encoding():

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


def test_toposimplify_set_in_options():
    data = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
    data = data[(data.name == "Antarctica")]
    topo = topojson.Topology(
        data, prequantize=True, simplify_with="shapely", toposimplify=4
    ).to_dict()

    assert "transform" in topo.keys()


def test_toposimplify_as_chaining():
    data = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
    data = data[(data.name == "Antarctica")]
    topo = topojson.Topology(data, prequantize=True, simplify_with="shapely")
    topos = topo.toposimplify(2).to_dict()

    assert "transform" in topos.keys()


def test_topoquantize_as_chaining():
    data = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
    data = data[(data.name == "Antarctica")]
    topo = topojson.Topology(data, prequantize=False, simplify_with="shapely")
    topos = topo.topoquantize(1e2).to_dict()

    assert "transform" in topos.keys()


def test_prequantize_topoquantize_as_chaining():
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


def test_topology_point():
    data = [{"type": "Point", "coordinates": [0.5, 0.5]}]
    with pytest.raises(SystemExit) as topo:
        topojson.Topology(data, topoquantize=True).to_dict()

    assert topo.type == SystemExit
    assert topo.value.code == "Cannot quantize when xmax-xmin OR ymax-ymin equals 0"


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
