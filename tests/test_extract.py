import json
import unittest
from topojson.core.extract import Extract
from shapely import geometry
import geopandas
import geojson


class TestExtract(unittest.TestCase):
    # extract copies coordinates sequentially into a buffer
    def test_linestring(self):
        data = {
            "foo": {"type": "LineString", "coordinates": [[0, 0], [1, 0], [2, 0]]},
            "bar": {"type": "LineString", "coordinates": [[0, 0], [1, 0], [2, 0]]},
        }
        topo = Extract(data).to_dict()
        self.assertEqual(len(topo["linestrings"]), 2)

    # assess if a multipolygon with hole is processed into the right number of rings
    def test_multipolygon(self):
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
        self.assertEqual(len(topo["bookkeeping_geoms"]), 3)
        self.assertEqual(len(topo["linestrings"]), 4)

    # a LineString without coordinates is ke polygon geometry
    def test_empty_linestring(self):
        data = {"empty_ls": {"type": "LineString", "coordinates": None}}
        topo = Extract(data).to_dict()
        self.assertEqual(topo["objects"]["empty_ls"]["arcs"], None)

    # invalid polygon geometry
    def test_invalid_polygon(self):
        data = {
            "wrong": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [1, 0], [2, 0], [0, 0]]],
            },
            "valid": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [2, 0], [1, 1], [0, 0]]],
            },
        }
        topo = Extract(data).to_dict()
        self.assertEqual(len(topo["linestrings"]), 1)

    # test multiliinestring
    def test_multilinestring(self):
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
        self.assertEqual(len(topo["linestrings"]), 3)

    # test nested geojosn geometrycollection collection
    def test_nested_geometrycollection(self):
        data = {
            "foo": {
                "type": "GeometryCollection",
                "geometries": [
                    {
                        "type": "GeometryCollection",
                        "geometries": [
                            {
                                "type": "LineString",
                                "coordinates": [[0.1, 0.2], [0.3, 0.4]],
                            }
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
        self.assertEqual(
            len(topo["objects"]["foo"]["geometries"][0]["geometries"][0]["arcs"]), 1
        )

    # test geometry collection + polygon
    def test_geometrycollection_polygon(self):
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
        self.assertEqual(len(topo["linestrings"]), 2)

    # test feature type
    def test_features(self):
        data = {
            "foo": {
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": [[.1, .2], [.3, .4]]},
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
        self.assertEqual(len(topo["linestrings"]), 2)

    # test feature collection including geometry collection
    def test_featurecollection(self):
        data = {
            "collection": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [[.1, .2], [.3, .4]],
                        },
                    },
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "GeometryCollection",
                            "geometries": [
                                {
                                    "type": "Polygon",
                                    "coordinates": [
                                        [[0.5, 0.6], [0.7, 0.8], [0.9, 1.0]]
                                    ],
                                }
                            ],
                        },
                    },
                ],
            }
        }
        topo = Extract(data).to_dict()
        # print(topology)
        self.assertEqual(len(topo["objects"]), 2)
        self.assertEqual(len(topo["bookkeeping_geoms"]), 2)
        self.assertEqual(len(topo["linestrings"]), 2)
        self.assertEqual(
            topo["objects"]["feature_0"]["geometries"][0]["type"], "LineString"
        )
        self.assertEqual(
            topo["objects"]["feature_1"]["geometries"][0]["geometries"][0]["type"],
            "Polygon",
        )

    # test to parse feature collection from a geojson file through geojson library
    def test_geojson_feat_col_geom_col(self):
        with open("tests/files_geojson/feature_collection.geojson") as f:
            data = geojson.load(f)
        topo = Extract(data).to_dict()
        self.assertEqual(len(topo["objects"]), 1)
        self.assertEqual(len(topo["bookkeeping_geoms"]), 3)
        self.assertEqual(len(topo["linestrings"]), 3)

    # test to parse a feature from a geojson file through geojson library
    def test_geojson_feature_geom_col(self):
        with open("tests/files_geojson/feature.geojson") as f:
            data = geojson.load(f)
        topo = Extract(data).to_dict()
        self.assertEqual(len(topo["objects"]), 1)
        self.assertEqual(len(topo["bookkeeping_geoms"]), 3)
        self.assertEqual(len(topo["linestrings"]), 3)

    # test feature collection including geometry collection
    def test_geopandas_geoseries(self):
        data = geopandas.GeoSeries(
            [
                geometry.Polygon([(0, 0), (1, 0), (1, 1)]),
                geometry.Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
                geometry.Polygon([(2, 0), (3, 0), (3, 1), (2, 1)]),
            ]
        )
        topo = Extract(data).to_dict()
        self.assertEqual(len(topo["objects"]), 3)
        self.assertEqual(len(topo["bookkeeping_geoms"]), 3)
        self.assertEqual(len(topo["linestrings"]), 3)
        # TEST FAILS because of https://github.com/geopandas/geopandas/issues/1070

    # test shapely geometry collection.
    def test_shapely_geometrycollection(self):
        data = geometry.GeometryCollection(
            [
                geometry.Polygon([[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]),
                geometry.Polygon([[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]),
            ]
        )
        topo = Extract(data).to_dict()
        self.assertEqual(len(topo["objects"]), 1)
        self.assertEqual(len(topo["bookkeeping_geoms"]), 2)
        self.assertEqual(len(topo["linestrings"]), 2)

    def test_geo_interface_from_list(self):
        data = [
            {"type": "LineString", "coordinates": [[0, 0], [1, 0], [2, 0]]},
            {"type": "LineString", "coordinates": [[0, 0], [1, 0], [2, 0]]},
        ]
        topo = Extract(data).to_dict()
        self.assertEqual(len(topo["linestrings"]), 2)

    def test_shapely_geo_interface_from_list(self):
        data = [
            geometry.Polygon([[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]),
            geometry.Polygon([[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]),
        ]
        topo = Extract(data).to_dict()
        self.assertEqual(len(topo["linestrings"]), 2)
        self.assertEqual(isinstance(topo["objects"][0], dict), True)

    # duplicate rotated geometry bar with hole interior in geometry foo
    def test_extract_geomcol_multipolygon_polygon(self):
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
        self.assertEqual(len(topo["linestrings"]), 4)

    # def test_extract_geo_interface_shapefile(self):
    #     import shapefile

    #     data = shapefile.Reader("tests/files_shapefile/southamerica.shp")
    #     topo = Extract(data).to_dict()
    #     self.assertEqual(len(topo["linestrings"]), 4)

