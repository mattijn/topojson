import pprint
import json
import copy
import numpy as np
from .hashmap import Hashmap
from ..ops import properties_foreign
from ..ops import simplify
from ..ops import delta_encoding
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

        # execute main function of Topology
        self.output = self.topologic(self.output)

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

    def flatten_properties(self):
        objects = self.output["objects"]["data"]["geometries"]
        if objects:
            objects = properties_foreign(objects)
            self.output["objects"]["data"]["geometries"] = objects

    def topologic(self, data):

        # toposimplify linestrings if required
        if self.options.toposimplify > 0:
            # set default if not specifically given in the options
            if type(self.options.toposimplify) == bool:
                simplify_factor = 2
            else:
                simplify_factor = self.options.toposimplify

            data["linestrings"] = simplify(
                data["linestrings"], simplify_factor, package="shapely"
            )

        # apply delta-encoding if prequantization is applied
        if self.options.prequantize > 0:
            self.data["linestrings"] = delta_encoding(data["linestrings"])
        else:
            for idx, ls in enumerate(data["linestrings"]):
                self.data["linestrings"][idx] = np.array(ls).tolist()

        data["arcs"] = data["linestrings"]
        del data["linestrings"]

        return data
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

