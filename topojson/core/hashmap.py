import copy
import pprint
import numpy as np
from shapely import geometry
from shapely.ops import linemerge
from .dedup import Dedup
from ..ops import is_ccw
from ..utils import serialize_as_svg
from ..utils import serialize_as_json
from ..utils import serialize_as_altair


class Hashmap(Dedup):
    """
    hash arcs based on their type
    """

    def __init__(self, data, options={}):
        # execute previous step
        super().__init__(data, options)

        # initation topology items
        self.simplified = False

        # execute main function of Hashmap
        self.output = self.hashmapper(self.output)

    def __repr__(self):
        return "Hashmap(\n{}\n)".format(pprint.pformat(self.output))

    def to_dict(self):
        topo_object = copy.copy(self.output)
        topo_object["options"] = vars(topo_object["options"])
        return topo_object

    def to_svg(self, separate=False, include_junctions=False):
        serialize_as_svg(self.output, separate, include_junctions)

    def to_json(self, fp=None):
        topo_object = copy.copy(self.output)
        topo_object["options"] = vars(topo_object["options"])
        return serialize_as_json(topo_object, fp)

    def to_alt(
        self,
        mesh=True,
        color=None,
        tooltip=True,
        projection="identity",
        objectname="data",
    ):
        topo_object = copy.copy(self.output)
        del topo_object["options"]
        return serialize_as_altair(
            topo_object, mesh, color, tooltip, projection, objectname
        )

    def hashmapper(self, data):
        """
        Hashmap function resolves bookkeeping results to object arcs.

        The hashmap function is the fifth step in the topology computation.
        The following sequence is adopted:
        1. extract
        2. join
        3. cut
        4. dedup
        5. hashmap

        Developping Notes:
        * PostGIS Tips for Power Users: http://2010.foss4g.org/presentations/3369.pdf
        """

        # make data available within class
        self.data = data

        # resolve bookkeeping to arcs in objects, including backward check of arcs
        # resolve bookkeeping of coordinates in objects, including delta-encodig
        list(self.resolve_objects(["arcs", "coordinates"], self.data["objects"]))

        objects = {}
        objects["geometries"] = []
        objects["type"] = "GeometryCollection"
        for feature in data["objects"]:
            feat = data["objects"][feature]

            if "geometries" in feat and len(feat["geometries"]) == 1:
                feat["type"] = feat["geometries"][0]["type"]

            self.resolve_arcs(feat)

            objects["geometries"].append(feat)

        data["objects"] = {}
        data["objects"]["data"] = objects

        # prepare to return object
        data = self.data
        del data["junctions"]
        del data["bookkeeping_geoms"]
        del data["bookkeeping_coords"]
        del data["bookkeeping_duplicates"]
        del data["bookkeeping_arcs"]
        del data["bookkeeping_shared_arcs"]

        return data

    def hash_order(self, arc_ids, shared_bool):
        """
        create a decision list with the following options:
        0 - skip the array
        1 - follow the order of the first arc
        2 - follow the order of the last arc
        3 - align first two arcs and continue

        Parameters
        ----------
        arc_ids : list
            list containing the index values of the arcs
        shared_bool : list
            boolean list with same length as arc_ids,
            True means the arc is shared, False means it is a non-shared arc

        Returns
        -------
        order_of_arc : numpy array
            array containg values if first or last arc should be used to order
        split_arc_ids : list of numpy arrays
            array containing splitted arc ids
        """

        # first split it by the boolean shared arcs
        split_arc_ids = np.split(arc_ids, np.nonzero(~shared_bool)[0])
        split_boolean = np.split(shared_bool, np.nonzero(~shared_bool)[0])

        order_of_arc = [None] * len(split_boolean)
        # no need for iterations if split_boolean contains only 1 array
        if len(split_boolean) == 1:
            # happens when the geom only contains shared arcs,  its impossible to guess
            # the direction of the geometry, so align the first two arcs and continue
            # from there
            order_of_arc[0] = 3

        else:
            # check each splitted geom to decide how to treat
            for idx, split_geom in enumerate(split_boolean):
                if len(split_geom) == 0:
                    # skip when the array is empty
                    order_of_arc[idx] = 0

                elif len(split_geom) != 0 and split_geom.sum() == 0:
                    # skip when the splitted geom contains only non-shared arcs
                    order_of_arc[idx] = 0

                elif len(split_geom) != 0 and split_geom.sum() == len(split_geom):
                    # happens when the first splitted geom contains only shared arcs
                    # but the first arc of next splitted geom contains a non-shared arc
                    # lets take that one, and follow the order of the last arc
                    next_arc = split_arc_ids[idx + 1][0]
                    split_arc_ids[idx] = np.append(split_arc_ids[idx], next_arc)
                    order_of_arc[idx] = 2

                else:
                    # len(split_geom) > 1 and split_geom.sum() != len(split_geom):
                    order_of_arc[idx] = 1

        return order_of_arc, split_arc_ids

    def backward_arcs(self, arc_ids):
        """
        Function to check if the shared arcs in geom should be backward.
        If so, are written as -(index+1)

        Parameters
        ----------
        arc_ids : list
            description of input

        Returns
        -------
        arc_ids : list
            description of output
        """

        shared_bool = np.isin(arc_ids, self.data["bookkeeping_shared_arcs"])
        order_of_arc, split_arc_ids = self.hash_order(arc_ids, shared_bool)

        for idx_outer, split_arc in enumerate(split_arc_ids):
            order = order_of_arc[idx_outer]

            # if order is 0 can skip the split_arc
            # if order is 1 should follow order of the first arc
            # if order is 2 should follow order of the last arc
            # if order is 3 align first two arcs and continue
            if order == 0:
                continue

            if order == 2:
                split_arc = split_arc[::-1]

            previous_arc_backwards = False
            for idx, arc_idx in enumerate(split_arc):
                if idx == 0:
                    continue

                # seems previous run can influence next run
                arc_idx_prev = split_arc[idx - 1]
                if arc_idx_prev < 0:
                    arc_idx_prev = abs(arc_idx_prev) - 1

                current_arc = self.data["linestrings"][arc_idx]
                previous_arc = self.data["linestrings"][arc_idx_prev]

                # get first and last coordinate of current and previous arc
                coord_f = [current_arc.xy[0][0], current_arc.xy[1][0]]
                coord_l = [current_arc.xy[0][-1], current_arc.xy[1][-1]]

                if not previous_arc_backwards:
                    coords_prev = [
                        [previous_arc.xy[0][0], previous_arc.xy[1][0]],
                        [previous_arc.xy[0][-1], previous_arc.xy[1][-1]],
                    ]
                else:
                    coords_prev = [
                        [previous_arc.xy[0][-1], previous_arc.xy[1][-1]],
                        [previous_arc.xy[0][0], previous_arc.xy[1][0]],
                    ]
                coord_f_prev = coords_prev[0]
                coord_l_prev = coords_prev[1]

                # order 1, compare last coordinate of previous arc with first coordinate
                # of current arc. If not equal, rotate current arc
                if order == 1:
                    if not np.array_equiv(coord_l_prev, coord_f):
                        split_arc[idx] = -(arc_idx + 1)
                        previous_arc_backwards = True
                    else:
                        previous_arc_backwards = False

                # order 2, since the list is reversed, have to check first coordinate
                # of previous arc with the last coordinate of current arc. If not equal
                # rotate current arc.
                elif order == 2:
                    if not np.array_equiv(coord_f_prev, coord_l):
                        split_arc[idx] = -(arc_idx + 1)
                        previous_arc_backwards = True
                    else:
                        previous_arc_backwards = False

                elif order == 3:
                    if np.array_equiv(coord_f_prev, coord_l) and not np.array_equiv(
                        coord_l_prev, coord_f
                    ):
                        split_arc[idx - 1] = -(arc_idx_prev + 1)
                        split_arc[idx] = -(arc_idx + 1)
                        previous_arc_backwards = True
                    elif np.array_equiv(coord_f, coord_f_prev):
                        split_arc[idx - 1] = -(arc_idx_prev + 1)
                        previous_arc_backwards = False
                    elif not np.array_equiv(coord_l_prev, coord_f):
                        split_arc[idx] = -(arc_idx + 1)
                        previous_arc_backwards = True
                    else:
                        previous_arc_backwards = False

            if order == 2:
                split_arc_ids[idx_outer] = split_arc[::-1]

        comb_arc_ids = np.concatenate(split_arc_ids).flatten()
        _, idx_arcs = np.unique(comb_arc_ids, return_index=True)
        arc_ids = comb_arc_ids[np.sort(idx_arcs)].tolist()

        if order == 3:
            # since alignment is done based on the first two arcs, need a double-check
            # if it follows the required order of the ring
            if self.inner and self.options.winding_order == "CCW_CW":
                need_ccw = False
            elif not self.inner and (
                self.options.winding_order == "CW_CCW"
                or self.options.winding_order is None
            ):
                need_ccw = False
            else:
                need_ccw = True

            arc_ids = self.resolve_orient(arc_ids, need_ccw)

        return arc_ids

    def resolve_orient(self, arcs_idx_geom, need_ccw):
        arcs_geom = []
        for arc_idx in arcs_idx_geom:
            if arc_idx < 0:
                arc = copy.copy(self.data["linestrings"][~arc_idx])
                arc.coords = list(arc.coords)[::-1]
                arcs_geom.append(arc)
            else:
                arc = self.data["linestrings"][arc_idx]
                arcs_geom.append(arc)
        lring = geometry.LinearRing(linemerge(arcs_geom))

        if is_ccw(lring) != need_ccw:
            arcs_idx_geom = (np.array(arcs_idx_geom) * -1 - 1).tolist()

        return arcs_idx_geom

    def resolve_bookkeeping(self, geoms, key):
        """
        Function that is activated once the key of interest in the find_arcs function
        is detected. It replaces the geom ids with the corresponding arc ids.
        """

        if key == "arcs":
            bk_objects = "bookkeeping_geoms"
            bk_element = "bookkeeping_arcs"
        elif key == "coordinates":
            bk_objects = bk_element = "bookkeeping_coords"

        arcs = []
        for geom in geoms:
            arcs_in_geom = self.data[bk_objects][geom]
            for idx_arc, arc_ref in enumerate(arcs_in_geom):
                arc_ids = self.data[bk_element][arc_ref]
                if len(arc_ids) > 1 and key is not "coordinates":
                    self.inner = True if idx_arc > 0 else False
                    arc_ids = self.backward_arcs(arc_ids)

                arcs.append(arc_ids)
        return arcs

    def resolve_objects(self, keys, dictionary):
        """
        Function that resolves the bookkeeping back to the arcs in the objects.
        Support also nested dicts such as GeometryCollections
        """

        for k, v in dictionary.items():
            # resolve when key equals 'arcs' and v contains arc indici
            if str(k) in keys and v is not None:
                dictionary[k] = self.resolve_bookkeeping(v, k)
                yield v
            elif isinstance(v, dict):
                for result in self.resolve_objects(keys, v):
                    yield result
            elif isinstance(v, list):
                for d in v:
                    for result in self.resolve_objects(keys, d):
                        yield result

    def resolve_arcs(self, feat):
        """
        Function that resolves the arcs based on the type of the feature
        """
        if feat["type"] == "LineString":
            f_arc = feat["arcs"][0]
            feat["arcs"] = f_arc

        elif feat["type"] == "Polygon":
            if "geometries" in feat:
                f_arc = feat["geometries"][0]["arcs"]
            else:
                f_arc = feat["arcs"]

            feat["arcs"] = f_arc
            feat.pop("geometries", None)

        elif feat["type"] == "MultiPolygon":
            if "geometries" in feat:
                f_arcs = feat["geometries"][0]["arcs"]
            else:
                f_arcs = feat["arcs"]
            feat["arcs"] = [[arc] for arc in f_arcs]
            feat.pop("geometries", None)

        elif feat["type"] == "GeometryCollection":
            feat["geometries"] = [
                self.resolve_arcs(feat) for feat in feat["geometries"]
            ]

        elif feat["type"] == "Point":
            if "geometries" in feat:
                f_arc = feat["geometries"][0]["coordinates"]
            else:
                f_arc = feat["coordinates"]

            feat["coordinates"] = f_arc
            feat.pop("geometries", None)

        elif feat["type"] == "MultiPoint":
            if "geometries" in feat:
                f_arcs = feat["geometries"][0]["coordinates"]
            else:
                f_arcs = feat["coordinates"]
            feat["coordinates"] = [[arc] for arc in f_arcs]
            feat.pop("geometries", None)

        return feat
