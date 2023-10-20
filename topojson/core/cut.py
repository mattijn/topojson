import itertools
import pprint
import copy
import numpy as np
from shapely import geometry
from shapely.strtree import STRtree
from .join import Join
from ..ops import ignore_shapely2_warnings
from ..ops import insert_coords_in_line
from ..ops import np_array_bbox_points_line
from ..ops import fast_split
from ..ops import find_duplicates
from ..ops import np_array_from_lists
from ..ops import remove_collinear_points
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

        # initiation topology items
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
            with ignore_shapely2_warnings():
                tree_splitter = STRtree(mp)
            lines_split = []

            # create dict with original geometry type per linestring
            lines_object_types = self._get_linestring_types(
                objects=data["objects"],
                bookkeeping_geoms=data["bookkeeping_geoms"],
            )

            # junctions are only existing in coordinates of linestring
            for index, linestring in enumerate(data["linestrings"]):
                if self.options.shared_coords:
                    line, splitter = np_array_bbox_points_line(
                        linestring, tree_splitter
                    )
                else:
                    line, splitter = insert_coords_in_line(linestring, tree_splitter)
                # prev function returns None for splitter if nothing to split
                if splitter is not None:
                    is_ring = False
                    if lines_object_types[index] in ["Polygon", "MultiPolygon"]:
                        is_ring = True
                    line_split = fast_split(line, splitter, is_ring)
                    if isinstance(line_split, list):
                        line_split = [
                            remove_collinear_points(line) for line in line_split
                        ]
                    else:
                        line_split = remove_collinear_points(line_split)
                    lines_split.append(line_split)
                else:
                    lines_split.append(
                        [remove_collinear_points(np.array(linestring.coords))]
                    )
            # flatten the splitted linestrings, create bookkeeping_geoms array
            # and find duplicates
            self._segments_list, bk_array = self._flatten_and_index(lines_split)
            self._duplicates = find_duplicates(self._segments_list)
            self._bookkeeping_linestrings = bk_array.astype(float)
        elif data["bookkeeping_geoms"]:
            bk_array = np_array_from_lists(data["bookkeeping_geoms"]).ravel()
            bk_array = np.expand_dims(
                bk_array[~np.isnan(bk_array)].astype(np.int64), axis=1
            )
            self._segments_list = [
                remove_collinear_points(np.array(ls.coords))
                for ls in data["linestrings"]
            ]
            self._duplicates = find_duplicates(self._segments_list)
            self._bookkeeping_linestrings = bk_array
        else:
            self._segments_list = [
                remove_collinear_points(np.array(ls.coords))
                for ls in data["linestrings"]
            ]
        # prepare to return object
        data["linestrings"] = self._segments_list
        data["bookkeeping_duplicates"] = self._duplicates
        data["bookkeeping_linestrings"] = self._bookkeeping_linestrings

        return data

    def _get_linestring_types(
        self, objects, bookkeeping_geoms, bookkeeping_linestrings=None
    ) -> dict:
        """
        Returns the original geometry type for each linestring.

        Parameters
        ----------
        objects : list
            list of original objects that contains a list of arcs for each geometry.
        bookkeeping_geoms : list
            list of arc-linestrings for each arc in the objects list.
        bookkeeping_linestrings : numpy array, optional
            array with for each arc-linestring the corresponding linestrings that were
            constructed after splitting them on junctions. Defaults to None.

        Returns
        -------
        dict :
            dict with for each data["linestrings"] index the geometry type of
            the object the linestring originated from.
        """
        # create dict with original geometry type per linestring
        def recurse_geometries(object):
            # If object is not a list, make it a list to be able to loop
            if not isinstance(object, list):
                object = [object]
            # Loop over children of object
            for object_child in object:
                # Depending on input format there is one or more geometry in an object
                if "geometries" in object_child:
                    geometries = object_child["geometries"]
                    recurse_geometries(geometries)
                elif object_child["type"] != "Point":
                    # For non-Point geometries, loop over arcs
                    for arc_id in object_child["arcs"]:
                        # Find the linestrings for the arc via bookkeeping_geoms
                        for arc_line_id in bookkeeping_geoms[arc_id]:
                            if bookkeeping_linestrings is None:
                                arc_lines = [arc_line_id]
                            else:
                                arc_lines = bookkeeping_linestrings[arc_line_id]
                            for linestring_id in arc_lines:
                                if linestring_id >= 0:
                                    linestring_object_types[
                                        linestring_id
                                    ] = object_child["type"]

        linestring_object_types = {}
        for object_key in objects:
            recurse_geometries(objects[object_key])
        return linestring_object_types

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
            segment_list flattens the nested LineString in slist
        numpy.array
            array_bk is a bookkeeping array with index values to each LineString
        """

        # flatten
        segment_list = list(itertools.chain(*slist))
        # create slice pairs
        segment_idx = list(itertools.accumulate([len(geom) for geom in slist]))
        slice_pair = [
            (segment_idx[idx - 1] if idx >= 1 else 0, current)
            for idx, current in enumerate(segment_idx)
        ]
        # index array
        list_bk = [range(len(segment_list))[s[0] : s[1]] for s in slice_pair]
        array_bk = np_array_from_lists(list_bk)

        return segment_list, array_bk
