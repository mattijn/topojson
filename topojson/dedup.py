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
        self.shared_arcs_idx = []
        pass       

    def index_array(self, parameter_list):
        # create numpy array from variable
        array_bk = np.array(list(itertools.zip_longest(*parameter_list, fillvalue=np.nan))).T
        return array_bk

    def deduplicate(self, dup_pair_list, linestring_list, array_bk):
        # start deduping
        for idx, dup_pair in enumerate(dup_pair_list):
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
            
            # store shared arc index
            idx2keep = idx_keep if idx_pop > idx_keep else idx_keep - 1
            self.shared_arcs_idx.append(idx2keep)
            # set duplicate entry to -99
            dup_pair_list[idx, :] = -99
        
        return array_bk   

    def flatten_and_index(self, slist):
        """
        function to create a flattened list of splitted linestrings, but make sure to
        create a numpy array for bookkeeping_geoms for the numerical computation
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
        # convert numpy array to list, where elements set as np.nan are filtered
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
        Quantization might be explained here: https://gist.github.com/scardine/6320052
        """
        
        # deduplicate equal geometries
        # create numpy array from bookkeeping_geoms variable for numerical computation
        array_bk = self.index_array(data['bookkeeping_linestrings'])
        array_bk = self.deduplicate(data['duplicates'], data['linestrings'], array_bk)

        # apply a shapely linemerge to merge all contiguous line-elements
        # first create a mask for shared arcs to select only non-duplicates
        # slice array_bk_ndp for geoms (rows) containing np.nan values
        mask = np.isin(array_bk, self.shared_arcs_idx)
        array_bk_ndp = copy.deepcopy(array_bk)
        array_bk_ndp[mask] = np.nan
        sliced_array_bk_ndp = array_bk_ndp[np.argwhere(np.isnan(array_bk_ndp))[0,:]]

        # iterate over geoms that contain shared arcs and try linemerge on remaining arcs
        for idx, arcs_geom_bk in enumerate(sliced_array_bk_ndp):
            # print(np.isnan(arcs_geom_bk).any()) # should print True
            # set number of arcs before trying linemerge
            ndp_arcs_bk = arcs_geom_bk[~np.isnan(arcs_geom_bk)].astype(int)#.tolist()
            no_ndp_arcs_bk = len(ndp_arcs_bk)

            # apply linemerge
            ndp_arcs = list(linemerge([ data['linestrings'][i] for i in ndp_arcs_bk ]))
            no_ndp_arcs = len(ndp_arcs)

            # only if no_ndp_arcs is different than no_ndp_arcs_bk continue, else is no changes 
            if no_ndp_arcs != no_ndp_arcs_bk:
                # TODO: place the merged linestrings back in data['linestrings']
                # TODO: solve the bookkeeping
                # print some variables if some linestrings were merged
                print(idx, ndp_arcs_bk, ndp_arcs)       
        
        # set changed objects
        del data['bookkeeping_linestrings']
        data['bookkeeping_arcs'] = self.list_from_array(array_bk)
        data['bookkeeping_shared_arcs'] = self.shared_arcs_idx
        data['duplicates'] = self.list_from_array(data['duplicates'][data['duplicates'] != -99])

        return data
    
    
def _deduper(data):
    data = copy.deepcopy(data)
    Dedup = _Dedup()
    d = Dedup.main(data)
    return d
