import numpy as np
from itertools import compress
from simplification import cutil
import copy


class Hashmap:
    """
    dedup duplicates and merge contiguous arcs
    """

    def __init__(self):
        # initation topology items
        self.simp = False

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

        return arc_ids

    def resolve_bookkeeping(self, geoms):
        """
        Function that is activated once the key of interest in the find_arcs function
        is detected. It replaces the geom ids with the corresponding arc ids.
        """

        arcs = []
        for geom in geoms:
            arcs_in_geom = self.data["bookkeeping_geoms"][geom]
            for arc_ref in arcs_in_geom:
                arc_ids = self.data["bookkeeping_arcs"][arc_ref]
                if len(arc_ids) > 1:
                    # print('detect backwards if shared arcs: {}'.format(arc_ids))
                    arc_ids = self.backward_arcs(arc_ids)

                arcs.append(arc_ids)
        return arcs

    def resolve_objects(self, key, dictionary):
        """
        Function that resolves the bookkeeping back to the arcs in the objects.
        Support also nested dicts such as GeometryCollections
        """

        for k, v in dictionary.items():
            # resolve when key equals 'arcs' and v contains arc indici
            if k == key and v is not None:
                dictionary[key] = self.resolve_bookkeeping(v)
                yield v
            elif isinstance(v, dict):
                for result in self.resolve_objects(key, v):
                    yield result
            elif isinstance(v, list):
                for d in v:
                    for result in self.resolve_objects(key, d):
                        yield result

    def main(self, data, simplify_factor=None):
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
        list(self.resolve_objects("arcs", self.data["objects"]))

        # parse the linestrings into list of coordinates
        # only if linestrings are quantized, apply delta encoding.
        if "transform" in data.keys():
            if simplify_factor is not None:
                if simplify_factor >= 1:
                    for idx, ls in enumerate(data["linestrings"]):
                        self.data["linestrings"][idx] = cutil.simplify_coords(
                            np.array(ls), simplify_factor
                        )
                    self.simp = True

            for idx, ls in enumerate(data["linestrings"]):
                if self.simp:
                    ls = ls.astype(int)
                else:
                    ls = np.array(ls).astype(int)
                ls_p1 = copy.copy(ls[0])
                ls -= np.roll(ls, 1, axis=0)
                ls[0] = ls_p1
                self.data["linestrings"][idx] = ls.tolist()

        else:
            if simplify_factor is not None:
                print("xxx")
                if simplify_factor >= 1:
                    for idx, ls in enumerate(data["linestrings"]):
                        self.data["linestrings"][idx] = cutil.simplify_coords(
                            np.array(ls), simplify_factor
                        ).tolist()
            else:
                for idx, ls in enumerate(data["linestrings"]):
                    self.data["linestrings"][idx] = np.array(ls).tolist()

        objects = {}
        objects["geometries"] = []
        objects["type"] = "GeometryCollection"
        for idx, feature in enumerate(data["objects"]):
            feat = data["objects"][feature]

            if "geometries" in feat:
                feat["type"] = feat["geometries"][0]["type"]

            if feat["type"] == "Polygon":
                if "geometries" in feat:
                    f_arc = feat["geometries"][0]["arcs"]
                else:
                    f_arc = feat["arcs"]

                feat["arcs"] = f_arc

            if feat["type"] == "MultiPolygon":
                if "geometries" in feat:
                    f_arcs = feat["geometries"][0]["arcs"]
                else:
                    f_arcs["arcs"]
                feat["arcs"] = [[arc] for arc in f_arcs]

            feat.pop("geometries", None)
            objects["geometries"].append(feat)

        data["objects"] = {}
        data["objects"]["data"] = objects

        # prepare to return object
        data = self.data
        data["arcs"] = data["linestrings"]
        del data["linestrings"]
        del data["junctions"]
        del data["bookkeeping_geoms"]
        del data["bookkeeping_duplicates"]
        del data["bookkeeping_arcs"]
        del data["bookkeeping_shared_arcs"]

        return data


def hashmap(data, simplify_factor=None):
    data = copy.deepcopy(data)
    hashmapper = Hashmap()
    return hashmapper.main(data, simplify_factor)
