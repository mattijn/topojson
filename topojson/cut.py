from shapely import geometry
from .utils.ops import fast_split
from .utils.ops import select_unique_combs
import itertools
import numpy as np
import copy


class Cut:
    """
    cut shared paths and keep track of it
    """

    def __init__(self):
        # initation topology items
        self.duplicates = []
        self.bookkeeping_linestrings = []
        pass

    def index_array(self, parameter_list):
        # create numpy array from variable
        array_bk = np.array(
            list(itertools.zip_longest(*parameter_list, fillvalue=np.nan))
        ).T
        return array_bk

    def flatten_and_index(self, slist):
        """
        function to create a flattened list of splitted linestrings and create a 
        numpy array for bookkeeping_geoms for the numerical computation
        """
        # flatten
        segmntlist = list(itertools.chain(*slist))
        # create slice pairs
        segmnt_idx = list(itertools.accumulate([len(geom) for geom in slist]))
        slice_pair = [
            (segmnt_idx[idx - 1] if idx >= 1 else 0, current)
            for idx, current in enumerate(segmnt_idx)
        ]
        # index array
        list_bk = [range(len(segmntlist))[s[0] : s[1]] for s in slice_pair]
        array_bk = self.index_array(list_bk)

        return segmntlist, array_bk

    def find_duplicates(self, segments_list):
        # find duplicates of splitted linestrings
        # create list with unique combinations of lines using a rdtree
        line_combs = select_unique_combs(segments_list)

        # iterate over index combinations
        for i1, i2 in line_combs:
            g1 = segments_list[i1]
            g2 = segments_list[i2]

            # check if geometry are equal
            # being equal meaning the geometry object coincide with each other.
            # a rotated polygon or reversed linestring are both considered equal.
            if g1.equals(g2):
                idx_pop = i1 if len(g1.coords) <= len(g2.coords) else i2
                idx_keep = i1 if i2 == idx_pop else i2
                self.duplicates.append([idx_keep, idx_pop])

    def main(self, data):
        """
        Cut the linestrings given the junctions of shared paths.

        The cut function is the third step in the topology computation.
        The following sequence is adopted:
        1. extract
        2. join
        3. cut 
        4. dedup 
        5. hashmap     
        """

        if data["junctions"]:
            # split each feature given the intersections
            # mp = geometry.MultiPoint(data["junctions"])
            mp = data["junctions"]
            slist = []
            for ls in data["linestrings"]:
                # slines = split(ls, mp)
                slines = fast_split(ls, mp)
                slist.append(list(geometry.MultiLineString(slines)))

            # flatten the splitted linestrings and create bookkeeping_geoms array
            # and find duplicates
            self.segments_list, bk_array = self.flatten_and_index(slist)
            # return self.segments_list
            self.find_duplicates(self.segments_list)
            self.bookkeeping_linestrings = bk_array.astype(float)

        else:
            bk_array = self.index_array(data["bookkeeping_geoms"]).ravel()
            bk_array = np.expand_dims(bk_array[~np.isnan(bk_array)].astype(int), axis=1)
            self.segments_list = data["linestrings"]
            self.find_duplicates(data["linestrings"])
            self.bookkeeping_linestrings = bk_array

        # prepare to return object
        data["linestrings"] = self.segments_list
        data["bookkeeping_duplicates"] = np.array(self.duplicates)
        data["bookkeeping_linestrings"] = self.bookkeeping_linestrings

        return data


def cut(data):
    data = copy.deepcopy(data)
    cutter = Cut()
    return cutter.main(data)
