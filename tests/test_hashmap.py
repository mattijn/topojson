import geopandas
import fiona
from shapely import geometry
from topojson.core.hashmap import Hashmap
import pytest


# duplicate rotated geometry bar with hole interior in geometry foo
def test_hashmap_geomcol_multipolygon_polygon():
    data = {
        "foo": {
            "type": "GeometryCollection",
            "geometries": [
                {
                    "type": "MultiPolygon",
                    "coordinates": [
                        [
                            [[10, 20], [20, 0], [0, 0], [10, 20]],
                            [[3, 2], [10, 16], [17, 2], [3, 2]],
                        ],
                        [[[6, 4], [14, 4], [10, 12], [6, 4]]],
                    ],
                },
                {
                    "type": "Polygon",
                    "coordinates": [[[20, 0], [35, 5], [10, 20], [20, 0]]],
                },
            ],
        }
    }
    topo = Hashmap(data).to_dict()

    assert topo["objects"]["data"]["geometries"][0]["geometries"][0]["arcs"] == [
        [[4, 0], [1]],
        [[2]],
    ]


def test_hashmap_backward_polygon():
    data = {
        "abc": {
            "type": "Polygon",
            "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
        },
        "def": {
            "type": "Polygon",
            "coordinates": [[[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]],
        },
    }
    topo = Hashmap(data).to_dict()

    assert topo["objects"]["data"]["geometries"][0]["arcs"] == [[-3, 0]]
    assert topo["objects"]["data"]["geometries"][1]["arcs"] == [[1, 2]]


# this test should catch a shared boundary and a hashed multipolygon
# related to https://github.com/Toblerity/Shapely/issues/535
def test_hashmap_albania_greece():
    data = geopandas.read_file("tests/files_shapefile/static_natural_earth.gpkg")
    data = data[(data.ADMIN == "Albania") | (data.ADMIN == "Greece")]
    topo = Hashmap(data).to_dict()

    assert len(topo["linestrings"]) == 4


# something is wrong with hashmapping in the example of benin
def test_hashmap_benin_surrounding_countries():
    data = geopandas.read_file("tests/files_shapefile/static_natural_earth.gpkg")
    data = data[
        (data.ADMIN == "Togo")
        | (data.ADMIN == "Benin")
        | (data.ADMIN == "Burkina Faso")
    ]
    topo = Hashmap(data).to_dict()

    assert len(topo["linestrings"]) == 6


# something is wrong with hashmapping once a geometry has only shared arcs
def test_hashmap_geom_surrounding_many_geometries():
    data = geopandas.read_file("tests/files_shapefile/static_natural_earth.gpkg")
    data = data[
        (data.ADMIN == "Botswana")
        | (data.ADMIN == "South Africa")
        | (data.ADMIN == "Zimbabwe")
        | (data.ADMIN == "Namibia")
        | (data.ADMIN == "Zambia")
    ]
    topo = Hashmap(data).to_dict()

    assert len(topo["linestrings"]) == 13


# this test was added since the shared_arcs bookkeeping is doing well, but the
# wrong arc got deleted. How come?
def test_hashmap_shared_arcs_ordering_issues():
    data = geopandas.read_file("tests/files_shapefile/static_natural_earth.gpkg")
    data = data[
        (data.ADMIN == "Botswana")
        | (data.ADMIN == "South Africa")
        | (data.ADMIN == "Zimbabwe")
        | (data.ADMIN == "Mozambique")
        | (data.ADMIN == "Zambia")
    ]
    topo = Hashmap(data).to_dict()
    assert len(topo["linestrings"]) == 16


def test_hashmap_super_function():
    data = geometry.GeometryCollection(
        [
            geometry.Polygon([[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]),
            geometry.Polygon([[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]),
        ]
    )
    topo = Hashmap(data).to_dict()
    geoms = topo["objects"]["data"]["geometries"][0]["geometries"]

    assert len(list(topo.keys())) == 6
    assert geoms[0]["arcs"] == [[-3, 0]]
    assert geoms[1]["arcs"] == [[1, 2]]


# this test was added since objects with nested geometry-collections seems not
# being parsed in the topojson format.
# Pass for now:
def test_hashmap_of_nested_geometrycollection():
    data = {
        "foo": {
            "type": "GeometryCollection",
            "geometries": [
                {
                    "type": "GeometryCollection",
                    "geometries": [
                        {"type": "LineString", "coordinates": [[0.1, 0.2], [0.3, 0.4]]}
                    ],
                },
                {
                    "type": "Polygon",
                    "coordinates": [[[0.5, 0.6], [0.7, 0.8], [0.9, 1.0]]],
                },
            ],
        }
    }
    topo = Hashmap(data).to_dict()

    assert topo["objects"]["data"]["type"] == "GeometryCollection"


# this test was added because the winding order is still giving issues.
# see related issue: https://github.com/mattijn/topojson/issues/30
def test_hashmap_winding_order_geom_solely_shared_arcs():
    data = geopandas.read_file("tests/files_shapefile/static_natural_earth.gpkg")
    data = data[
        (data.ADMIN == "Jordan")
        | (data.ADMIN == "Palestine")
        | (data.ADMIN == "Israel")
    ]
    topo = Hashmap(data).to_dict()

    assert topo["objects"]["data"]["geometries"][1]["arcs"] == [[1, -6]]


def test_hashmap_point():
    data = [{"type": "Point", "coordinates": [0.5, 0.5]}]
    topo = Hashmap(data).to_dict()

    assert topo["bbox"] == (0.5, 0.5, 0.5, 0.5)
    assert len(topo["coordinates"]) == 1


def test_hashmap_polygon_point():
    data = [
        {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
        {"type": "Point", "coordinates": [0.5, 0.5]},
    ]
    topo = Hashmap(data).to_dict()

    assert len(topo["coordinates"]) == 1
    assert len(topo["linestrings"]) == 1


def test_hashmap_multipoint():
    data = [{"type": "MultiPoint", "coordinates": [[0.5, 0.5], [1.0, 1.0]]}]
    topo = Hashmap(data).to_dict()

    assert len(topo["coordinates"]) == 2


def test_hashmap_polygon():
    data = [
        {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]}
    ]
    topo = Hashmap(data).to_dict()

    assert len(topo["linestrings"]) == 1


def test_hashmap_point_multipoint():
    data = [
        {"type": "Point", "coordinates": [0.5, 0.5]},
        {"type": "MultiPoint", "coordinates": [[0.5, 0.5], [1.0, 1.0]]},
        {"type": "Point", "coordinates": [2.5, 3.5]},
    ]
    topo = Hashmap(data).to_dict()

    assert len(topo["coordinates"]) == 4


def test_hashmap_nested_geometrycollection():
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
                            }
                        ],
                    },
                },
            ],
        }
    }
    topo = Hashmap(data).to_dict()

    assert len(topo["linestrings"]) == 2


