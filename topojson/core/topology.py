import pprint
import copy
import numpy as np
import itertools
from .hashmap import Hashmap
from ..ops import np_array_from_arcs
from ..ops import dequantize
from ..ops import quantize
from ..ops import simplify
from ..ops import delta_encoding
from ..ops import bounds
from ..ops import compare_bounds
from ..utils import TopoOptions
from ..utils import instance
from ..utils import serialize_as_svg
from ..utils import serialize_as_json
from ..utils import serialize_as_topojson
from ..utils import serialize_as_geojson


class Topology(Hashmap):
    """
    Returns a TopoJSON topology for the specified geometric object. TopoJSON is an
    extension of GeoJSON providing multiple approaches to compress the geographical
    input data. These options include simplifying the linestrings or quantizing the
    coordinates but foremost the computation of a topology.

    Parameters
    ----------
    data : _any_ geometric type
        Geometric data that should be converted into TopoJSON.
        It is possible to provide a list of multiple geopandas.GeoDataFrames as
        separate objects. In this case it is required to provide an equal length list of
        the names of the objects for parameter `object_name`.
    topology : boolean
        Specify if the topology should be computed for deriving the TopoJSON.
        Default is `True`.
    prequantize : boolean, int
        If the prequantization parameter is specified, the input geometry is
        quantized prior to computing the topology, the returned topology is
        quantized, and its arcs are delta-encoded. Quantization is recommended to
        improve the quality of the topology if the input geometry is messy (i.e.,
        small floating point error means that adjacent boundaries do not have
        identical values); typical values are powers of ten, such as `1e4`, `1e5` or
        `1e6`.
        Default is `True` (which correspond to a quantize factor of `1e5`).
    topoquantize : boolean or int
        If the topoquantization parameter is specified, the input geometry is quantized
        after the topology is constructed. If the topology is already quantized this
        will be resolved first before the topoquantization is applied. See for more
        details the `prequantize` parameter.
        Default is `False`.
    presimplify : boolean, float
        Apply presimplify to remove unnecessary points from linestrings before the
        topology is constructed. This will simplify the input geometries. Use with care.
        Default is `False`.
    toposimplify : boolean, float
        Apply toposimplify to remove unnecessary points from arcs after the topology
        is constructed. This will simplify the constructed arcs without altering the
        topological relations. Sensible values for coordinates stored in degrees are
        in the range of `0.0001` to `10`.
        Defaults to `False`.
    shared_coords : boolean
        Sets the strategy to detect junctions. When set to `False` a path is considered
        shared when coordinates are the same path (`path-connected`). The path-connected
        strategy is more 'correct', but slightly slower. When set to `True` a path is
        considered shared when all coordinates appear in both paths
        (`coords-connected`).
        Default is `False`.
    prevent_oversimplify: boolean
        If this setting is set to `True`, the simplification is slower, but the
        likelihood of producing valid geometries is higher as it prevents
        oversimplification. Simplification happens on paths separately, so this
        setting is especially relevant for rings with no partial shared paths. This
        is also known as a topology-preserving variant of simplification.
        Default is `True`.
    simplify_with : str
        Sets the package to use for simplifying (both pre- and toposimplify). Choose
        between `shapely` or `simplification`. Shapely adopts solely Douglas-Peucker
        and simplification both Douglas-Peucker and Visvalingam-Whyatt. The package
        simplification is known to be quicker than shapely.
        Default is `shapely`.
    simplify_algorithm : str
        Choose between `dp` and `vw`, for Douglas-Peucker or Visvalingam-Whyatt
        respectively. `vw` will only be selected if `simplify_with` is set to
        `simplification`.
        Default is `dp`.
    winding_order : str
        Determines the winding order of the features in the output geometry. Choose
        between `CW_CCW` for clockwise orientation for outer rings and counter-
        clockwise for interior rings. Or `CCW_CW` for counter-clockwise for outer
        rings and clockwise for interior rings.
        Default is `CW_CCW` for TopoJSON.
    object_name : Union[str, list[str]]
        Name to use as key for the objects in the topojson file. This name is used for
        writing and reading topojson file formats.
        It is possible to define multiple objects within the topojson file. In this
        case it is required to provide a list of the referenced `object_name` in
        combination with an equal length list of `data` objects.
        Default is a single object named `data`.
    ignore_index : bool
        If set to true existing ids/indexes of geojson FeatureCollections will be
        ignored and overwritten. Otherwise features with ids will use their existing one.
        If indexes are not ignored and a duplicate id exists an exception will be raised.
        Default is false.
    """

    def __init__(
        self,
        data,
        topology=True,
        prequantize=True,
        topoquantize=False,
        presimplify=False,
        toposimplify=False,
        shared_coords=False,
        prevent_oversimplify=True,
        simplify_with="shapely",
        simplify_algorithm="dp",
        winding_order="CW_CCW",
        object_name="data",
        ignore_index=False,
    ):
        options = TopoOptions(locals())

        # shortcut when dealing with topojson data
        if (
            instance(data) == "dict"
            and "type" in data.keys()
            and data["type"].casefold() == "Topology".casefold()
        ):
            self.output, self.options = serialize_as_topojson(data, options)

        # all others follow normal route
        else:
            # execute previous steps
            super().__init__(data, options)

        # execute main function of Topology
        self.output = self._topo(self.output)

    def __repr__(self):
        return "Topology(\n{}\n)".format(pprint.pformat(self.output))

    @property
    def __geo_interface__(self):
        topo_object = copy.deepcopy(self.output)
        objectname = self._resolve_object_name(0)
        return serialize_as_geojson(topo_object, validate=False, objectname=objectname)

    def to_dict(self, options=False):
        """
        Convert the Topology to a dictionary.

        Parameters
        ----------
        options : boolean
            If `True`, the options also will be included.
            Default is `False`
        """
        topo_object = copy.deepcopy(self.output)
        topo_object = self._resolve_coords(topo_object)
        if options:
            topo_object["options"] = vars(self.options)
        else:
            topo_object.pop("options", None)
        return topo_object

    def to_svg(self, separate=False):
        """
        Display the arcs and junctions as SVG.

        Parameters
        ----------
        separate : boolean
            If `True`, each of the arcs will be displayed separately.
            Default is `False`
        """
        serialize_as_svg(self.output, separate, include_junctions=False)

    def to_json(self, fp=None, options=False, pretty=False, indent=4, maxlinelength=88):
        """
        Convert the Topology to a JSON object.

        Parameters
        ----------
        fp : str
            If set, writes the object to a file on drive.
            Default is `None`.
        options : boolean
            If `True`, the options also will be included.
            Default is `False`.
        pretty : boolean
            If `pretty=True`, the JSON object will be 'pretty', depending on the
            `ident` and `maxlinelength` options. If `pretty=False`, it will `compact`,
            eliminating whitespace.
            Default is `False`.
        indent : int
            If `style='pretty'`, declares the indentation of the objects.
            Default is `4`.
        maxlinelength : int
            If `style='pretty'`, declares the maximum length of each line.
            Default is `88`.
        """
        topo_object = copy.deepcopy(self.output)
        topo_object = self._resolve_coords(topo_object)

        if options is True:
            topo_object["options"] = vars(self.options)
        else:
            topo_object.pop("options", None)
        return serialize_as_json(
            topo_object, fp, pretty=pretty, indent=indent, maxlinelength=maxlinelength
        )

    def to_geojson(
        self,
        fp=None,
        pretty=False,
        indent=4,
        maxlinelength=88,
        validate=False,
        winding_order="CCW_CW",
        decimals=None,
        object_name=0,
    ):
        """
        Convert the Topology to a GeoJSON object. Remember that this will destroy the
        computed Topology.

        Parameters
        ----------
        fp : str
            If set, writes the object to a file on drive.
            Default is `None`
        pretty : boolean
            If `pretty=True`, the JSON object will be 'pretty', depending on the
            `ident` and `maxlinelength` options. If `pretty=False`, it will `compact`,
            eliminating whitespace.
            Default is `False`.
        indent : int
            If `pretty=True`, declares the indentation of the objects.
            Default is `4`.
        maxlinelength : int
            If `pretty=True`, declares the maximum length of each line.
            Default is `88`.
        validate : boolean
            Set to `True` to validate each feature before inclusion in the GeoJSON. Only
            features that are valid geometries objects will be included.
            Default is `False`.
        winding_order : str
            Determines the winding order of the features in the output geometry. Choose
            between `CW_CCW` for clockwise orientation for outer rings and counter-
            clockwise for interior rings. Or `CCW_CW` for counter-clockwise for outer
            rings and clockwise for interior rings.
            Default is `CCW_CW` for GeoJSON.
        decimals : int or None
            Evenly round the coordinates to the given number of decimals.
            Default is None, which means no rounding is applied.
        object_name : str, int
            The name or the index of the object within the Topology to display.
            Default is index 0.
        """
        topo_object = copy.deepcopy(self.output)
        topo_object = self._resolve_coords(topo_object)
        objectname = self._resolve_object_name(object_name)

        fc = serialize_as_geojson(
            topo_object,
            validate=validate,
            objectname=objectname,
            order=winding_order,
            decimals=decimals,
        )
        return serialize_as_json(
            fc, fp, pretty=pretty, indent=indent, maxlinelength=maxlinelength
        )

    def to_gdf(self, crs=None, validate=False, winding_order="CCW_CW", object_name=0):
        """
        Convert the Topology to a GeoDataFrame. Remember that this will destroy the
        computed Topology.

        Note: This function use not the TopoJSON driver within Fiona, but a custom
        implemented more robust variant. See for info the `to_geojson()` function.

        Parameters
        ----------
        crs : str, dict
            coordinate reference system to set on the resulting frame.
            Default tries to use crs from data-input, otherwise is `None`.
        validate : boolean
            Set to `True` to validate each feature before inclusion in the GeoJSON. Only
            features that are valid geometries objects will be included.
            Default is `False`.
        winding_order : str
            Determines the winding order of the features in the output geometry. Choose
            between `CW_CCW` for clockwise orientation for outer rings and counter-
            clockwise for interior rings. Or `CCW_CW` for counter-clockwise for outer
            rings and clockwise for interior rings.
            Default is `CCW_CW` for GeoJSON.
        object_name : str, int
            Name or index of the object.
            Default is index `0` to select the first object.
        """
        from ..utils import serialize_as_geodataframe

        topo_object = copy.deepcopy(self.output)
        topo_object = self._resolve_coords(topo_object)
        objectname = self._resolve_object_name(object_name)
        fc = serialize_as_geojson(
            topo_object, validate=validate, objectname=objectname, order=winding_order
        )

        if crs is None and hasattr(self, "_defined_crs_source"):
            crs = self._defined_crs_source
        return serialize_as_geodataframe(fc, crs=crs)

    def to_alt(self, color=None, tooltip=True, projection="identity", object_name=0):
        """
        Display as Altair visualization.

        Parameters
        ----------
        color : str
            Assign an property attribute to be used for color encoding and renders the
            Altair visualization as geoshape. Remember that most of the time the wanted
            attribute is nested within properties. Moreover, specific type declaration
            is required. Eg `color='properties.name:N'`.
            Default is `None` (render as mesh).
        tooltip : boolean
            Option to include or exclude tooltips on geoshape objects
            Default is `True`.
        projection : str
            Defines the projection of the visualization. Defaults to a non-geographic,
            Cartesian projection (known by Altair as `identity`).
        object_name : str, int
            The name or the index of the object within the Topology to display.
            Default is index 0.
        """
        from ..utils import serialize_as_altair

        topo_object = self.to_json()
        objectname = self._resolve_object_name(object_name)

        return serialize_as_altair(topo_object, color, tooltip, projection, objectname)

    def to_widget(
        self,
        slider_toposimplify={"min": 0, "max": 10, "step": 0.01, "value": 0.01},
        slider_topoquantize={"min": 1, "max": 6, "step": 1, "value": 1e5, "base": 10},
    ):
        """
        Create an interactive widget based on Altair. The widget includes sliders to
        interactively change the `toposimplify` and `topoquantize` settings.

        Parameters
        ----------
        slider_toposimplify : dict
            The dict should contain the following keys: `min`, `max`, `step`, `value`.
            Default is `{"min": 0, "max": 10, "step": 0.01, "value": 0.01}`.
        slider_topoquantize : dict
            The dict should contain the following keys: `min`, `max`, `value`, `base`.
            Default is `{"min": 1, "max": 6, "step": 1, "value": 1e5, "base": 10}`.
        """

        from ..utils import serialize_as_ipywidgets

        return serialize_as_ipywidgets(
            topo_object=self,
            toposimplify=slider_toposimplify,
            topoquantize=slider_topoquantize,
        )

    def topoquantize(self, quant_factor, inplace=False):
        """
        Quantization is recommended to improve the quality of the topology if the
        input geometry is messy (i.e., small floating point error means that
        adjacent boundaries do not have identical values); typical values are powers
        of ten, such as `1e4`, `1e5` or  `1e6`.

        Parameters
        ----------
        quant_factor : float
            tolerance parameter
        inplace : bool, optional
            If `True`, do operation inplace and return `None`.
            Default is `False`.

        Returns
        -------
        object or None
            Quantized coordinates and delta-encoded arcs if `inplace` is `False`.
        """
        result = copy.deepcopy(self)
        arcs = result.output["arcs"]

        if not arcs:
            return result

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
            lsbs = bounds(arcs)
        else:
            lsbs = bounds(arcs)

        arcs_qnt, transform = quantize(arcs, result.output["bbox"], quant_factor)
        ptbs = bounds(result.output["coordinates"])
        result.output["bbox"] = compare_bounds(lsbs, ptbs)

        result.output["arcs"] = delta_encoding(arcs_qnt)
        result.output["transform"] = transform
        result.options.topoquantize = quant_factor

        if inplace:
            # update into self
            self.output["arcs"] = result.output["arcs"]
            self.output["transform"] = result.output["transform"]
            self.options.topoquantize = result.options.topoquantize
        else:
            return result

    def toposimplify(
        self,
        epsilon,
        simplify_algorithm=None,
        simplify_with=None,
        prevent_oversimplify=None,
        inplace=False,
    ):
        """
        Apply toposimplify to remove unnecessary points from arcs after the topology
        is constructed. This will simplify the constructed arcs without altering the
        topological relations. Sensible values for coordinates stored in degrees are
        in the range of `0.0001` to `10`.

        Parameters
        ----------
        epsilon : float
            tolerance parameter.
        simplify_algorithm : str, optional
            Choose between `dp` and `vw`, for Douglas-Peucker or Visvalingam-Whyatt
            respectively. `vw` will only be selected if `simplify_with` is set to
            `simplification`.
            Default is `None`, meaning that the default (`dp`) is not overwritten.
        simplify_with : str, optional
            Sets the package to use for simplifying. Choose between `shapely` or
            `simplification`. Shapely adopts solely Douglas-Peucker and simplification
            both Douglas-Peucker and Visvalingam-Whyatt. The package simplification is
            known to be quicker than shapely.
            Default is `None`, meaning that the default (`shapely`) is not overwritten.
        prevent_oversimplify: boolean, optional
            If this setting is set to `True`, the simplification is slower, but the
            likelihood of producing valid geometries is higher as it prevents
            oversimplification. Simplification happens on paths separately, so this
            setting is especially relevant for rings with no partial shared paths. This
            is also known as a topology-preserving variant of simplification.
            Default is `None`, meaning that the default (`True`) is not overwritten.
        inplace : bool, optional
            If `True`, do operation inplace and return `None`.
            Default is `False`.

        Returns
        -------
        object or None
            Topology object with simplified linestrings if `inplace` is `False`.
        """
        result = copy.deepcopy(self)

        # set settings in options to override
        if isinstance(type(prevent_oversimplify), bool):
            result.options.prevent_oversimplify = prevent_oversimplify
        if simplify_with in ["shapely", "simplification"]:
            result.options.simplify_with = simplify_with
        if simplify_algorithm in ["dp", "vw"]:
            result.options.simplify_algorithm = simplify_algorithm

        transform = None
        # get transform settings to dequantize if necessary
        if "transform" in result.output.keys():
            transform = result.output["transform"]
            scale = transform["scale"]
            translate = transform["translate"]

        # first do the arcs
        arcs = result.output["arcs"]
        if arcs:
            np_arcs = np_array_from_arcs(arcs)

            # dequantize if transform exist
            if transform is not None:
                power_estimate = len(str(int(np_arcs[:, 0].max())))
                quant_factor_estimate = 10**power_estimate
                np_arcs = dequantize(np_arcs, scale, translate)

            # apply simplify
            result.output["arcs"] = simplify(
                np_arcs,
                epsilon,
                algorithm=result.options.simplify_algorithm,
                package=result.options.simplify_with,
                input_as="array",
                prevent_oversimplify=result.options.prevent_oversimplify,
            )

            lsbs = bounds(result.output["arcs"])
            ptbs = bounds(result.output["coordinates"])
            result.output["bbox"] = compare_bounds(lsbs, ptbs)

            # quantize again if quantization was applied
            if transform is not None:
                quant_factor = None
                if result.options.topoquantize > 0:
                    # set default if not specifically given in the options
                    if isinstance(result.options.topoquantize, bool):
                        quant_factor = 1e5
                    else:
                        quant_factor = result.options.topoquantize
                elif result.options.prequantize > 0:
                    # set default if not specifically given in the options
                    if isinstance(result.options.prequantize, bool):
                        quant_factor = 1e5
                    else:
                        quant_factor = result.options.prequantize
                else:
                    # no options set, use the guessed estimate from input data
                    quant_factor = quant_factor_estimate

                # apply quantization and delta encode result.
                result.output["arcs"], transform = quantize(
                    result.output["arcs"], result.output["bbox"], quant_factor
                )
                result.output["arcs"] = delta_encoding(result.output["arcs"])
                result.output["transform"] = transform
        if inplace:
            # update into self
            self.output["arcs"] = result.output["arcs"]
            if "transform" in result.output.keys():
                self.output["transform"] = result.output["transform"]
        else:
            return result

    def _resolve_coords(self, data):
        for objectname in self.options.object_name:
            if objectname not in data["objects"]:
                raise SystemExit(
                    f"'{objectname}' is not an object name in your topojson file"
                )
            geoms = data["objects"][objectname]["geometries"]
            for idx, feat in enumerate(geoms):
                if feat["type"] in ["Point", "MultiPoint"]:
                    lofl = feat["coordinates"]
                    repeat = 1 if feat["type"] == "Point" else 2

                    for _ in range(repeat):
                        lofl = list(itertools.chain(*lofl))

                    for idx, val in enumerate(lofl):
                        coord = data["coordinates"][val][0]
                        lofl[idx] = np.asarray(coord).tolist()

                    feat["coordinates"] = lofl[0] if feat["type"] == "Point" else lofl
                    feat.pop("reset_coords", None)
            data.pop("coordinates", None)
        return data

    def _resolve_object_name(self, object_name):
        # check if object_name as str or index is within self.options.object_name
        if type(object_name) is int:
            ix = object_name
            if ix < len(self.options.object_name):
                objectname = self.options.object_name[ix]
            else:
                raise IndexError(
                    f'Cannot use object_name: "{object_name}" as index in objects: {self.options.object_name}. List index out of range'
                )
        else:
            if object_name in self.options.object_name:
                objectname = object_name
            else:
                raise LookupError(
                    f'object_name: "{object_name}" not in objects: {self.options.object_name}'
                )
        return objectname

    def _topo(self, data):
        self.output["arcs"] = data["linestrings"]
        del data["linestrings"]

        # apply delta-encoding if prequantization is applied
        if self.options.prequantize > 0:
            self.output["arcs"] = delta_encoding(self.output["arcs"])
        else:
            for idx, ls in enumerate(self.output["arcs"]):
                self.output["arcs"][idx] = ls.tolist()

        # toposimplify linestrings if required
        if self.options.toposimplify > 0:
            # set default if not specifically given in the options
            if isinstance(self.options.toposimplify, bool):
                simplify_factor = 0.0001
            else:
                simplify_factor = self.options.toposimplify

            self.toposimplify(epsilon=simplify_factor, inplace=True)

        # topoquantize linestrings if required
        if self.options.topoquantize > 0:
            # set default if not specifically given in the options
            if isinstance(self.options.topoquantize, bool):
                quant_factor = 1e5
            else:
                quant_factor = self.options.topoquantize

            self.topoquantize(quant_factor=quant_factor, inplace=True)

        return self.output
