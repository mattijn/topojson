import unittest
import topojson    

class TestCut(unittest.TestCase): 
    # overlapping rings ABCDA and BEFCB are cut into BC-CDAB and BEFC-CB
    def test_overlapping_rings_are_cut(self): 
        data = {
            "abcda": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]}, # rotated to BCDAB, cut BC-CDAB
            "befcb": {"type": "Polygon", "coordinates": [[[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]]},
        }        
        topo = topojson.cut(topojson.join(topojson.extract(data)))
        # print(topo)
        self.assertEqual(topo['bookkeeping_linestrings'].size, 6)
        self.assertSequenceEqual(topo['duplicates'].tolist(), [[4, 1]])

       
