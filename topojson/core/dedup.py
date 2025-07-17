import copy
import pprint
import numpy as np
from shapely import geometry
from shapely.ops import linemerge
from .cut import Cut
from ..ops import asvoid
from ..ops import map_values
from ..ops import lists_from_np_array
from ..ops import cart
from ..utils import serialize_as_svg


class Dedup(Cut):
    """
    Dedup duplicates and merge contiguous arcs
    """

    def __init__(self, data, options={}):
        # execute previous step
        super().__init__(data, options)

        # initiation topology items
        self._idx_merged_dups = []

        # execute main function of Dedup
        self.output = self._deduper(self.output)

    def __repr__(self):
        return "Dedup(\n{}\n)".format(pprint.pformat(self.output))

    def to_dict(self):
        """
        Convert the Dedup object to a dictionary.
        """
        topo_object = copy.copy(self.output)
        topo_object["options"] = vars(self.options)
        return topo_object

    def to_svg(self, separate=False, include_junctions=False):
        """
        Display the linestrings and junctions as SVG.

        Parameters
        ----------
        separate : boolean
            If `True`, each of the linestrings will be displayed separately.
            Default is `False`
        include_junctions : boolean
            If `True`, the detected junctions will be displayed as well.
            Default is `False`
        """
        serialize_as_svg(self.output, separate, include_junctions)

    def _deduper(self, data):
        """
        Deduplication of linestrings that contain duplicates

        The dedup function is the fourth step in the topology computation.
        The following sequence is adopted:
        1. extract
        2. join
        3. cut
        4. dedup
        5. hashmap
        """

        # deduplicate equal geometries
        # create numpy array from bookkeeping_geoms variable for numerical computation
        if len(data["bookkeeping_linestrings"]):
            array_bk = np.vstack(data["bookkeeping_linestrings"])
        else:
            array_bk = np.array([])
        array_bk_sarcs = None
        if len(data["bookkeeping_duplicates"]):
            array_bk, array_bk_sarcs = self._deduplicate(
                data["bookkeeping_duplicates"], data["linestrings"], array_bk
            )

        # apply a shapely linemerge to merge all contiguous line-elements
        # first create a mask for shared arcs to select only non-duplicates
        mask = np.isin(array_bk, array_bk_sarcs)
        array_bk_ndp = copy.deepcopy(array_bk.astype(float))

        # only do merging of arcs if there are contiguous arcs in geoms
        if array_bk_ndp[mask].size != 0:
            # make sure the idx of shared arcs are set to np.nan
            array_bk_ndp[mask] = np.nan

            # slice array_bk_ndp for geoms (rows) containing np.nan values
            slice_idx = np.all(~np.isnan(array_bk_ndp)[:, [0, -1]], axis=1)
            sliced_array_bk_ndp = array_bk_ndp[slice_idx]

            if sliced_array_bk_ndp.shape[1] > 1:
                # apply linemerge on geoms containing contiguous arcs and collect idx
                idx_merged_dups = self._merge_contiguous_arcs(data, sliced_array_bk_ndp)
                # use deduplicate as proxy-function for merged arcs index bookkeeping
                if idx_merged_dups is not None:
                    array_bk, array_bk_sarcs = self._pop_merged_arcs(
                        idx_merged_dups, data["linestrings"], array_bk
                    )

        # prepare to return object
        del data["bookkeeping_linestrings"]
        data["bookkeeping_arcs"] = lists_from_np_array(array_bk)
        if len(data["bookkeeping_duplicates"]):
            data["bookkeeping_shared_arcs"] = array_bk_sarcs.astype(np.int64).tolist()
            data["bookkeeping_duplicates"] = []
        else:
            data["bookkeeping_shared_arcs"] = []

        return data

    def _find_merged_linestring(self, data, no_ndp_arcs, ndp_arcs, ndp_arcs_bk):
        """
        Function to find the index of LineString in a MultiLineString object which
        contains merged LineStrings.

        Parameters
        ----------
        data : dict
            object that contains the 'linestrings'
        no_ndp_arcs : int
            number of non-duplicate arcs
        ndp_arcs : array
            array containing index values of the related arcs

        Returns
        -------
        np.array
            combinations of index of LineString that contains merged LineStrings
        """

        for segment_idx in range(no_ndp_arcs):
            # use isin function as proxy for contains
            merged_arcs_bool = [
                np.isin(
                    asvoid(data["linestrings"][i]),
                    asvoid(ndp_arcs.geoms[segment_idx].coords),
                ).any()
                for i in ndp_arcs_bk
            ]
            count_merged_arcs = merged_arcs_bool.count(True)
            if count_merged_arcs >= 2:
                merged_arcs = ndp_arcs_bk[merged_arcs_bool]
                # create dedup pairs of merged arcs
                merged_dedups = cart(merged_arcs)
                return segment_idx, merged_dedups

    def _deduplicate(self, bk_dups, linestring_list, array_bk):
        """
        Function to deduplicate items

        Parameters
        ----------
        bk_dups : numpy.ndarray
            array containing pair of indexes that refer to duplicate linestrings.
        linestring_list : list of shapely.geometry.LineStrings
            list of linestrings from which items will be removed.
        array_bk : numpy.ndarray
            array used for bookkeeping of linestrings.

        Returns
        -------
        numpy.ndarray
            new array of bookkeeping linestrings
        numpy.ndarray
            bookkeeping array of shared arcs
        """
        # guarantee that first column contain higher values than second column
        bk_dups.sort(axis=1)
        bk_dups = bk_dups[:, ::-1]

        # define arrays from which the indices can be kept and popped
        vals2keep = bk_dups[:, 0]
        vals2pop = bk_dups[:, 1]

        # remove duplicate linestrings (loop over indices backwards to avoid popping
        # subsequent indices)
        for idx in sorted(vals2pop, reverse=True):
            del linestring_list[idx]

        # prepare bookkeeping array, add +1 so NaN can be 0 and array only contains
        # positive integers
        arr = array_bk + 1
        arr[np.isnan(arr)] = 0
        arr = arr.astype(np.int64)

        # replace duplicates by single values, add +1 since NaNs are on 0
        arr_map = map_values(arr, vals2pop + 1, vals2keep + 1)

        # popped indices changes the bookkeeping, align decremented indices
        # add +1 since NaNs are on 0
        arr_bin = np.digitize(arr_map, sorted(vals2pop + 1), right=False)
        arr_new = arr_map - arr_bin

        # set 0 to nan and subtract -1
        arr_new = arr_new.astype(float)
        arr_new[arr_new == 0] = np.nan
        arr_new -= 1

        # collect new indices of shared arcs
        u, c = np.unique(arr_new[~np.isnan(arr_new)], return_counts=True)
        arr_bk_sarcs = u[c > 1]

        return arr_new, arr_bk_sarcs

    def _merge_contiguous_arcs(self, data, sliced_array_bk_ndp):
        """
        Function that iterate over geoms that contain shared arcs and try linemerge
        on remaining arcs. The merged contiguous arc is placed back in the 'linestrings'
        object.
        The arcs that can be popped are placed within the merged_arcs_idx list

        Parameters
        ----------
        data : dict
            object that contains the 'linestrings'.
        sliced_array_bk_ndp : numpy.ndarray
            bookkeeping array where shared linestrings are set to np.nan.
        """

        list_merged_dups = []
        for arcs_geom_bk in sliced_array_bk_ndp:
            # set number of arcs before trying linemerge
            ndp_arcs_bk = arcs_geom_bk[~np.isnan(arcs_geom_bk)].astype(np.int64)
            no_ndp_arcs_bk = len(ndp_arcs_bk)

            # apply linemerge
            ndp_arcs = linemerge([data["linestrings"][i] for i in ndp_arcs_bk])
            if isinstance(ndp_arcs, geometry.LineString):
                ndp_arcs = geometry.MultiLineString([ndp_arcs])
            no_ndp_arcs = len(ndp_arcs.geoms)

            # if no_ndp_arcs is different than no_ndp_arcs_bk, than a merge took place
            # if lengths are equal, than no merge did occur and no need to solve the
            # bookkeeping
            if no_ndp_arcs != no_ndp_arcs_bk:
                # get the idx of the linestring which was merged
                idx_merged_arc, merged_dedups = self._find_merged_linestring(
                    data, no_ndp_arcs, ndp_arcs, ndp_arcs_bk
                )

                # replace arc with highest index of non-duplicate arcs
                # and collect remaining arcs as duplicates
                idx_keep = merged_dedups[0][0]
                data["linestrings"][idx_keep] = np.array(
                    ndp_arcs.geoms[idx_merged_arc].coords
                )
                list_merged_dups.append(merged_dedups)

        if len(list_merged_dups):
            idx_merged_dups = np.vstack(list_merged_dups)
            return idx_merged_dups
        else:
            return None

    def _pop_merged_arcs(self, bk_dups, linestring_list, array_bk):
        """
        The collected indices that can be popped, since they have been merged
        This functions looks like _deduplicate(), but is slightly different where
        vals2pop indices are set to 0 (NaN).
        """

        # guarantee that first column contain higher values than second column
        bk_dups.sort(axis=1)
        bk_dups = bk_dups[:, ::-1]

        # define arrays from which the indices can be kept and popped
        # vals2keep = bk_dups[:, 0]
        vals2pop = bk_dups[:, 1]

        # remove duplicate linestrings (loop over indices backwards to avoid popping
        # subsequent indices)
        for idx in sorted(vals2pop, reverse=True):
            del linestring_list[idx]

        # prepare bookkeeping array, add +1 so NaN can be 0 and array only contains
        # positive integers
        arr = array_bk + 1
        arr[np.isnan(arr)] = 0
        arr = arr.astype(np.int64)

        # replace duplicates by single values, add +1 since NaNs are on 0
        zero_array = np.zeros_like(vals2pop)
        arr_map = map_values(arr, vals2pop + 1, zero_array)

        # popped indices changes the bookkeeping, align decremented indices
        # add +1 since NaNs are on 0
        arr_bin = np.digitize(arr_map, sorted(vals2pop + 1), right=False)
        arr_new = arr_map - arr_bin

        # set 0 to nan and subtract -1
        arr_new = arr_new.astype(float)
        arr_new[arr_new == 0] = np.nan
        arr_new -= 1

        # collect new indices of shared arcs
        u, c = np.unique(arr_new, return_counts=True)
        arr_bk_sarcs = u[c > 1]
        arr_bk_sarcs = arr_bk_sarcs[~np.isnan(arr_bk_sarcs)]

        return arr_new, arr_bk_sarcs
