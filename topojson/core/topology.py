import copy
import hashlib
import itertools
import json
import os
import pprint
from collections.abc import Hashable, Iterable
from typing import IO, TYPE_CHECKING, Any, Literal, Self, cast, overload

import numpy as np

from .._types import Algorithm, Package, Quantize, Slider, Transform, WindingOrder
from ..ops import (
    arc_areas,
    arc_coordinates,
    bounds,
    compare_bounds,
    delta_encoding,
    quantize,
    restore_collapsed_rings,
    simplify,
    simplify_keep,
    validate_transform,
)
from ..utils import (
    TopoOptions,
    instance,
    serialize_as_geojson,
    serialize_as_json,
    serialize_as_svg,
    serialize_as_topojson,
)
from . import incremental
from .extract import Extract
from .hashmap import Hashmap

if TYPE_CHECKING:
    import altair
    import geopandas


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
    prequantize : boolean, int, dict
        If the prequantization parameter is specified, the input geometry is
        quantized prior to computing the topology, the returned topology is
        quantized, and its arcs are delta-encoded. Quantization is recommended to
        improve the quality of the topology if the input geometry is messy (i.e.,
        small floating point error means that adjacent boundaries do not have
        identical values); typical values are powers of ten, such as `1e4`, `1e5` or
        `1e6`. The grid is then derived from the bounding box of the input.
        Alternatively, provide a fixed TopoJSON transform as a dict
        (`{"scale": [kx, ky], "translate": [x0, y0]}`) to quantize on a grid that
        does not depend on the input, for example the `transform` of a previously
        computed Topology (`topo.output["transform"]`). The grid then stays the same
        when features are added or removed.
        Default is `True` (which correspond to a quantize factor of `1e5`).
    topoquantize : boolean, int or dict
        If the topoquantization parameter is specified, the input geometry is quantized
        after the topology is constructed. If the topology is already quantized this
        will be resolved first before the topoquantization is applied. As for
        `prequantize`, a fixed TopoJSON transform can be given as a dict. See for more
        details the `prequantize` parameter.
        Default is `False`.
    presimplify : boolean, float
        Apply presimplify to remove unnecessary points from linestrings before the
        topology is constructed. This will simplify the input geometries; lines are
        simplified one by one, so shared borders can drift apart, unless
        `simplify_with` is `geos`. `True` uses a tolerance of `2`.
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
    prevent_oversimplify : boolean
        If this setting is set to `True`, the simplification is slower, but the
        likelihood of producing valid geometries is higher as it prevents
        oversimplification. Simplification happens on paths separately, so this
        setting is especially relevant for rings with no partial shared paths. This
        is also known as a topology-preserving variant of simplification. With
        toposimplify, a ring that would be reduced to fewer than three points keeps
        the vertices to stay a triangle.
        Default is `True`.
    simplify_with : str
        Sets the package to use for simplifying (both pre- and toposimplify). Choose
        between `shapely`, `simplification` or `geos`. Shapely adopts solely
        Douglas-Peucker and simplification both Douglas-Peucker and
        Visvalingam-Whyatt. The package simplification is known to be quicker than
        shapely. `geos` applies to presimplify only: it simplifies the polygons
        together as a coverage (`shapely.coverage_simplify`, Visvalingam-Whyatt), so
        that shared borders stay matched and each ring stays at least a triangle;
        other lines are simplified with shapely. The polygons should form a valid
        coverage (`shapely.coverage_is_valid`).
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
        data: Any,
        topology: bool = True,
        prequantize: Quantize = True,
        topoquantize: Quantize = False,
        presimplify: bool | float = False,
        toposimplify: bool | float = False,
        shared_coords: bool = False,
        prevent_oversimplify: bool = True,
        simplify_with: Package = "shapely",
        simplify_algorithm: Algorithm = "dp",
        winding_order: WindingOrder | None = "CW_CCW",
        object_name: str | list[str] = "data",
        ignore_index: bool = False,
    ) -> None:
        options = TopoOptions(locals())

        # shortcut when dealing with topojson data
        if (
            instance(data) == "dict"
            and "type" in data
            and data["type"].casefold() == "Topology".casefold()
        ):
            self.output, self.options = serialize_as_topojson(data, options)

        # all others follow normal route
        else:
            # execute previous steps
            super().__init__(data, options)

        # execute main function of Topology
        self.output = self._topo(self.output)

        # per feature a hash of its input geometry, used by sync()
        self._source_hashes = _source_hashes(data)

    def __repr__(self) -> str:
        return f"Topology(\n{pprint.pformat(self.output)}\n)"

    def _copy_output(self) -> dict[str, Any]:
        """
        Copy of `output` that shares the arcs, for methods that only read them.
        """
        arcs = self.output["arcs"]
        return copy.deepcopy(self.output, {id(arcs): arcs})

    def _copy(self) -> Self:
        """
        Copy of the Topology with a new list of arcs, for methods that replace them.
        """
        arcs = self.output["arcs"]
        return copy.deepcopy(self, {id(arcs): list(arcs)})

    @property
    def __geo_interface__(self) -> dict[str, Any]:
        topo_object = self._copy_output()
        objectname = self._resolve_object_name(0)
        return serialize_as_geojson(topo_object, validate=False, objectname=objectname)

    def to_dict(self, options: bool = False, state: bool = False) -> dict[str, Any]:
        """
        Convert the Topology to a dictionary.

        Parameters
        ----------
        options : boolean
            If `True`, the options also will be included.
            Default is `False`
        state : boolean
            If `True`, the options and a hash of the input geometry of each feature
            (`source_hashes`) are included, so that `Topology.read_json` and `sync`
            can continue from it.
            Default is `False`
        """
        return self._to_dict(copy.deepcopy(self.output), options, state)

    def _to_dict(
        self, topo_object: dict[str, Any], options: bool, state: bool
    ) -> dict[str, Any]:
        topo_object = self._resolve_coords(topo_object)
        if options or state:
            topo_object["options"] = vars(self.options)
        else:
            topo_object.pop("options", None)
        if state:
            # as pairs, so that ids keep their type in JSON
            topo_object["source_hashes"] = [
                list(i) for i in self._source_hashes.items()
            ]
        return topo_object

    def to_svg(self, separate: bool = False) -> None:  # type: ignore[override]
        """
        Display the arcs and junctions as SVG.

        Parameters
        ----------
        separate : boolean
            If `True`, each of the arcs will be displayed separately.
            Default is `False`
        """
        serialize_as_svg(self.output, separate, include_junctions=False)

    def to_json(
        self,
        fp: str | os.PathLike[str] | None = None,
        options: bool = False,
        pretty: bool = False,
        indent: int = 4,
        maxlinelength: int = 88,
        state: bool = False,
    ) -> str | None:
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
        state : boolean
            If `True`, the options and a hash of the input geometry of each feature
            (`source_hashes`) are included, so that `Topology.read_json` and `sync`
            can continue from it in a next run.
            Default is `False`.
        """
        topo_object = self._to_dict(self._copy_output(), options is True, state)
        return serialize_as_json(
            topo_object, fp, pretty=pretty, indent=indent, maxlinelength=maxlinelength
        )

    def to_geojson(
        self,
        fp: str | os.PathLike[str] | None = None,
        pretty: bool = False,
        indent: int = 4,
        maxlinelength: int = 88,
        validate: bool = False,
        winding_order: WindingOrder = "CCW_CW",
        decimals: int | None = None,
        object_name: str | int = 0,
    ) -> str | None:
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
        topo_object = self._resolve_coords(self._copy_output())
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

    def to_gdf(
        self,
        crs: Any = None,
        validate: bool = False,
        winding_order: WindingOrder = "CCW_CW",
        object_name: str | int = 0,
    ) -> "geopandas.GeoDataFrame":
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

        topo_object = self._resolve_coords(self._copy_output())
        objectname = self._resolve_object_name(object_name)
        fc = serialize_as_geojson(
            topo_object, validate=validate, objectname=objectname, order=winding_order
        )

        if crs is None and hasattr(self, "_defined_crs_source"):
            crs = self._defined_crs_source
        return serialize_as_geodataframe(fc, crs=crs)

    def to_alt(  # type: ignore[override]
        self,
        color: str | None = None,
        tooltip: bool = True,
        projection: str = "identity",
        object_name: str | int = 0,
    ) -> "altair.Chart":
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
        slider_toposimplify: Slider | None = None,
        slider_topoquantize: Slider | None = None,
        slider_keep: Slider | None = None,
    ) -> Any:
        """
        Create an interactive widget based on Altair. The widget includes sliders to
        interactively change the `toposimplify` and `topoquantize` settings. With
        an algorithm "share of vertices", the `keep` slider sets the share of the
        vertices to keep instead of the tolerance.

        Parameters
        ----------
        slider_toposimplify : dict
            The dict should contain the following keys: `min`, `max`, `step`, `value`.
            Default is `{"min": 0, "max": 10, "step": 0.01, "value": 0.01}`.
        slider_topoquantize : dict
            The dict should contain the following keys: `min`, `max`, `value`, `base`.
            Default is `{"min": 1, "max": 6, "step": 1, "value": 1e5, "base": 10}`.
        slider_keep : dict
            The dict should contain the following keys: `min`, `max`, `step`, `value`.
            Default is `{"min": 0, "max": 1, "step": 0.01, "value": 0.1}`.
        """

        from ..utils import serialize_as_ipywidgets

        return serialize_as_ipywidgets(
            topo_object=self,
            toposimplify=slider_toposimplify
            or {"min": 0, "max": 10, "step": 0.01, "value": 0.01},
            topoquantize=slider_topoquantize
            or {"min": 1, "max": 6, "step": 1, "value": 1e5, "base": 10},
            keep=slider_keep or {"min": 0, "max": 1, "step": 0.01, "value": 0.1},
        )

    @overload
    def topoquantize(
        self, quant_factor: float | Transform, inplace: Literal[False] = False
    ) -> Self: ...

    @overload
    def topoquantize(
        self, quant_factor: float | Transform, inplace: Literal[True]
    ) -> None: ...

    def topoquantize(
        self, quant_factor: float | Transform, inplace: bool = False
    ) -> Self | None:
        """
        Quantization is recommended to improve the quality of the topology if the
        input geometry is messy (i.e., small floating point error means that
        adjacent boundaries do not have identical values); typical values are powers
        of ten, such as `1e4`, `1e5` or  `1e6`.

        Parameters
        ----------
        quant_factor : float or dict
            Quantization factor: the number of steps on each axis of the bounding
            box. Or a fixed TopoJSON transform as a dict
            (`{"scale": [kx, ky], "translate": [x0, y0]}`), for example a grid with
            cells that are a multiple of those of `prequantize`, so that each
            quantized point is also a point of the finer grid.
        inplace : bool, optional
            If `True`, do operation inplace and return `None`.
            Default is `False`.

        Returns
        -------
        object or None
            Quantized coordinates and delta-encoded arcs if `inplace` is `False`.
        """
        result = self._copy()
        arcs = result.output["arcs"]

        if not arcs:
            return None if inplace else result

        # dequantize if quantization is applied
        arcs = arc_coordinates(arcs, result.output.get("transform"))
        lsbs = bounds(arcs)

        if isinstance(quant_factor, dict):
            quant_factor = validate_transform(quant_factor)
            arcs_qnt, transform = quantize(arcs, None, transform=quant_factor)
        else:
            arcs_qnt, transform = quantize(arcs, result.output["bbox"], quant_factor)
        ptbs = bounds(result.output["coordinates"])
        result.output["bbox"] = compare_bounds(lsbs, ptbs)

        result.output["arcs"] = delta_encoding(arcs_qnt)
        result.output["transform"] = transform
        result.options.topoquantize = quant_factor

        if not inplace:
            return result
        # update into self
        self.output["arcs"] = result.output["arcs"]
        self.output["transform"] = result.output["transform"]
        self.options.topoquantize = result.options.topoquantize
        return None

    @overload
    def toposimplify(
        self,
        epsilon: float | None = None,
        simplify_algorithm: Algorithm | None = None,
        simplify_with: Package | None = None,
        prevent_oversimplify: bool | None = None,
        inplace: Literal[False] = False,
        keep: float | None = None,
    ) -> Self: ...

    @overload
    def toposimplify(
        self,
        epsilon: float | None = None,
        simplify_algorithm: Algorithm | None = None,
        simplify_with: Package | None = None,
        prevent_oversimplify: bool | None = None,
        *,
        inplace: Literal[True],
        keep: float | None = None,
    ) -> None: ...

    def toposimplify(
        self,
        epsilon: float | None = None,
        simplify_algorithm: Algorithm | None = None,
        simplify_with: Package | None = None,
        prevent_oversimplify: bool | None = None,
        inplace: bool = False,
        keep: float | None = None,
    ) -> Self | None:
        """
        Apply toposimplify to remove unnecessary points from arcs after the topology
        is constructed. This will simplify the constructed arcs without altering the
        topological relations. Sensible values for coordinates stored in degrees are
        in the range of `0.0001` to `10`.

        Parameters
        ----------
        epsilon : float, optional
            tolerance parameter. Give either `epsilon` or `keep`.
        simplify_algorithm : str, optional
            Choose between `dp` and `vw`, for Douglas-Peucker or Visvalingam-Whyatt
            respectively. `vw` will only be selected if `simplify_with` is set to
            `simplification`.
            Default is `None`, meaning that the default (`dp`) is not overwritten.
        simplify_with : str, optional
            Sets the package to use for simplifying. Choose between `shapely` or
            `simplification`. Shapely adopts solely Douglas-Peucker and simplification
            both Douglas-Peucker and Visvalingam-Whyatt. The package simplification is
            known to be quicker than shapely. `geos` applies to presimplify only and
            raises a `ValueError` here.
            Default is `None`, meaning that the default (`shapely`) is not overwritten.
        prevent_oversimplify : boolean, optional
            If this setting is set to `True`, the simplification is slower, but the
            likelihood of producing valid geometries is higher as it prevents
            oversimplification. Simplification happens on paths separately, so this
            setting is especially relevant for rings with no partial shared paths. This
            is also known as a topology-preserving variant of simplification. With
            toposimplify, a ring that would be reduced to fewer than three points keeps
            the vertices to stay a triangle.
            Default is `None`, meaning that the default (`True`) is not overwritten.
        inplace : bool, optional
            If `True`, do operation inplace and return `None`.
            Default is `False`.
        keep : float, optional
            Instead of `epsilon`, the share of the vertices to keep, between `0` and
            `1`: the inner vertices of the arcs that the algorithm removes last are
            kept, the ends of the arcs always. The result is that of the matching
            `epsilon`. Douglas-Peucker uses its own implementation, whatever
            `simplify_with`; Visvalingam-Whyatt (`simplify_algorithm="vw"`) uses the
            package simplification. With `prevent_oversimplify` a ring stays at least
            a triangle.

        Returns
        -------
        object or None
            Topology object with simplified linestrings if `inplace` is `False`.
        """
        if (epsilon is None) == (keep is None):
            raise ValueError("give either epsilon or keep")
        if keep is not None and not 0 <= keep <= 1:
            raise ValueError(f"keep is a share between 0 and 1, got: {keep!r}")
        result = self._copy()
        if not result.options.toposimplify:
            result.options.toposimplify = epsilon

        # set settings in options to override
        if isinstance(prevent_oversimplify, bool):
            result.options.prevent_oversimplify = prevent_oversimplify
        if simplify_with in ["shapely", "simplification"]:
            result.options.simplify_with = simplify_with
        if "geos" in (simplify_with, result.options.simplify_with):
            raise ValueError(
                "simplify_with='geos' simplifies polygons as a coverage and applies to "
                "presimplify; toposimplify simplifies arcs, use 'shapely' or "
                "'simplification'"
            )
        if simplify_algorithm in ["dp", "vw"]:
            result.options.simplify_algorithm = simplify_algorithm

        # get transform settings to dequantize if necessary
        transform = result.output.get("transform")

        # first do the arcs
        arcs = result.output["arcs"]
        if arcs:
            # dequantize if transform exist
            if transform is not None:
                power_estimate = len(str(int(np.max([arc[0] for arc in arcs]))))
                quant_factor_estimate = 10**power_estimate
            np_arcs = arc_coordinates(arcs, transform)

            # apply simplify
            if keep is not None:
                result.output["arcs"], _ = simplify_keep(
                    np_arcs, keep, result.options.simplify_algorithm
                )
            else:
                result.output["arcs"] = simplify(
                    np_arcs,
                    epsilon,
                    algorithm=result.options.simplify_algorithm,
                    package=result.options.simplify_with,
                    input_as="array",
                    prevent_oversimplify=result.options.prevent_oversimplify,
                )
            if result.options.prevent_oversimplify:
                sequences = incremental._all_sequences(result.output)
                rings = [s for s, ring in sequences if ring]
                result.output["arcs"] = restore_collapsed_rings(
                    result.output["arcs"], np_arcs, rings
                )

            lsbs = bounds(result.output["arcs"])
            ptbs = bounds(result.output["coordinates"])
            result.output["bbox"] = compare_bounds(lsbs, ptbs)

            # quantize again if quantization was applied
            if transform is not None:
                grid = result._grid() or quant_factor_estimate
                fixed = isinstance(grid, dict)
                # apply quantization and delta encode result.
                result.output["arcs"], transform = quantize(
                    result.output["arcs"],
                    result.output["bbox"],
                    None if fixed else grid,
                    transform=grid if fixed else None,
                )
                result.output["arcs"] = delta_encoding(result.output["arcs"])
                result.output["transform"] = transform
        if not inplace:
            return result
        # update into self
        self.output["arcs"] = result.output["arcs"]
        if "transform" in result.output:
            self.output["transform"] = result.output["transform"]
        self.options.toposimplify = result.options.toposimplify
        return None

    def _grid(self) -> float | dict[str, Any] | None:
        """The grid of the options to quantize on again: a transform (dict), a
        quantize factor, or `None` when the options set no quantization."""
        for option in (self.options.topoquantize, self.options.prequantize):
            if isinstance(option, dict):
                # keep the fixed grid
                return option
            if option > 0:
                # set default if not specifically given in the options
                return 1e5 if isinstance(option, bool) else option
        return None

    @classmethod
    def read_json(cls, fp: str | os.PathLike[str] | IO[str]) -> Self:
        """
        Read a Topology from a TopoJSON file. If the file was written with
        `to_json(..., state=True)`, the options and source hashes are restored, so that
        `add`, `remove` and `sync` can continue from it.

        Parameters
        ----------
        fp : str, path or file-like object
            TopoJSON file to read.

        Returns
        -------
        Topology
        """
        if isinstance(fp, str | os.PathLike):
            with open(fp) as f:
                data = json.load(f)
        else:
            data = json.load(fp)
        options = data.pop("options", None)
        hashes = data.pop("source_hashes", None)
        topo = cls(data)
        if options is not None:
            topo.options = TopoOptions(options)
        if hashes is not None:
            topo._source_hashes = dict(hashes)
        return topo

    def add(self, data: Any, object_name: str | None = None) -> Self:
        """
        Add features to the Topology without recomputing it. Existing arcs are cut
        where the new features share a path with them; the result is the same as a
        full build on the same quantization grid.

        Parameters
        ----------
        data : geopandas.GeoDataFrame or geopandas.GeoSeries
            Features to add. The index is used as feature id and must not exist yet.
        object_name : str, optional
            Object to add the features to. Only needed if the Topology has more than
            one object.

        Returns
        -------
        Topology
            `self`, so that calls can be chained.
        """
        return self._update(object_name, add=data)

    def remove(self, ids: Iterable[Hashable], object_name: str | None = None) -> Self:
        """
        Remove features from the Topology without recomputing it. Arcs that are no
        longer used are dropped and arcs are merged where a point is no longer a
        junction. Compared to a full build, a ring that is no longer cut can start at
        another vertex, and the bbox (recomputed from the quantized data) can differ
        by at most half a grid cell.

        Parameters
        ----------
        ids : iterable
            Ids of the features to remove.
        object_name : str, optional
            Object to remove the features from. Only needed if the Topology has more
            than one object.

        Returns
        -------
        Topology
            `self`, so that calls can be chained.
        """
        return self._update(object_name, remove=ids)

    def sync(self, data: Any, object_name: str | None = None) -> Self:
        """
        Make the Topology equal to `data`: features that are new are added, features
        that are gone are removed and features with a changed geometry are replaced.
        Unchanged features are left as they are. What happened is stored in
        `self.last_sync`.

        Comparing uses a hash of the input geometry of each feature. These hashes are
        kept on the Topology and written with `to_json(..., state=True)`.

        Parameters
        ----------
        data : geopandas.GeoDataFrame or geopandas.GeoSeries
            The complete set of features; the index is the feature id.
        object_name : str, optional
            Object to synchronise. Only needed if the Topology has more than one
            object.

        Returns
        -------
        Topology
            `self`, so that calls can be chained.
        """
        new_hashes = _source_hashes(data)
        if not new_hashes and len(data):
            raise TypeError("sync() needs a GeoDataFrame or GeoSeries")
        if not self._source_hashes and self._ids(
            self._incremental_object_name(object_name)
        ):
            raise ValueError(
                "sync() does not know the input geometry of the current features. "
                "Write the Topology with to_json(fp, state=True) and read it with "
                "Topology.read_json(fp)."
            )
        old = self._source_hashes
        gone = [i for i in old if i not in new_hashes]
        new = [i for i in new_hashes if i not in old]
        changed = [i for i in new_hashes if i in old and old[i] != new_hashes[i]]
        self._update(
            object_name,
            remove=gone + changed,
            add=data.loc[new + changed] if new or changed else None,
            ring_starts=incremental.ring_starts(data, self.output["transform"]),
        )
        self.last_sync = {
            "added": len(new),
            "removed": len(gone),
            "changed": len(changed),
            "unchanged": len(new_hashes) - len(new) - len(changed),
        }
        return self

    def _update(
        self,
        object_name: str | None,
        remove: Iterable[Hashable] = (),
        add: Any = None,
        ring_starts: dict[Hashable, Any] | None = None,
    ) -> Self:
        """Remove and then add features, decoding and encoding the arcs once."""
        name = self._incremental_object_name(object_name)
        remove = list(remove)
        missing = set(remove) - self._ids(name)
        if missing:
            raise KeyError(f"ids not in the topology: {sorted(missing, key=str)[:10]}")
        extracted = None
        if add is not None and len(add):
            extracted = Extract(add, copy.deepcopy(self.options)).output
            clash = (self._ids(name) - set(remove)) & set(extracted["objects"])
            if clash:
                raise ValueError(
                    f"ids already in the topology: {sorted(clash, key=str)[:10]}. To replace "
                    "features use topo.remove(ids).add(data) or topo.sync(data)."
                )
        if not remove and extracted is None:
            return self

        arcs = incremental.decode(self.output)
        if remove:
            incremental.remove_features(self.output, arcs, remove, name, ring_starts)
            for i in remove:
                self._source_hashes.pop(i, None)
        if extracted is not None:
            incremental.add_features(self.output, arcs, extracted, name)
            self._source_hashes.update(_source_hashes(add))
        area = arc_areas([arcs[i] for i in sorted(arcs)])
        incremental.encode(self.output, arcs)
        incremental.drop_collapsed_rings(self.output, area)
        return self

    def _ids(self, object_name: str) -> set[Hashable]:
        return {g.get("id") for g in self.output["objects"][object_name]["geometries"]}

    def _incremental_object_name(self, object_name: str | None) -> str:
        """Check that the Topology can be updated in place and resolve the object."""
        options = self.options
        if "transform" not in self.output or not options.topology:
            raise ValueError(
                "add, remove and sync need a quantized topology (prequantize, the "
                "default)."
            )
        if options.shared_coords:
            raise NotImplementedError(
                "add, remove and sync do not support shared_coords=True yet."
            )
        if options.presimplify or options.toposimplify or options.topoquantize:
            raise NotImplementedError(
                "add, remove and sync work on the unsimplified arcs. Apply toposimplify "
                "or topoquantize to the result instead, e.g. "
                "topo.toposimplify(epsilon, inplace=False)."
            )
        if options.ignore_index:
            raise NotImplementedError(
                "add, remove and sync use the index as feature id and do not support "
                "ignore_index=True."
            )
        names = list(self.output["objects"])
        if object_name is None:
            if len(names) != 1:
                raise ValueError(f"specify object_name, one of {names}")
            return names[0]
        if object_name not in names:
            raise KeyError(f"object_name {object_name!r} not in {names}")
        return object_name

    def _resolve_coords(self, data: dict[str, Any]) -> dict[str, Any]:
        def resolve(feat: dict[str, Any]) -> None:
            if feat["type"] == "GeometryCollection":
                for geom in feat.get("geometries", []):
                    resolve(geom)
            elif feat["type"] in ["Point", "MultiPoint"]:
                lofl = feat["coordinates"]
                repeat = 1 if feat["type"] == "Point" else 2

                for _ in range(repeat):
                    lofl = list(itertools.chain(*lofl))

                for idx, val in enumerate(lofl):
                    coord = data["coordinates"][val][0]
                    lofl[idx] = np.asarray(coord).tolist()

                feat["coordinates"] = lofl[0] if feat["type"] == "Point" else lofl
                feat.pop("reset_coords", None)

        for objectname in self.options.object_name:
            if objectname not in data["objects"]:
                raise SystemExit(
                    f"'{objectname}' is not an object name in your topojson file"
                )
            for feat in data["objects"][objectname]["geometries"]:
                resolve(feat)
            data.pop("coordinates", None)
        return data

    def _resolve_object_name(self, object_name: str | int | None) -> str:
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

    def _topo(self, data: dict[str, Any]) -> dict[str, Any]:
        self.output["arcs"] = data["linestrings"]
        del data["linestrings"]

        # apply delta-encoding if prequantization is applied
        if isinstance(self.options.prequantize, dict) or self.options.prequantize > 0:
            area = arc_areas(self.output["arcs"])
            self.output["arcs"] = delta_encoding(self.output["arcs"])
            # rings that collapsed on the grid have no area left
            incremental.drop_collapsed_rings(self.output, area)
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
        if isinstance(self.options.topoquantize, dict):
            grid = cast(Transform, self.options.topoquantize)
            self.topoquantize(quant_factor=grid, inplace=True)
        elif self.options.topoquantize > 0:
            # set default if not specifically given in the options
            if isinstance(self.options.topoquantize, bool):
                quant_factor = 1e5
            else:
                quant_factor = self.options.topoquantize

            self.topoquantize(quant_factor=quant_factor, inplace=True)

        return self.output


def _source_hashes(data: Any) -> dict[Hashable, str]:
    """Hash of the input geometry of each feature of a GeoDataFrame or GeoSeries."""
    if instance(data) not in ("GeoDataFrame", "GeoSeries"):
        return {}
    return {
        fid: hashlib.blake2b(b"" if g is None else g.wkb, digest_size=16).hexdigest()
        for fid, g in data.geometry.items()
    }
