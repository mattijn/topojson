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
        * dedup only arcs, not geoms.
        """
        
        # deduplicate equal geometries
        # create numpy array from bookkeeping variable for numerical computation
        array_bk = self.index_array(data['bookkeeping'])
        array_bk = self.deduplicate(data['duplicates'], data['linestrings'], array_bk)
        data['bookkeeping'] = self.list_from_array(array_bk)

        return data
    
    
def _deduper(data):
    data = copy.deepcopy(data)
    Dedup = _Dedup()
    d = Dedup.main(data)
    return d
