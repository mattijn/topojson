from shapely import geometry

class _Cut:
    """
    identify junctions (intersection points).
    """

    def __init__(self):
        # initatie topology items
        self.junctions = []
        self.segments = []

            
    def main(self, data):
        """
        start cut function
 
        Prepared Geometry Operations
        Shapely geometries can be processed into a state that supports more efficient batches of operations.

        Prepared geometries instances have the following methods: contains, 
        contains_properly, covers, and intersects. 
        All have exactly the same arguments and usage as their counterparts in 
        non-prepared geometric objects.
        https://shapely.readthedocs.io/en/stable/manual.html#prepared-geometry-operations


        """
        
        return data
    
    
def _cutter(data):
    Cut = _Cut()
    c = Cut.main(data)
    return c
