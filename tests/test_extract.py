import json
from topojson.core.extract import Extract
from shapely import geometry
import geopandas
import geojson


# extract copies coordinates sequentially into a buffer
def test_linestring():
    data = {
        "foo": {"type": "LineString", "coordinates": [[0, 0], [1, 0], [2, 0]]},
        "bar": {"type": "LineString", "coordinates": [[0, 0], [1, 0], [2, 0]]},
    }
    topo = Extract(data).to_dict()

    assert len(topo["linestrings"]) == 2


# assess if a multipolygon with hole is processed into the right number of rings
def test_multipolygon():
    # multipolygon with hole
    data = {
        "foo": {
            "type": "MultiPolygon",
            "coordinates": [
                [
                    [[0, 0], [20, 0], [10, 20], [0, 0]],  # CCW
                    [[3, 2], [10, 16], [17, 2], [3, 2]],  # CW
                ],
                [[[6, 4], [14, 4], [10, 12], [6, 4]]],  # CCW
                [[[25, 5], [30, 10], [35, 5], [25, 5]]],
            ],
        }
    }
    topo = Extract(data).to_dict()

    assert len(topo["bookkeeping_geoms"]) == 3
    assert len(topo["linestrings"]) == 4


# a LineString without coordinates is an empty polygon geometry
def test_empty_linestring():
    data = {"empty_ls": {"type": "LineString", "coordinates": None}}
    topo = Extract(data).to_dict()

    assert topo["objects"]["empty_ls"]["arcs"] == None


# invalid polygon geometry
def test_invalid_polygon():
    data = {
        "wrong": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [2, 0], [0, 0]]]},
        "valid": {"type": "Polygon", "coordinates": [[[0, 0], [2, 0], [1, 1], [0, 0]]]},
    }
    topo = Extract(data).to_dict()

    assert len(topo["linestrings"]) == 1


# test multiliinestring
def test_multilinestring():
    data = {
        "foo": {
            "type": "MultiLineString",
            "coordinates": [
                [[0.0, 0.0], [1, 1], [3, 3]],
                [[1, 1], [0, 1]],
                [[3, 3], [4, 4], [0, 1]],
            ],
        }
    }
    topo = Extract(data).to_dict()

    assert len(topo["linestrings"]) == 3


# test nested geojosn geometrycollection collection
def test_nested_geometrycollection():
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
    topo = Extract(data).to_dict()

    assert len(topo["objects"]["foo"]["geometries"][0]["geometries"][0]["arcs"]) == 1


# test geometry collection + polygon
def test_geometrycollection_polygon():
    data = {
        "bar": {"type": "Polygon", "coordinates": [[[0, 0], [1, 1], [2, 0]]]},
        "foo": {
            "type": "GeometryCollection",
            "geometries": [
                {"type": "LineString", "coordinates": [[0.1, 0.2], [0.3, 0.4]]}
            ],
        },
    }
    topo = Extract(data).to_dict()

    assert len(topo["linestrings"]) == 2


# test feature type
def test_features():
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
    topo = Extract(data).to_dict()

    assert len(topo["linestrings"]) == 2


# test feature collection including geometry collection
def test_featurecollection():
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
    topo = Extract(data).to_dict()

    assert len(topo["objects"]) == 2
    assert len(topo["bookkeeping_geoms"]) == 2
    assert len(topo["linestrings"]) == 2
    assert topo["objects"]["feature_0"]["geometries"][0]["type"] == "LineString"
    assert (
        topo["objects"]["feature_1"]["geometries"][0]["geometries"][0]["type"]
        == "Polygon"
    )


# test to parse feature collection from a geojson file through geojson library
def test_geojson_feat_col_geom_col():
    with open("tests/files_geojson/feature_collection.geojson") as f:
        data = geojson.load(f)
    topo = Extract(data).to_dict()

    assert len(topo["objects"]) == 1
    assert len(topo["bookkeeping_geoms"]) == 3
    assert len(topo["linestrings"]) == 3


# test to parse a feature from a geojson file through geojson library
def test_geojson_feature_geom_col():
    with open("tests/files_geojson/feature.geojson") as f:
        data = geojson.load(f)
    topo = Extract(data).to_dict()

    assert len(topo["objects"]) == 1
    assert len(topo["bookkeeping_geoms"]) == 3
    assert len(topo["linestrings"]) == 3


# test feature collection including geometry collection
def test_geopandas_geoseries():
    data = geopandas.GeoSeries(
        [
            geometry.Polygon([(0, 0), (1, 0), (1, 1)]),
            geometry.Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
            geometry.Polygon([(2, 0), (3, 0), (3, 1), (2, 1)]),
        ]
    )
    topo = Extract(data).to_dict()

    assert len(topo["objects"]) == 3
    assert len(topo["bookkeeping_geoms"]) == 3
    assert len(topo["linestrings"]) == 3
    # TEST FAILS because of https://github.com/geopandas/geopandas/issues/1070


# test shapely geometry collection.
def test_shapely_geometrycollection():
    data = geometry.GeometryCollection(
        [
            geometry.Polygon([[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]),
            geometry.Polygon([[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]),
        ]
    )
    topo = Extract(data).to_dict()

    assert len(topo["objects"]) == 1
    assert len(topo["bookkeeping_geoms"]) == 2
    assert len(topo["linestrings"]) == 2


def test_geo_interface_from_list():
    data = [
        {"type": "LineString", "coordinates": [[0, 0], [1, 0], [2, 0]]},
        {"type": "LineString", "coordinates": [[0, 0], [1, 0], [2, 0]]},
    ]
    topo = Extract(data).to_dict()

    assert len(topo["linestrings"]) == 2


def test_shapely_geo_interface_from_list():
    data = [
        geometry.Polygon([[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]),
        geometry.Polygon([[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]),
    ]
    topo = Extract(data).to_dict()

    assert len(topo["linestrings"]) == 2
    assert isinstance(topo["objects"][0], dict)


# duplicate rotated geometry bar with hole interior in geometry foo
def test_extract_geomcol_multipolygon_polygon():
    data = {
        "foo": {
            "type": "GeometryCollection",
            "geometries": [
                {
                    "type": "MultiPolygon",
                    "coordinates": [
                        [
                            [[10, 20], [20, 0], [0, 0], [3, 13], [10, 20]],
                            [[3, 2], [10, 16], [17, 2], [3, 2]],
                        ],
                        [[[10, 4], [14, 4], [10, 12], [10, 4]]],
                    ],
                },
                {
                    "type": "Polygon",
                    "coordinates": [[[20, 0], [35, 5], [10, 20], [20, 0]]],
                },
            ],
        }
    }
    topo = Extract(data).to_dict()

    assert len(topo["linestrings"]) == 4


def test_extract_geo_interface_shapefile():
    import shapefile

    data = shapefile.Reader("tests/files_shapefile/southamerica.shp")
    topo = Extract(data).to_dict()

    assert len(topo["linestrings"]) == 15


def test_extract_points():
    data = [
        {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
        {"type": "Point", "coordinates": [0.5, 0.5]},
    ]
    topo = Extract(data).to_dict()

    assert len(topo["bookkeeping_coords"]) == 1
    assert len(topo["bookkeeping_geoms"]) == 1
    assert topo["coordinates"][0].wkt == "POINT (0.5 0.5)"
    assert "coordinates" in topo["objects"][1].keys()

