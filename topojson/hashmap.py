import numpy as np
from itertools import compress
import copy


class _Hashmap:
    """
    dedup duplicates and merge contiguous arcs
    """

    def __init__(self):
        # initation topology items
        pass

    def backward_arcs(self, arc_ids):
        """
        Function to check if the shared arcs in geom should be backward.
        If so, are written as -(index+1)
        """

        boolean_shared_arcs = np.isin(self.data["bookkeeping_shared_arcs"], arc_ids)
        shared_arcs_in_geom = list(
            compress(self.data["bookkeeping_shared_arcs"], boolean_shared_arcs)
        )

        for arc_idx in shared_arcs_in_geom:
            arc_idxs = [idx for idx, val in enumerate(arc_ids) if val == arc_idx]
            arc_idxs_next = [x + 1 for x in arc_idxs]
            arc_idxs_prev = [x - 1 for x in arc_idxs]

            for idx, arc in enumerate(arc_idxs):
                # print(arc)
                # print(idx)
                # print(arc_idxs_next[idx])
                shrd_arc_idx = arc_ids[arc]
                shrd_arc = self.data["linestrings"][shrd_arc_idx]

                try:
                    # get next arc in geom
                    next_arc_idx = arc_idxs_next[idx]
                    # print(next_arc_idx)
                    next_arc = self.data["linestrings"][arc_ids[next_arc_idx]]
                except IndexError:
                    # no next arc in geom, get previous arc
                    next_arc = None
                    prev_arc_idx = arc_idxs_prev[idx]
                    prev_arc = self.data["linestrings"][arc_ids[prev_arc_idx]]

                if next_arc:
                    # check last value of shrd_idx and first value of next_idx
                    # print('n')
                    coord_shrd_last = np.array(shrd_arc.xy)[:, -1]
                    coord_next_first = np.array(next_arc.xy)[:, 0]
                    # print(coord_shrd_last, coord_next_first)
                    if not np.array_equiv(coord_shrd_last, coord_next_first):
                        # shrd_arc should be backwards
                        arc_ids[arc] = -(arc_ids[arc] + 1)
                else:
                    # check first value of shrd_idx and last value prev_idx
                    # print('p')
                    coord_shrd_first = np.array(shrd_arc.xy)[:, 0]
                    coord_prev_last = np.array(prev_arc.xy)[:, -1]
                    if not np.array_equiv(coord_shrd_first, coord_prev_last):
                        # shrd_arc should be backwards
                        arc_ids[arc] = -(arc_ids[arc] + 1)

        return arc_ids

    def resolve_bookkeeping(self, geoms):
        """
        Function that is activated once the key of interest in the find_arcs functino is detected.
        It replaces the geom ids with the corresponding arc ids.
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

    def main(self, data):
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
        * ..
        """

        # make data available within class
        self.data = data

        # resolve bookkeeping to arcs in objects, including backward check of arcs
        list(self.resolve_objects("arcs", self.data["objects"]))

        # parse the linestrings into list of coordinates
        for idx, ls in enumerate(data["linestrings"]):
            self.data["linestrings"][idx] = np.array(ls.xy).T.tolist()

        # prepare to return object
        data = self.data
        data["arcs"] = data["linestrings"]
        del data["linestrings"]
        del data["bookkeeping_geoms"]
        del data["bookkeeping_duplicates"]
        del data["junctions"]
        del data["bookkeeping_arcs"]
        del data["bookkeeping_shared_arcs"]

        return data


def _hashmapper(data):
    data = copy.deepcopy(data)
    Hashmap = _Hashmap()
    h = Hashmap.main(data)
    return h
