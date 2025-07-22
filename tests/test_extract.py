import json
import pytest
from topojson.core.extract import Extract
from shapely import geometry
import geopandas
import geojson
from geojson import Feature, Polygon, FeatureCollection
import fiona


# extract copies coordinates sequentially into a buffer
def test_extract_linestring():
    data = {
        "foo": {"type": "LineString", "coordinates": [[0, 0], [1, 0], [2, 0]]},
        "bar": {"type": "LineString", "coordinates": [[0, 0], [1, 0], [2, 0]]},
    }
    topo = Extract(data).to_dict()

    assert len(topo["linestrings"]) == 2


# assess if a multipolygon with hole is processed into the right number of rings
def test_extract_multipolygon():
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
def test_extract_empty_linestring():
    data = {"empty_ls": {"type": "LineString", "coordinates": None}}
    topo = Extract(data).to_dict()

    assert topo["objects"]["empty_ls"]["arcs"] == None


# invalid polygon geometry
def test_extract_invalid_polygon():
    data = {
        "wrong": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [2, 0], [0, 0]]]},
        "valid": {"type": "Polygon", "coordinates": [[[0, 0], [2, 0], [1, 1], [0, 0]]]},
    }
    topo = Extract(data).to_dict()

    assert len(topo["linestrings"]) == 1


# test multilinestring
def test_extract_multilinestring():
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


# test nested geojson geometrycollection collection
def test_extract_nested_geometrycollection():
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
def test_extract_geometrycollection_polygon():
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
def test_extract_features():
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
def test_extract_featurecollection():
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
    assert topo["objects"]["feature_0"]["type"] == "LineString"
    assert topo["objects"]["feature_1"]["geometries"][0]["type"] == "Polygon"


# test to parse feature collection from a geojson file through geojson library
def test_extract_geojson_feat_col_geom_col():
    with open("tests/files_geojson/feature_collection.geojson") as f:
        data = geojson.load(f)
    topo = Extract(data).to_dict()

    assert len(topo["objects"]) == 1
    assert len(topo["bookkeeping_geoms"]) == 3
    assert len(topo["linestrings"]) == 3


# test to parse a feature from a geojson file through geojson library
def test_extract_geojson_feature_geom_col():
    with open("tests/files_geojson/feature.geojson") as f:
        data = geojson.load(f)
    topo = Extract(data).to_dict()

    assert len(topo["objects"]) == 1
    assert len(topo["bookkeeping_geoms"]) == 3
    assert len(topo["linestrings"]) == 3


# test feature collection including geometry collection
def test_extract_geopandas_geoseries():
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


# test shapely geometry collection.
def test_extract_shapely_geometrycollection():
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


def test_extract_geo_interface_from_list():
    data = [
        {"type": "LineString", "coordinates": [[0, 0], [1, 0], [2, 0]]},
        {"type": "LineString", "coordinates": [[0, 0], [1, 0], [2, 0]]},
    ]
    topo = Extract(data).to_dict()

    assert len(topo["linestrings"]) == 2


def test_extract_shapely_geo_interface_from_list():
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
    assert topo["coordinates"][0].tolist() == [[0.5, 0.5]]
    assert "coordinates" in topo["objects"][1].keys()


def test_extract_single_polygon():
    data = geometry.Polygon([[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]])
    topo = Extract(data).to_dict()

    assert len(topo["bookkeeping_geoms"]) == 1


def test_extract_single_linestring():
    data = geometry.LineString([[0, 0], [1, 0], [1, 1], [0, 1]])
    topo = Extract(data).to_dict()

    assert len(topo["bookkeeping_geoms"]) == 1


def test_extract_single_multilinestring():
    data = geometry.MultiLineString([[[0, 0], [1, 1]], [[-1, 0], [1, 0]]])
    topo = Extract(data).to_dict()

    assert len(topo["bookkeeping_geoms"]) == 2


def test_extract_single_multilinestring_list():
    data = [geometry.MultiLineString([[[0, 0], [1, 1]], [[-1, 0], [1, 0]]])]
    topo = Extract(data).to_dict()

    assert len(topo["bookkeeping_geoms"]) == 2


def test_extract_geopandas_geodataframe():
    data = geopandas.read_file(
        "tests/files_geojson/naturalearth_alb_grc.geojson"
    )
    topo = Extract(data).to_dict()

    assert len(topo["bookkeeping_geoms"]) == 3


# dict should have a valued key:geom_object. Otherwise key:value is removed
def test_extract_invalid_dict_item():
    data = {
        "type": "MultiPolygon",
        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
    }
    topo = Extract(data).to_dict()

    assert len(topo["bookkeeping_geoms"]) == 0


def test_extract_fiona_file():
    with fiona.open("tests/files_shapefile/southamerica.shp") as data:
        topo = Extract(data).to_dict()

    assert len(topo["bookkeeping_geoms"]) == 15


def test_extract_fiona_file_gpkg():
    with fiona.open("tests/files_shapefile/rivers.gpkg") as col:
        feats = []
        for idx, feat in enumerate(col):
            if idx in [24, 25]:
                feats.append(feat)

    topo = Extract(feats).to_dict()

    assert len(topo["bookkeeping_geoms"]) == 4