def test_hashmap_polygon_geometrycollection():
    data = {
        "bar": {"type": "Polygon", "coordinates": [[[0, 0], [1, 1], [2, 0]]]},
        "foo": {
            "type": "GeometryCollection",
            "geometries": [
                {"type": "LineString", "coordinates": [[0.1, 0.2], [0.3, 0.4]]}
            ],
        },
    }
    topo = Hashmap(data).to_dict()

    assert len(topo["linestrings"]) == 2


def test_hashmap_linestring_polygon():
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
    topo = Hashmap(data).to_dict()

    assert len(topo["linestrings"]) == 2


def test_hashmap_fiona_gpkg_to_dict():
    with fiona.open("tests/files_shapefile/rivers.gpkg", driver="Geopackage") as f:
        data = [f[24], f[25]]
    topo = Hashmap(data)
    topo = topo.to_dict()

    assert len(topo["linestrings"]) == 4


# issue #148 and issue #167
def test_hashmap_serializing_holes():
    mp = geometry.shape(
        {
            "type": "MultiPolygon",
            "coordinates": [
                [
                    [[0, 0], [20, 0], [10, 20], [0, 0]],  # CCW
                    [[8, 2], [12, 12], [17, 2], [8, 2]],  # CW
                    [[3, 2], [5, 6], [7, 2], [3, 2]],  # CW
                ],
                [[[10, 3], [15, 3], [12, 9], [10, 3]]],  # CCW
            ],
        }
    )
    topo = Hashmap(mp)
    topo = topo.to_dict()

    arc = topo["objects"]["data"]["geometries"][0]["arcs"]
    assert arc == [[[0], [1], [2]], [[3]]]


def test_hashmap_read_multiple_gdf_object_name():
    world = geopandas.read_file("tests/files_shapefile/static_natural_earth.gpkg")
    world = world[["CONTINENT", "geometry", "POP_EST"]]
    continents = world.dissolve(by="CONTINENT", aggfunc="sum")

    topo = Hashmap(
        data=[world, continents], options={"object_name": ["world", "continents"]}
    ).to_dict()

    assert len(topo["objects"]) == 2
