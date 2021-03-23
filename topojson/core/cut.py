import itertools
import pprint
import copy
import numpy as np
from shapely import geometry
from shapely.strtree import STRtree
from .join import Join
from ..ops import insert_coords_in_line
from ..ops import np_array_bbox_points_line
from ..ops import fast_split
from ..ops import find_duplicates
from ..ops import np_array_from_lists
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
        self._duplicates = []
        self._bookkeeping_linestrings = []

        # execute main function
        self.output = self._cutter(self.output)

    def __repr__(self):
        return "Cut(\n{}\n)".format(pprint.pformat(self.output))

    def to_dict(self):
        """
        Convert the Cut object to a dictionary.
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
        serialize_as_svg(
            self.output, separate=separate, include_junctions=include_junctions
        )

    def _cutter(self, data):
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
            slist = []
            # junctions are only existing in coordinates of linestring
            if self.options.shared_coords:
                for ls in data["linestrings"]:
                    line, splitter = np_array_bbox_points_line(ls, tree_splitter)
                    # prev function returns None for splitter if there is nothing to split
                    if splitter is not None:
                        slines = fast_split(line, splitter)
                        slist.append(slines)
                    else:
                        slist.append(np.array([ls.coords]))

            # junctions can exist between existing coords of linestring
            else:
                for ls in data["linestrings"]:
                    # slines = split(ls, mp)
                    line, splitter = insert_coords_in_line(ls, tree_splitter)
                    # prev function returns None for splitter if there is nothing to split
                    if splitter is not None:
                        slines = fast_split(line, splitter)
                        slist.append(slines)
                    else:
                        slist.append(np.array([ls.coords]))

            # flatten the splitted linestrings, create bookkeeping_geoms array
            # and find duplicates
            self._segments_list, bk_array = self._flatten_and_index(slist)
            self._duplicates = find_duplicates(self._segments_list)
            self._bookkeeping_linestrings = bk_array.astype(float)

        elif data["bookkeeping_geoms"]:
            bk_array = np_array_from_lists(data["bookkeeping_geoms"]).ravel()
            bk_array = np.expand_dims(
                bk_array[~np.isnan(bk_array)].astype(np.int64), axis=1
            )
            self._segments_list = data["linestrings"]
            self._duplicates = find_duplicates(data["linestrings"], type="linestring")
            self._bookkeeping_linestrings = bk_array

        else:
            self._segments_list = data["linestrings"]

        # prepare to return object
        data["linestrings"] = self._segments_list
        data["bookkeeping_duplicates"] = self._duplicates
        data["bookkeeping_linestrings"] = self._bookkeeping_linestrings

        return data

    def _flatten_and_index(self, slist):
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
