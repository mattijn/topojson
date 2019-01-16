from shapely import geometry
from shapely.ops import split
from shapely.ops import linemerge
import itertools
import numpy as np
import copy


class Dedup:
    """
    dedup duplicates and merge contiguous arcs
    """

    def __init__(self):
        # initation topology items
        self.shared_arcs_idx = []
        self.merged_arcs_idx = []
        pass

    def index_array(self, parameter_list):
        """"
        Function to create numpy array from nested lists. The shape of the numpy array 
        are the number of nested lists (rows) x the length of the longest nested list 
        (columns). Rows that contain less values are filled with np.nan values.
        """

        array_bk = np.array(
            list(itertools.zip_longest(*parameter_list, fillvalue=np.nan))
        ).T
        return array_bk

    def deduplicate(self, dup_pair_list, linestring_list, array_bk):
        """
        Function to deduplicate items
        """

        # sort the dup_pair_list by the 1st column (idx_keep) in descending order
        dup_pair_list = dup_pair_list[dup_pair_list[:, 0].argsort()[::-1]]
        # initiate an array with np.nans, where sizes equals number of duplicates
        array_bk_sarcs = np.empty(len(dup_pair_list))
        array_bk_sarcs.fill(np.nan)

        # start deduping
        for idx, dup_pair in enumerate(dup_pair_list):
            idx_keep = dup_pair[0]
            idx_pop = dup_pair[1]

            # remove duplicate linestring
            del linestring_list[idx_pop]

            # change reference duplicate to idx_keep
            no_dups = array_bk[array_bk == idx_pop].size
            array_bk[array_bk == idx_pop] = idx_keep

            # next run may affect previous runs, maintain bookkeeping and change
            # all elements greater than the index which was removed.
            with np.errstate(invalid="ignore"):
                array_bk[array_bk > idx_pop] -= no_dups
                dup_pair_list[dup_pair_list > idx_pop] -= no_dups
                array_bk_sarcs[array_bk_sarcs > idx_pop] -= no_dups

            # store shared arc index
            idx2keep = idx_keep if idx_pop > idx_keep else idx_keep - 1
            array_bk_sarcs[idx] = idx2keep

            # set duplicate entry to -99
            dup_pair_list[idx, :] = -99

        return array_bk_sarcs, dup_pair_list

    def merge_contigious_arcs(self, data, sliced_array_bk_ndp):
        """
        Function that iterate over geoms that contain shared arcs and try linemerge 
        on remaining arcs. The merged contigious arc is placed back in the 'linestrings'
        object. 
        The arcs that can be popped are placed within the merged_arcs_idx list
        """
        for arcs_geom_bk in sliced_array_bk_ndp:
            # set number of arcs before trying linemerge
            ndp_arcs_bk = arcs_geom_bk[~np.isnan(arcs_geom_bk)].astype(int)
            no_ndp_arcs_bk = len(ndp_arcs_bk)

            # apply linemerge
            ndp_arcs = linemerge([data["linestrings"][i] for i in ndp_arcs_bk])
            if isinstance(ndp_arcs, geometry.LineString):
                ndp_arcs = [ndp_arcs]
            no_ndp_arcs = len(ndp_arcs)

            # if no_ndp_arcs is different than no_ndp_arcs_bk, than a merge took place
            # if lengths are equal, than no merge did occur and no need to solve the
            # bookkeeping
            if no_ndp_arcs != no_ndp_arcs_bk:
                # assumes that only first and last item of non-duplicate arcs can merge
                idx_keep = ndp_arcs_bk[-1]
                idx_pop = ndp_arcs_bk[0]

                # replace linestring of idx_keep with merged linestring
                # merged linestring seems to be placed up front, so get idx 0.
                data["linestrings"][idx_keep] = ndp_arcs[0]
                self.merged_arcs_idx.append(idx_pop)

    def pop_merged_arcs(self, data, array_bk, array_bk_sarcs):
        """
        The collected indici that can be popped, since they have been merged
        """

        self.merged_arcs_idx.sort(reverse=True)
        for idx_pop in self.merged_arcs_idx:

            # remove merged linestring
            del data["linestrings"][idx_pop]

            # change reference of merged linestring and all index elements greater
            # then idx_pop
            array_bk[array_bk == idx_pop] = np.nan
            with np.errstate(invalid="ignore"):
                array_bk[array_bk > idx_pop] -= 1
                array_bk_sarcs[array_bk_sarcs > idx_pop] -= 1

    def list_from_array(self, array_bk):
        """
        Function to convert numpy array to list, where elements set as np.nan 
        are filtered
        """

        list_bk = [obj[~np.isnan(obj)].astype(int).tolist() for obj in array_bk]
        return list_bk

    def main(self, data):
        """
        Deduplication of linestrings that contain duplicates

        The dedup function is the fourth step in the topology computation.
        The following sequence is adopted:
        1. extract
        2. join
        3. cut 
        4. dedup
        5. hashmap     
 
        Developping Notes:
        * dedup only arcs, not geoms.
        Quantization might be explained here: https://gist.github.com/scardine/6320052
        """

        # deduplicate equal geometries
        # create numpy array from bookkeeping_geoms variable for numerical computation
        array_bk = self.index_array(data["bookkeeping_linestrings"])
        if data["bookkeeping_duplicates"].size != 0:
            array_bk_sarcs, dup_pair_list = self.deduplicate(
                data["bookkeeping_duplicates"], data["linestrings"], array_bk
            )

        # The assumption that only the first and last item of non-duplicate arcs can
        # merge doesn't hold. For now comment the linemerging of contigiuous
        # line-elements
        # --------------------------------------------------------------------

        # # apply a shapely linemerge to merge all contiguous line-elements
        # # first create a mask for shared arcs to select only non-duplicates
        # mask = np.isin(array_bk, array_bk_sarcs)
        # array_bk_ndp = copy.deepcopy(array_bk.astype(float))

        # # only do merging of arcs if there are contigous arcs in geoms
        # if array_bk_ndp[mask].size != 0:
        #     # make sure idx to shared arcs are set to np.nan
        #     array_bk_ndp[mask] = np.nan

        #     # slice array_bk_ndp for geoms (rows) containing np.nan values
        #     slice_idx = np.all(~np.isnan(array_bk_ndp)[:, [0, -1]], axis=1)
        #     sliced_array_bk_ndp = array_bk_ndp[slice_idx]

        #     # apply linemerge on geoms containing contigious arcs and maintain
        #     # bookkeeping
        #     self.merge_contigious_arcs(data, sliced_array_bk_ndp)

        #     # pop the merged contigious arcs and maintain bookkeeping.
        #     self.pop_merged_arcs(data, array_bk, array_bk_sarcs)

        # prepare to return object
        del data["bookkeeping_linestrings"]
        data["bookkeeping_arcs"] = self.list_from_array(array_bk)
        data["bookkeeping_shared_arcs"] = array_bk_sarcs.astype(int).tolist()
        data["bookkeeping_duplicates"] = self.list_from_array(
            data["bookkeeping_duplicates"][dup_pair_list != -99]
        )

        return data


def dedup(data):
    data = copy.deepcopy(data)
    deduper = Dedup()
    return deduper.main(data)
