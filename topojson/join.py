from .extract import Extract
from shapely import geometry
from shapely.ops import shared_paths
from shapely.ops import linemerge

class Join:
    """
    identify junctions (intersection points).
    """

    def __init__(self):
        # initatie topology items
        self.junctions = []

    def junctions_two_lines(self, g1, g2):
        forward, backward = shared_paths(g1, g2)    
        
        if backward.is_empty and forward.is_empty:
            print('both empty')
            
        elif backward.is_empty:
            shared_segments = forward
        elif forward.is_empty:    
            shared_segments = backward       
        else:
            print('both full')  
            shared_segments = geometry.MultiLineString([linemerge(forward),linemerge(backward)])

        for segment in shared_segments:
            #print(segment.wkt)
            xy = list(segment.coords) 
            xy[::len(list(xy))-1]
            self.junctions.extend(xy)

        # only get coordinates that appear only once
        self.junctions = [i for i in self.junctions if self.junctions.count(i) is 1]               

    def join(self, data):
        """
        start join function
        
        to find shared paths:
        https://shapely.readthedocs.io/en/stable/manual.html#shared-paths
        
        to set up a R-tree:
        https://shapely.readthedocs.io/en/stable/manual.html#str-packed-r-tree
        
        get cartesian product:
        https://stackoverflow.com/a/34032549
        """
        print(data)
        g1 = data['lines'][0]
        g2 = data['lines'][1]

        self.junctions_two_lines(g1, g2)

        data['junctions'] = self.junctions
        return data        
