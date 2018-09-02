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
        try:
            forward, backward = shared_paths(g1, g2) 
            
            # if both backward and forward cotains objects combine 
            if backward.is_empty:
                shared_segments = forward
            elif forward.is_empty:    
                shared_segments = backward       
            else:
                # print('both full')  
                shared_segments = geometry.MultiLineString([
                    linemerge(forward),
                    linemerge(backward)
                ])

            self.segments.extend(list(shared_segments))
                
        except ValueError:
            # print('backward.is_empty and forward.is_empty')
            pass
            
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
        
        # first create list with all combinations of lines
        line_combs = list(itertools.combinations(data['lines'], 2))
        
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
