from shapely import geometry
from shapely.ops import split
from shapely.ops import linemerge
import itertools
import numpy as np
import copy

class _Dedup:
    """
    cut shared paths and keep track of it
    """

    def __init__(self):
        # initation topology items
        pass       

    def index_array(self, parameter_list):
        # create numpy array from variable
        array_bk = np.array(list(itertools.zip_longest(*parameter_list, fillvalue=np.nan))).T
        return array_bk

    def deduplicate(self, dup_pair_list, linestring_list, array_bk):
        # start deduping
        # iterate over copy to change original list
        for idx, dup_pair in enumerate(list(dup_pair_list)):
            idx_keep = dup_pair[0]
            idx_pop = dup_pair[1]
            
            # remove duplicate linestring
            del linestring_list[idx_pop]
            
            # change reference duplicate and all elements greater index
            array_bk[array_bk == idx_pop] = idx_keep
            # numpy 1.8.0-notes states:
            # "Comparing NaN floating point numbers now raises the invalid runtime warning."
            with np.errstate(invalid='ignore'):
                array_bk[array_bk > idx_pop] -= 1
            
            # remove duplicate entry
            del dup_pair_list[idx]  
        
        return array_bk   

    def flatten_and_index(self, slist):
        """
        function to create a flattened list of splitted linestrings, but make sure to
        create a numpy array for bookkeeping for the numerical computation
        """
        # flatten
        segmntlist = list(itertools.chain(*slist))
        # create slice pairs
        segmnt_idx = list(itertools.accumulate([len(geom) for geom in slist]))
        slice_pair = [(segmnt_idx[idx - 1] if idx >= 1 else 0, current) for idx, current in enumerate(segmnt_idx)]
        # index array
        list_bk = [range(len(segmntlist))[s[0]:s[1]] for s in slice_pair]
        array_bk = self.index_array(list_bk)
        
        return segmntlist, array_bk  

    def list_from_array(self, array_bk):
        # convert to list after numpy computation is finished
        list_bk = [obj[~np.isnan(obj)].astype(int).tolist() for obj in array_bk]   
        return list_bk        
            
    def main(self, data):
        """
        Deduplication of linestrings that contain duplicates

        The cut function is the third step in the topology computation.
        The following sequence is adopted:
        1. extract
        2. join
        3. cut 
        4. dedup      
 
        Developping Notes:
        * prepared geometric operations can only be applied on many-points vs polygon operations
        * firstly dedup recorded equal geoms, since equal geoms will be cut both.
        * start of iteration between cut.py and dedup.py        

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
        
        # --- 1 ---
        # start with first round of deduplicate equal geometries
        # create numpy array from bookkeeping variable for numerical computation
        array_bk = self.index_array(data['bookkeeping'])
        array_bk = self.deduplicate(data['duplicates'], data['linestrings'], array_bk)
        data['bookkeeping'] = self.list_from_array(array_bk)

        # --- 1 ---
        # split each feature given the intersections 
        mp = geometry.MultiPoint(data['junctions'])
        slist = []
        for ls in data['linestrings']:
            slines = split(ls, mp)
            slist.append(list(geometry.MultiLineString(slines)))        
        
        # flatten the splitted linestrings and create bookkeeping array
        segments_list, nested_array = self.flatten_and_index(slist)

        # --- 3 ---
        # second round of deduplication on splitted linestrings
        # first create list with all combinations of lines
        # this code block comes from join.py
        # TODO: rewrite into functions
        # TODO: make it work
        ls_idx = [pair for pair in enumerate(segments_list)]
        line_combs = list(itertools.combinations(ls_idx, 2))

        # iterate over line combinations
        for geoms in line_combs:
            i1 = geoms[0][0]
            g1 = geoms[0][1]

            i2 = geoms[1][0]
            g2 = geoms[1][1]

            # check if geometry are equal
            # being equal meaning the geometry object coincide with each other.
            # a rotated polygon or reversed linestring are both considered equal.
            if g1.equals(g2):
                # we only deup the geoms that are equal
                idx_pop = i1 if len(g1.coords) <= len(g2.coords) else i2
                idx_keep = i1 if i2 == idx_pop else i2
                data['duplicates'].append((idx_keep, idx_pop)) 
        
        # --- 4 ---
        # TODO: separate shared arcs from single used arcs
        # TODO: apply linemerge on the single used arcs (this avoids inclusion of rotation!)
        # TODO: etc

        return data
    
    
def _deduper(data):
    data = copy.deepcopy(data)
    Dedup = _Dedup()
    d = Dedup.main(data)
    return d
