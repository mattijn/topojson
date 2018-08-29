import json
import unittest
import topojson as tj

class TestExtract(unittest.TestCase):
    # extract copies coordinates sequentially into a buffer
    def test_linestring(self):        
        topology = None
        data = {
            "foo": {"type": "LineString", "coordinates": [[0, 0], [1, 0], [2, 0]]},
            "bar": {"type": "LineString", "coordinates": [[0, 0], [1, 0], [2, 0]]}
        }
        topology = tj.extract(data)
        # print(topology)
        self.assertEqual(topology['coordinates'], [(0, 0), (1, 0), (2, 0), (0, 0), (1, 0), (2, 0)])

    # assess if a multipolygon is processed into the right number of rings
    def test_multipolygon(self):
        topology = None
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
        # print(topology)
        self.assertEqual(len(topology['rings']), 3)  

    # test multiliinestring
    def test_multilinestring(self):
        topology = None
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
        # print(topology)
        self.assertEqual(len(topology['lines']), 3)  

    # test nested geojosn geometrycollection collection
    def test_nested_geometrycollection(self):
        topology = None
        data =  {
            "foo": {
                "type": "GeometryCollection",
                "geometries": [
                {
                    "type": "GeometryCollection",
                    "geometries": [
                    {"type": "LineString", "coordinates": [[0.1, 0.2], [0.3, 0.4]]}
                    ]
                },
                {"type": "Polygon", "coordinates": [[[0.5, 0.6], [0.7, 0.8], [0.9, 1.0]]]}
                ]
            }
        }
        topology = tj.extract(data)
        # print(topology)
        self.assertEqual(len(topology['objects']['foo']['geometries'][0]['geometries'][0]['arcs']), 1)         

    # test geometry collection + polygon
    def test_geometrycollection_polygon(self):
        topology = None
        data = {
            "bar": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [1, 1], [2, 0]]]
            },    
            "foo": {
                "type": "GeometryCollection",
                "geometries": [
                {"type": "LineString", "coordinates": [[0.1, 0.2], [0.3, 0.4]]}
                ]
            }
        }
        topology = tj.extract(data)
        # print(topology)
        self.assertEqual(len(topology['rings']), 1)  

    # test feature type
    def test_features(self):
        topology = None
        data = {
            "foo": {
                "type": "Feature", 
                "geometry": {"type": "LineString", "coordinates": [[.1, .2], [.3, .4]]}
            },
            "bar": {
                "type": "Feature", 
                "geometry": {"type": "Polygon", "coordinates": [[[0.5, 0.6], [0.7, 0.8], [0.9, 1.0]]]}
            }
        } 
             
        topology = tj.extract(data)
        # print(topology)  
        self.assertEqual(len(topology['rings']), 1)    

    # test feature collection including geometry collection
    def test_featurecollection(self):
        topology = None
        data = {
            "collection": {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature", "geometry": {"type": "LineString", "coordinates": [[.1, .2], [.3, .4]]}},
                {"type": "Feature", "geometry": {"type": "GeometryCollection", "geometries": [
                    {"type": "Polygon", "coordinates": [[[0.5, 0.6], [0.7, 0.8], [0.9, 1.0]]]}]}
                }
            ]            
            }
        }
        topology = tj.extract(data)
        # print(topology)  
        self.assertEqual(len(topology['objects']), 2)
        self.assertEqual(topology['coordinates'], [(0.1, 0.2), (0.3, 0.4), (0.5, 0.6), (0.7, 0.8), (0.9, 1.0), (0.5, 0.6)])
        self.assertEqual(len(topology['rings']), 1)
        self.assertEqual(len(topology['lines']), 1)
        self.assertEqual(topology['objects']['feature_0']['geometries'][0]['type'], 'LineString')
        self.assertEqual(topology['objects']['feature_1']['geometries'][0]['geometries'][0]['type'], 'Polygon')