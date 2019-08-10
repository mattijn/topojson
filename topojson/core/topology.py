import pprint
import json
import copy
import numpy as np
from .hashmap import Hashmap
from ..ops import properties_foreign
from ..ops import np_array_from_arcs
from ..ops import dequantize
from ..ops import quantize
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

    def topoquantize(self, quant_factor, inplace=False):
        result = copy.deepcopy(self)
        arcs = result.output["arcs"]

        # dequantize if quantization is applied
        if "transform" in result.output.keys():
            np_arcs = np_array_from_arcs(arcs)

            transform = result.output["transform"]
            scale = transform["scale"]
            translate = transform["translate"]

            np_arcs = dequantize(np_arcs, scale, translate)
            l_arcs = []
            for ls in np_arcs:
                l_arcs.append(ls[~np.isnan(ls)[:, 0]].tolist())
            arcs = l_arcs

        arcs_qnt, transform = quantize(arcs, result.output["bbox"], quant_factor)

        result.output["arcs"] = delta_encoding(arcs_qnt)
        result.output["transform"] = transform
        result.options.topoquantize = quant_factor

        if inplace:
            # update into self
            self = result
        else:
            return result

    def toposimplify(self, epsilon, _input_as="array", inplace=False):
        result = copy.deepcopy(self)

        arcs = result.output["arcs"]
        np_arcs = np_array_from_arcs(arcs)

        # dequantize if quantization is applied
        if "transform" in result.output.keys():

            transform = result.output["transform"]
            scale = transform["scale"]
            translate = transform["translate"]

            np_arcs = dequantize(np_arcs, scale, translate)

        result.output["arcs"] = simplify(
            np_arcs, epsilon, package=result.options.simplifypackage, input_as=_input_as
        )

        # quantize aqain if quantization was applied
        if "transform" in result.output.keys():
            if result.options.topoquantize > 0:
                # set default if not specifically given in the options
                if type(result.options.topoquantize) == bool:
                    quant_factor = 1e6
                else:
                    quant_factor = result.options.topoquantize
            elif result.options.prequantize > 0:
                # set default if not specifically given in the options
                if type(result.options.prequantize) == bool:
                    quant_factor = 1e6
                else:
                    quant_factor = result.options.prequantize

            result.output["arcs"], transform = quantize(
                result.output["arcs"], result.output["bbox"], quant_factor
            )
            result.output["arcs"] = delta_encoding(result.output["arcs"])
            result.output["transform"] = transform
        if inplace:
            # update into self
            self = result
        else:
            return result

    def topologic(self, data):
        self.output["arcs"] = data["linestrings"]

        # apply delta-encoding if prequantization is applied
        if self.options.prequantize > 0:
            self.output["arcs"] = delta_encoding(self.output["arcs"])
        else:
            for idx, ls in enumerate(self.output["arcs"]):
                self.output["arcs"][idx] = np.array(ls).tolist()

        # toposimplify linestrings if required
        if self.options.toposimplify > 0:
            # set default if not specifically given in the options
            if type(self.options.toposimplify) == bool:
                simplify_factor = 2
            else:
                simplify_factor = self.options.toposimplify

            self.toposimplify(epsilon=simplify_factor, _input_as="array", inplace=True)

        return self.output
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

