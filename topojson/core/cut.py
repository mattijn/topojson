import itertools
import pprint
import copy
import numpy as np
from shapely import geometry
from shapely.strtree import STRtree
from .join import Join
from ..ops import insert_coords_in_line
from ..ops import fast_split
from ..ops import np_array_from_lists
from ..ops import select_unique_combs
from ..utils import serialize_as_svg


class Cut(Join):
    """
    This class targets the following objectives:
    1. Split linestrings given the junctions of shared paths
    2. Identifies indexes of linestrings that are duplicates

    The cut function is the third step in the topology computation.
    The following sequence is adopted:
    1. extract
    2. join
    3. cut
    4. dedup
    5. hashmap

    Parameters
    ----------
    data : dict
        object created by the method topojson.Join.

    Returns
    -------
    dict
        object updated and expanded with
        - updated key: linestrings
        - new key: bookkeeping_duplicates
        - new key: bookkeeping_linestrings
    """

    def __init__(self, data, options={}):
        # execute previous step
        super().__init__(data, options)

        # initation topology items
        self.duplicates = []
        self.bookkeeping_linestrings = []

        # execute main function
        self.output = self.cutter(self.output)

    def __repr__(self):
        return "Cut(\n{}\n)".format(pprint.pformat(self.output))

    def to_dict(self):
        topo_object = copy.copy(self.output)
        topo_object["options"] = vars(topo_object["options"])
        return topo_object

    def to_svg(self, separate=False, include_junctions=False):
        serialize_as_svg(self.output, separate, include_junctions)

    def cutter(self, data):
        """
        Entry point for the class Cut.

        The cut function is the third step in the topology computation.
        The following sequence is adopted:
        1. extract
        2. join
        3. cut
        4. dedup
        5. hashmap

        Parameters
        ----------
        data : dict
            object created by the method topojson.join.

        Returns
        -------
        dict
            object updated and expanded with
            - updated key: linestrings
            - new key: bookkeeping_duplicates
            - new key: bookkeeping_linestrings
        """

        if data["junctions"]:
            # split each feature given the intersections
            # prepare the junctions as a 2d coordinate array
            mp = data["junctions"]
            if isinstance(mp, geometry.Point):
                mp = geometry.MultiPoint([mp])

            # create spatial index on junctions
            tree_splitter = STRtree(mp)
            # splitter = np.squeeze(np.array([pt.xy for pt in mp]), axis=(2,))
            slist = []
            for ls in data["linestrings"]:
                # slines = split(ls, mp)
                line, splitter = insert_coords_in_line(ls, tree_splitter)
                # prev function returns None for splitter if there is nothing to split
                if splitter is not None:
                    slines = fast_split(line, splitter)
                    slist.append(list(geometry.MultiLineString(slines)))
                else:
                    slist.append([ls])

            # flatten the splitted linestrings, create bookkeeping_geoms array
            # and find duplicates
            self.segments_list, bk_array = self.flatten_and_index(slist)
            self.find_duplicates(self.segments_list)
            self.bookkeeping_linestrings = bk_array.astype(float)

        elif data["bookkeeping_geoms"]:
            bk_array = np_array_from_lists(data["bookkeeping_geoms"]).ravel()
            bk_array = np.expand_dims(
                bk_array[~np.isnan(bk_array)].astype(np.int64), axis=1
            )
            self.segments_list = data["linestrings"]
            self.find_duplicates(data["linestrings"])
            self.bookkeeping_linestrings = bk_array

        else:
            self.segments_list = data["linestrings"]

        # prepare to return object
        data["linestrings"] = self.segments_list
        data["bookkeeping_duplicates"] = np.array(self.duplicates)
        data["bookkeeping_linestrings"] = self.bookkeeping_linestrings

        return data

    def flatten_and_index(self, slist):
        """
        Function to create a flattened list of splitted linestrings and create a
        numpy array of the bookkeeping_geoms for tracking purposes.

        Parameters
        ----------
        slist : list of LineString
            list of splitted LineStrings

        Returns
        -------
        list
            segmntlist flattens the nested LineString in slist
        numpy.array
            array_bk is a bookkeeping array with index values to each LineString
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
        array_bk = np_array_from_lists(list_bk)

        return segmntlist, array_bk

    def find_duplicates(self, segments_list):
        """
        Function for solely detecting and recording duplicate LineStrings.
        Firstly creates couple-combinations of LineStrings. A couple is defined
        as two linestrings where the enveloppe overlaps. Indexes of duplicates are
        appended to the list self.duplicates.

        Parameters
        ----------
        segments_list : list of LineString
            list of valid LineStrings

        """

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
