import json
import unittest
import topojson    

class TestJoin(unittest.TestCase): 
    # the returned hashmap has true for junction points
    def test_true_for_junction_points(self): 
        data = {
            "cba": {"type": "LineString", "coordinates": [[2, 0], [1, 0], [0, 0]]},
            "ab": {"type": "LineString", "coordinates": [[0, 0], [1, 0]]}
        }        
        topo = topojson.join(topojson.extract(data))
        # print(topo)
        self.assertTrue((1.0, 0.0) in set(topo['junctions']))

    # the returned hashmap has undefined for non-junction points
    def test_undefined_for_non_junction_points(self):
        data = {
            "cba": {"type": "LineString", "coordinates": [[2, 0], [1, 0], [0, 0]]},
            "ab": {"type": "LineString", "coordinates": [[0, 0], [2, 0]]}
        }        
        topo = topojson.join(topojson.extract(data))
        # print(topo)
        self.assertFalse((1.0, 0.0) in set(topo['junctions']))

    # exact duplicate lines ABC & ABC have junctions at their end points   
    def test_duplicate_lines_junction_endpoints(self):
        data = {
            "abc1": {"type": "LineString", "coordinates": [[0, 0], [1, 0], [2, 0]]},
            "abc2": {"type": "LineString", "coordinates": [[0, 0], [1, 0], [2, 0]]}
        }        
        topo = topojson.join(topojson.extract(data))
        # print(topo)
        self.assertListEqual(topo['junctions'], [(0, 0), (2, 0)])
  
      # reversed duplicate lines ABC & CBA have junctions at their end points   
    def test_reversed_duplicate_lines_junction_endpoints(self):
        data = {
            "abc": {"type": "LineString", "coordinates": [[0, 0], [1, 0], [2, 0]]},
            "cba": {"type": "LineString", "coordinates": [[2, 0], [1, 0], [0, 0]]}
        }        
        topo = topojson.join(topojson.extract(data))
        # print(topo)
        self.assertListEqual(topo['junctions'], [(0, 0), (2, 0)])

    # exact duplicate rings ABCA & ABCA have no junctions
    def test_exact_duplicate_rings_no_endpoints(self):
        data = {
            "abca1": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [2, 0], [0, 0]]]},
            "abca2": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [2, 0], [0, 0]]]}
        }
        topo = topojson.join(topojson.extract(data))
        # assertion is wrong, test should fail as polygon junctions are not solved yet
        self.assertListEqual(topo['junctions'], [1])