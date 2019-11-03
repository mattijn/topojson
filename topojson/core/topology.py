import pprint
import copy
import numpy as np
import itertools
from .hashmap import Hashmap
from ..ops import properties_foreign
from ..ops import np_array_from_arcs
from ..ops import dequantize
from ..ops import quantize
from ..ops import simplify
from ..ops import delta_encoding
from ..utils import TopoOptions
from ..utils import serialize_as_svg
from ..utils import serialize_as_json


class Topology(Hashmap):
    """
    Returns a TopoJSON topology for the specified geometric object.
    TopoJSON is an extension of GeoJSON providing multiple approaches
    to compress the geographical input data. These options include
    simplifying the linestrings or quantizing the coordinates but
    foremost the computation of a topology.

    Parameters
    ----------
    data : _any_ geometric type
        Geometric data that should be converted into TopoJSON
    topology : boolean
        Specifiy if the topology should be computed for deriving the
        TopoJSON.
        Default is True.
    prequantize : boolean or int
        If the prequantization parameter is specified, the input geometry
        is quantized prior to computing the topology, the returned
        topology is quantized, and its arcs are delta-encoded.
        Quantization is recommended to improve the quality of the topology
        if the input geometry is messy (i.e., small floating point error
        means that adjacent boundaries do not have identical values);
        typical values are powers of ten, such as 1e4, 1e5 or 1e6.
        Default is True (which correspond to a quantize factor of 1e6).
    topoquantize : boolean or int
        If the topoquantization parameter is specified, the input geometry
        is quantized after the topology is constructed. If the topology is
        already quantized this will be resolved first before the
        topoquantization is applied.
        Default is False.
    presimplify : boolean or float
        Apply presimplify to remove unnecessary points from linestrings
        before the topology is constructed. This will simplify the input
        geometries.
        Default is False.
    toposimplify : boolean or float
        Apply toposimplify to remove unnecessary points from arcs after
        the topology is constructed. This will simplify the constructed
        arcs without altering the topological relations. Sensible values
        are in the range of 0.0001 to 10.
        Defaults to 0.0001.
    simplify_with : str
        Sets the package to use for simplifying (both pre- and
        toposimplify). Choose between `shapely` or `simplification`.
        Shapely adopts solely Douglas-Peucker and simplification both
        Douglas-Peucker and Visvalingam-Whyatt. The pacakge simplification
        is known to be quicker than shapely.
        Default is "shapely".
    simplify_algorithm : str
        Choose between 'dp' and 'vw', for Douglas-Peucker or Visvalingam-
        Whyatt respectively. 'vw' will only be selected if `simplify_with`
        is set to `simplification`.
        Default is `dp`, since it still "produces the most accurate
        generalization" (Chi & Cheung, 2006).
    winding_order : str
        Determines the winding order of the features in the output
        geometry. Choose between `CW_CCW` for clockwise orientation for
        outer rings and counter-clockwise for interior rings. Or `CCW_CW`
        for counter-clockwise for outer rings and clockwise for interior
        rings.
        Default is `CW_CCW`.
    """

    def __init__(
        self,
        data,
        topology=True,
        prequantize=True,
        topoquantize=False,
        presimplify=False,
        toposimplify=0.0001,
        simplify_with="shapely",
        simplify_algorithm="dp",
        winding_order="CW_CCW",
    ):

        options = TopoOptions(locals())
        # execute previous steps
        super().__init__(data, options)

        # execute main function of Topology
        self.output = self.worker(self.output)

    def __repr__(self):
        return "Topology(\n{}\n)".format(pprint.pformat(self.output))

    def to_dict(self):
        topo_object = copy.deepcopy(self.output)
        topo_object = self.resolve_coords(topo_object)
        topo_object["options"] = vars(topo_object["options"])
        return topo_object

    def to_svg(self, separate=False, include_junctions=False):
        serialize_as_svg(self.output, separate, include_junctions)

    def to_json(self, fp=None):
        topo_object = copy.deepcopy(self.output)
        topo_object = self.resolve_coords(topo_object)
        topo_object["options"] = vars(topo_object["options"])
        return serialize_as_json(topo_object, fp)

    def to_gdf(self):
        from ..utils import serialize_as_geodataframe

        topo_object = copy.deepcopy(self.output)
        topo_object = self.resolve_coords(topo_object)
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
        from ..utils import serialize_as_altair

        topo_object = copy.deepcopy(self.output)
        topo_object = self.resolve_coords(topo_object)
        del topo_object["options"]
        return serialize_as_altair(
            topo_object, mesh, color, tooltip, projection, objectname
        )

    def to_widget(
        self,
        slider_toposimplify={"min": 0, "max": 10, "step": 0.01, "value": 0.01},
        slider_topoquantize={"min": 1, "max": 6, "step": 1, "value": 1e5, "base": 10},
    ):

        from ..utils import serialize_as_ipywidgets

        return serialize_as_ipywidgets(
            topo_object=self,
            toposimplify=slider_toposimplify,
            topoquantize=slider_topoquantize,
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
        if arcs:
            np_arcs = np_array_from_arcs(arcs)

            # dequantize if quantization is applied
            if "transform" in result.output.keys():

                transform = result.output["transform"]
                scale = transform["scale"]
                translate = transform["translate"]

                np_arcs = dequantize(np_arcs, scale, translate)

            result.output["arcs"] = simplify(
                np_arcs,
                epsilon,
                algorithm=result.options.simplify_algorithm,
                package=result.options.simplify_with,
                input_as=_input_as,
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

            result.output["coordinates"], transform = quantize(
                result.output["coordinates"], result.output["bbox"], quant_factor
            )

            result.output["arcs"] = delta_encoding(result.output["arcs"])
            result.output["transform"] = transform
        if inplace:
            # update into self
            self.output["arcs"] = result.output["arcs"]
            if "transform" in result.output.keys():
                self.output["transform"] = result.output["transform"]
            # self.output["arcs"] = result.output["arcs"]
            # self.output["transform"] = result.output["transform"]
        else:
            return result

    def resolve_coords(self, data):
        geoms = data["objects"]["data"]["geometries"]
        for idx, feat in enumerate(geoms):
            if feat["type"] in ["Point", "MultiPoint"]:

                lofl = feat["coordinates"]
                repeat = 1 if feat["type"] == "Point" else 2

                for _ in range(repeat):
                    lofl = list(itertools.chain(*lofl))

                for idx, val in enumerate(lofl):
                    coord = data["coordinates"][val]
                    lofl[idx] = [int(coord.xy[0][0]), int(coord.xy[1][0])]

                feat["coordinates"] = lofl[0] if len(lofl) == 1 else lofl
                feat.pop("reset_coords", None)
        data.pop("coordinates", None)
        return data

    def worker(self, data):
        self.output["arcs"] = data["linestrings"]
        del data["linestrings"]

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
                simplify_factor = 0.0001
            else:
                simplify_factor = self.options.toposimplify

            self.toposimplify(epsilon=simplify_factor, _input_as="array", inplace=True)

        return self.output