# test to check if original data is not modified
def test_extract_dict_org_data_untouched():
    data = {
        "foo": {"type": "LineString", "coordinates": [[0, 0], [1, 0], [2, 0]]},
        "bar": {"type": "LineString", "coordinates": [[0, 0], [1, 0], [2, 0]]},
    }
    topo = Extract(data).to_dict()
    topo_foo = topo["objects"]["foo"]
    data_foo = data["foo"]

    assert "arcs" in topo_foo.keys()
    assert "arcs" not in data_foo.keys()


# test to check if original data is not modified
def test_extract_list_org_data_untouched():
    data = [
        geometry.Polygon([[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]),
        geometry.Polygon([[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]),
    ]
    topo = Extract(data).to_dict()
    topo_0 = topo["objects"][0]
    data_0 = data[0]

    assert "arcs" in topo_0.keys()
    assert data_0.geom_type == "Polygon"


# test to check if original data is not modified
def test_extract_gdf_org_data_untouched():
    data = geopandas.read_file(
        "tests/files_geojson/naturalearth_alb_grc.geojson"
    )
    topo = Extract(data).to_dict()
    topo_0 = topo["objects"][0]
    data_0 = data.iloc[0]

    assert "arcs" in topo_0.keys()
    assert data_0.geometry.geom_type == "Polygon"


# test to check if original data is not modified
def test_extract_shapely_org_data_untouched():
    data = geometry.LineString([[0, 0], [1, 0], [1, 1], [0, 1]])
    topo = Extract(data).to_dict()
    topo_0 = topo["objects"][0]

    assert "arcs" in topo_0.keys()
    assert data.geom_type == "LineString"


# test to check if original data is not modified
def test_extract_shapefile_org_data_untouched():
    import shapefile

    data = shapefile.Reader("tests/files_shapefile/southamerica.shp")
    topo = Extract(data).to_dict()
    topo_0 = topo["objects"]["feature_00"]
    data_0 = data.__geo_interface__["features"][0]["geometry"]

    assert "arcs" in topo_0.keys()
    assert "arcs" not in data_0.keys()


# issue 137 do not modify source data
def test_extract_source_data_modify():
    # prepare data
    feat_1 = Feature(
        geometry=Polygon([[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]),
        properties={"name": "abc"},
    )
    feat_2 = Feature(
        geometry=Polygon([[[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]]),
        properties={"name": "def"},
    )
    data = FeatureCollection([feat_1, feat_2])

    # before Topology()
    assert "geometry" in data["features"][0].keys()

    # apply Topology()
    topo = Extract(data)

    # after Topology()
    assert "geometry" in data["features"][0].keys()


# issue 151 properties are not kept in geojson data
def test_extract_keep_properties():
    # prepare data
    feat_1 = Feature(
        geometry=Polygon([[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]),
        properties={"name": "abc"},
    )
    feat_2 = Feature(
        geometry=Polygon([[[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]]),
        properties={"name": {"def": "ghi"}},
    )
    data = FeatureCollection([feat_1, feat_2])
    topo = Extract(data).to_dict()

    assert topo["objects"]["feature_0"]["properties"]["name"] == "abc"
    assert topo["objects"]["feature_1"]["properties"]["name"]["def"] == "ghi"


def test_extract_geojson_keep_index():
    feat_1 = Feature(
        id="custom_index",
        geometry=Polygon([[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]),
    )
    feat_2 = Feature(
        geometry=Polygon([[[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]]),
    )
    data = FeatureCollection([feat_1, feat_2])
    topo = Extract(data).to_dict()
    objects = topo["objects"]

    assert bool(objects.get("custom_index")) == True
    assert bool(objects.get("feature_1")) == True


def test_extract_geojson_keep_index_duplicates():
    feat_1 = Feature(
        id="duplicate_id",
        geometry=Polygon([[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]),
    )
    feat_2 = Feature(
        id="duplicate_id",
        geometry=Polygon([[[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]]),
    )
    data = FeatureCollection([feat_1,feat_2])
    with pytest.raises(IndexError):
        Extract(data)
        

# why cannot load geojson file using json module?
def test_extract_read_geojson_from_json_dict():
    with open("tests/files_geojson/naturalearth_lowres.geojson") as f:
        data = json.load(f)
    topo = Extract(data).to_dict()

    assert len(topo["linestrings"]) == 287


def test_extract_read_multiple_gdf_object_name():
    world = geopandas.read_file("tests/files_shapefile/static_natural_earth.gpkg")
    world = world[["CONTINENT", "geometry", "POP_EST"]]
    continents_sum = world.dissolve(by="CONTINENT", aggfunc="sum")
    continents_mean = world.dissolve(by="CONTINENT", aggfunc="mean")

    topo = Extract(
        data=[world, continents_sum, continents_mean],
        options={"object_name": ["world", "continents_sum", "continents_mean"]},
    ).to_dict()

    assert len(topo["objects"]) == (
        len(world) + len(continents_sum) + len(continents_mean)
    )


def test_extract_read_multiple_gjson_object_name():
    with open("tests/files_geojson/geojson_1.json", "r") as gj_1:
        geojson_1 = json.load(gj_1)

    with open("tests/files_geojson/geojson_2.json", "r") as gj_2:
        geojson_2 = json.load(gj_2)

    topo = Extract(
        data=[geojson_1, geojson_2], options={"object_name": ["gjson_1", "gjson_2"]}
    ).to_dict()

    assert len(topo["objects"]) == (
        len(geojson_1["features"]) + len(geojson_2["features"])
    )
