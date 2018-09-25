from shapely import geometry

class _Cut:
    """
    cut shared paths and keep track of it
    """

    def __init__(self):
        # initation topology items
        self.junctions = []
        self.segments = []
            
    def main(self, data):
        """
        Cuts the linestrings given the junctions of shared paths.

        The cut function is the third step in the topology computation.
        (Proably) the following sequence is adopted:
        1. extract
        2. join
        3. cut
        4. dedup        
 
        Notes:
        * prepared geometric operations can only be applied on many-points vs polygon operations
        * firstly dedup recorded equal geoms, since equal geoms will be cut both.

        The following links have been used as referene in creating this object/functions.
        TODO: delete when needed.

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
