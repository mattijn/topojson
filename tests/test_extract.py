import json
import unittest
import topojson as tj

class TestExtract(unittest.TestCase):

    # def setUp(self):
    #     with open("tests/data_geojson/polygon-featurecollection-feature-clockwise.json") as f:
    #         self.polygon_featurecollection_feature_clockwise = json.load(f)

    # extract copies coordinates sequentially into a buffer
    def test_linestring(self):
        data = {
            "foo": {"type": "LineString", "coordinates": [[0, 0], [1, 0], [2, 0]]},
            "bar": {"type": "LineString", "coordinates": [[0, 0], [1, 0], [2, 0]]}
        }
        topology = tj.extract(data)
        self.assertEqual(topology['coordinates'], [(0, 0), (1, 0), (2, 0), (0, 0), (1, 0), (2, 0)])

    # assess if a multipolygon is processed into the right number of rings
    def test_multipolygon(self):
        data = {
            "foo": {
                "type": "MultiPolygon",
                "coordinates": [
                    [
                        [
                        [0.125, 0.0625],
                        [0.5, 0.0625],
                        [0.5, 0.25],
                        [0.125, 0.25],
                        [0.125, 0.0625]
                        ]
                    ],
                    [[[0.125, 0.0625], [0.125, 0.0625], [0.125, 0.0625], [0.125, 0.0625]]],
                    [
                        [
                        [0.125, 0.0625],
                        [0.125, 0.25],
                        [0.5, 0.25],
                        [0.5, 0.0625],
                        [0.125, 0.0625]
                        ]
                    ]
                ]
            }
        }
        topology = tj.extract(data)
        self.assertEqual(len(topology['rings']), 3)  

    # test multiliinestring
    def test_multilinestring(self):
        data = {
            "foo": {
                "type": "MultiLineString",
                "coordinates": [
                [[0.125, 0.0625], [0.5, 0.25]],
                [[0.125, 0.0625], [0.125, 0.0625]],
                [[0.5, 0.25], [0.125, 0.0625]]
                ]
            }
        }  
        topology = tj.extract(data)
        self.assertEqual(len(topology['lines']), 3)             