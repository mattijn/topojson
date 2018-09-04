# pylint: disable=unsubscriptable-object
from shapely import geometry
from shapely.ops import shared_paths
from shapely.ops import linemerge
import itertools

class _Join:
    """
    identify junctions (intersection points).
    """

    def __init__(self):
        # initatie topology items
        self.junctions = []
        self.segments = []

    def junctions_two_lines(self, g1, g2):
        fw_bw = shared_paths(g1, g2) 
        if not fw_bw.is_empty:
            
            forward = fw_bw[0]
            backward = fw_bw[1]

            if backward.is_empty:
                # only contains forward objects
                shared_segments = forward
            elif forward.is_empty:    
                # only contains backward objects
                shared_segments = backward       
            else:
                # both backward and forward contains objects combine 
                shared_segments = geometry.MultiLineString([
                    linemerge(forward),
                    linemerge(backward)
                ])

            self.segments.extend(list(shared_segments))
            
    def main(self, data):
        """
        start join function
        
        to find shared paths:
        https://shapely.readthedocs.io/en/stable/manual.html#shared-paths
        
        to set up a R-tree:
        https://shapely.readthedocs.io/en/stable/manual.html#str-packed-r-tree
        
        get cartesian product:
        https://stackoverflow.com/a/34032549
        """
        
        # start of join from Polygon derived linearRings and LineStrings
        
#         # pop last coordinate        
#         linearrings = [
#             geometry.LineString(ring.boundary.coords[0:-1]) for ring in data['rings']
#         ]
        linearrings = [ring.boundary for ring in data['rings']]
        mergerings = linearrings + data['lines']
        
        # first create list with all combinations of lines
        line_combs = list(itertools.combinations(mergerings, 2))
        
        # iterate over line combinations
        for geoms in line_combs:
            self.junctions_two_lines(geoms[0], geoms[1])

        # self.segments is a list of LineStrings, get all coordinates
        s_coords = [y for x in self.segments for y in list(x.coords)]
 
        # only keep junctions that appear only once
        # coordinates that appear multiple times are not junctions         
        self.junctions = [i for i in s_coords if s_coords.count(i) is 1]
        data['junctions'] = self.junctions
        
        return data
    
    
def _joiner(data):
    Join = _Join()
    j = Join.main(data)
    return j
