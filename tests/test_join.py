import json
import unittest
import topojson    

class TestJoin(unittest.TestCase):
    # the function setUp() is a method called to prepare the test fixture
    # this means that the function is executed prior each test
    # it is important to initiate the object(s) prior each test
    # otherwise test output will stack to the object(s) if multiple tests are run.
    def setUp(self):
        joinClass = topojson.Join()        
        extractClass = topojson.Extract()
        self.join = joinClass.join
        self.extract = extractClass.extract     

    # the returned hashmap has true for junction points
    def test_true_for_junction_points(self): 
        data = {
            "cba": {"type": "LineString", "coordinates": [[2, 0], [1, 0], [0, 0]]},
            "ab": {"type": "LineString", "coordinates": [[0, 0], [1, 0]]}
        }        
        topo = self.join(self.extract(data))
        print(topo)
        self.assertTrue((2.0, 0.0) in set(topo['junctions']))

    # the returned hashmap has undefined for non-junction points
    def test_undefined_for_non_junction_points(self):
        data = {
            "cba": {"type": "LineString", "coordinates": [[2, 0], [1, 0], [0, 0]]},
            "ab": {"type": "LineString", "coordinates": [[0, 0], [2, 0]]}
        }        
        topo = self.join(self.extract(data))
        print(topo)
        self.assertFalse((1.0, 0.0) in set(topo['junctions']))

    # exact duplicate lines ABC & ABC have junctions at their end points   
    def test_duplicate_lines_junction_endpoints(self):
        data = {
            "abc1": {"type": "LineString", "coordinates": [[0, 0], [1, 0], [2, 0]]},
            "abc2": {"type": "LineString", "coordinates": [[0, 0], [1, 0], [2, 0]]}
        }        
        topo = self.join(self.extract(data))
        print(topo)
        self.assertListEqual(topo['junctions'], [(0, 0), (2, 0)])
  