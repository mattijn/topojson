import numpy as np
import itertools
import copy

class _Dedup:
    """
    class for eliminating duplicate copies of repeated data.
    """

    def __init__(self):
        # initation topology items
        pass # nothing new yet

            
    def main(self, data):
        """
        Deduplication of linestrings that contain duplicates.

        The dedup function is the fourth step in the topology computation.
        (Proably) the following sequence is adopted:
        1. extract
        2. join
        3. cut
        4. dedup        
 
        Developping Notes:
        * note sure if a class is required for this, but start with consistency 
        * start of iteration between cut.py and dedup.py
        """
        # create numpy array from bookkeeping variable for numerical computation
        array_bk = np.array(list(itertools.zip_longest(*data['bookkeeping'], fillvalue=np.nan))).T

        # start deduping
        # iterate over copy to change original list
        for idx, dup_pair in enumerate(list(data['duplicates'])):
            idx_keep = dup_pair[0]
            idx_pop = dup_pair[1]
            
            # remove duplicate linestring
            del data['linestrings'][idx_pop]
            
            # change reference duplicate and all elements greater index
            array_bk[array_bk == idx_pop] = idx_keep
            # numpy 1.8.0-notes states:
            # "Comparing NaN floating point numbers now raises the invalid runtime warning."
            with np.errstate(invalid='ignore'):
                array_bk[array_bk > idx_pop] -= 1
            
            # remove duplicate entry
            del data['duplicates'][idx]

        # convert to list after numpy computation is finished
        list_bk = [obj[~np.isnan(obj)].astype(int).tolist() for obj in array_bk]        
        data['bookkeeping'] = list_bk

        return data
    
    
def _deduper(data):
    data = copy.deepcopy(data)
    Dedup = _Dedup()
    d = Dedup.main(data)
    return d
