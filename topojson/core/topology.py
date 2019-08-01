import pprint
import json
import copy
from .hashmap import Hashmap
from ..utils import serialize_as_geodataframe
from ..utils import serialize_as_svg
from ..utils import serialize_as_json
from ..utils import serialize_as_altair


class Topology(Hashmap):
    """
    dedup duplicates and merge contiguous arcs
    """

    def __init__(self, data, **kwargs):

        # execute previous steps
        super().__init__(data, **kwargs)

        # do something after hashmapping in necessary

    def __repr__(self):
        return "Topology(\n{}\n)".format(pprint.pformat(self.output))

    def to_dict(self):
        return self.output

    def to_json(self, fp=None):
        topo_object = copy.copy(self.output)
        del topo_object["options"]
        return serialize_as_json(topo_object, fp)

    def to_gdf(self):
        topo_object = copy.copy(self.output)
        del topo_object["options"]
        return serialize_as_geodataframe(topo_object)

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

        # if simplify_factor is not None:
        #     if simplify_factor >= 1:
        #         for idx, ls in enumerate(data["linestrings"]):
        #             self.data["linestrings"][idx] = cutil.simplify_coords(
        #                 np.array(ls), simplify_factor
        #             )
        #         self.simplified = True

        # else:
        # if simplify_factor is not None:
        #     if simplify_factor >= 1:
        #         for idx, ls in enumerate(data["linestrings"]):
        #             self.data["linestrings"][idx] = cutil.simplify_coords(
        #                 np.array(ls), simplify_factor
        #             ).tolist()
        # else:


# def topology(
#     data, snap_vertices=False, snap_value_gridsize=1e6, simplify=False, simplify_factor=1
# ):


#     # execute the topoloy
#     super().__init__(data)


#     # initialize classes
#     extractor = Extract()
#     joiner = Join()
#     cutter = Cut()
#     deduper = Dedup()
#     hashmapper = Hashmap()

#     # copy data
#     try:
#         data = copy.deepcopy(data)
#     except:
#         data = data.copy()

#     # apply topology to data
#     data = extractor.main(data)

#     if snap_vertices:
#         data = joiner.main(data, quant_factor=gridsize_to_snap)
#     else:
#         data = joiner.main(data, quant_factor=None)

#     data = cutter.main(data)
#     data = deduper.main(data)
#     if simplify:
#         data = hashmapper.main(data, simplify_factor=simplify_factor)
#     else:
#         data = hashmapper.main(data, simplify_factor=None)

#     return data

