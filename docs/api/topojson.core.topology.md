---
layout: default
title: topojson.core.topology
parent: API reference
nav_order: 1
---


# topojson.core.topology

## Topology
```python
Topology(self, data, topology=True, prequantize=True, topoquantize=False, presimplify=False, toposimplify=False, shared_coords=True, prevent_oversimplify=True, simplify_with='shapely', simplify_algorithm='dp', winding_order='CW_CCW')
```

Returns a TopoJSON topology for the specified geometric object. TopoJSON is an
extension of GeoJSON providing multiple approaches to compress the geographical
input data. These options include simplifying the linestrings or quantizing the
coordinates but foremost the computation of a topology.

> #### Parameters
> + ###### `data` : _any_ geometric type
    Geometric data that should be converted into TopoJSON
> + ###### `topology` : boolean
    Specify if the topology should be computed for deriving the TopoJSON.
    Default is `True`.
> + ###### `prequantize` : boolean, int
    If the prequantization parameter is specified, the input geometry is
    quantized prior to computing the topology, the returned topology is
    quantized, and its arcs are delta-encoded. Quantization is recommended to
    improve the quality of the topology if the input geometry is messy (i.e.,
    small floating point error means that adjacent boundaries do not have
    identical values); typical values are powers of ten, such as `1e4`, `1e5` or
    `1e5`. Default is `True` (which correspond to a quantize factor of `1e5`).
> + ###### `topoquantize` : boolean or int
    If the topoquantization parameter is specified, the input geometry is quantized
    after the topology is constructed. If the topology is already quantized this
    will be resolved first before the topoquantization is applied. See for more
    details the `prequantize` parameter. Default is `False`.
> + ###### `presimplify` : boolean, float
    Apply presimplify to remove unnecessary points from linestrings before the
    topology is constructed. This will simplify the input geometries. Use with care.
    Default is `False`.
> + ###### `toposimplify` : boolean, float
    Apply toposimplify to remove unnecessary points from arcs after the topology
    is constructed. This will simplify the constructed arcs without altering the
    topological relations. Sensible values for coordinates stored in degrees are
    in the range of `0.0001` to `10`. Defaults to `False`.
> + ###### `shared_coords` : boolean
    Sets the strategy to detect junctions. When set to `True` a path is
    considered shared when all coordinates appear in both paths
    (`coords-connected`). When set to `False` a path is considered shared when
    coordinates are the same path (`path-connected`). The path-connected strategy
    is more 'correct', but slower. Default is `True`.
> + ###### `prevent_oversimplify`: boolean
    If this setting is set to `True`, the simplification is slower, but the
    likelihood of producing valid geometries is higher as it prevents
    oversimplification. Simplification happens on paths separately, so this
    setting is especially relevant for rings with no partial shared paths. This
    is also known as a topology-preserving variant of simplification.
    Default is `True`.
> + ###### `simplify_with` : str
    Sets the package to use for simplifying (both pre- and toposimplify). Choose
    between `shapely` or `simplification`. Shapely adopts solely Douglas-Peucker
    and simplification both Douglas-Peucker and Visvalingam-Whyatt. The package
    simplification is known to be quicker than shapely.
    Default is `shapely`.
> + ###### `simplify_algorithm` : str
    Choose between `dp` and `vw`, for Douglas-Peucker or Visvalingam-Whyatt
    respectively. `vw` will only be selected if `simplify_with` is set to
    `simplification`. Default is `dp`, since it "produced the most accurate
    generalization" (Shi, W. & Cheung, C., 2006).
> + ###### `winding_order` : str
    Determines the winding order of the features in the output geometry. Choose
    between `CW_CCW` for clockwise orientation for outer rings and counter-
    clockwise for interior rings. Or `CCW_CW` for counter-clockwise for outer
    rings and clockwise for interior rings. Default is `CW_CCW`.
> + ###### `object_name` : str
    Name to use as key for the objects in the topojson file. This name is used for
    writing and reading topojson file formats.
    Default is `data`.

### to_dict
```python
Topology.to_dict(self, options=False)
```

Convert the Topology to a dictionary.

> #### Parameters
> + ###### `options` : boolean
    If `True`, the options also will be included.
    Default is `False`

### to_svg
```python
Topology.to_svg(self, separate=False, include_junctions=False)
```

Display the arcs and junctions as SVG.

> #### Parameters
> + ###### `separate` : boolean
    If `True`, each of the arcs will be displayed separately.
    Default is `False`
> + ###### `include_junctions` : boolean
    If `True`, the detected junctions will be displayed as well.
    Default is `False`

### to_json
```python
Topology.to_json(self, fp=None, options=False, pretty=False, indent=4, maxlinelength=88)
```

Convert the Topology to a JSON object.

> #### Parameters
> + ###### `fp` : str
    If set, writes the object to a file on drive.
    Default is `None`
> + ###### `options` : boolean
    If `True`, the options also will be included.
    Default is `False`
> + ###### `pretty` : boolean
    If `True`, the JSON object will be 'pretty', depending on the `ident` and
    `maxlinelength` options
    Default is `False`
> + ###### `indent` : int
    If `pretty=True`, declares the indentation of the objects.
    Default is `4`.
> + ###### `maxlinelength` : int
    If `pretty=True`, declares the maximum length of each line.
    Default is `88`.

### to_geojson
```python
Topology.to_geojson(self, fp=None, pretty=False, indent=4, maxlinelength=88, validate=False, objectname='data')
```

Convert the Topology to a GeoJSON object. Remember that this will destroy the
computed Topology.

> #### Parameters
> + ###### `fp` : str
    If set, writes the object to a file on drive.
    Default is `None`
> + ###### `pretty` : boolean
    If `True`, the JSON object will be 'pretty', depending on the `ident` and
    `maxlinelength` options.
    Default is `False`
> + ###### `indent` : int
    If `pretty=True`, declares the indentation of the objects.
    Default is `4`
> + ###### `maxlinelength` : int
    If `pretty=True`, declares the maximum length of each line.
    Default is `88`
> + ###### `validate` : boolean
    Set to `True` to validate each feature before inclusion in the GeoJSON. Only
    features that are valid geometries objects will be included.
    Default is `False`
> + ###### `objectname` : str
    The name of the object within the Topology to convert to GeoJSON.
    Default is `data`
> + ###### `decimals` : int or None
    Evenly round the coordinates to the given number of decimals. 
    Default is `None`, which means no rounding is applied. 

### to_gdf
```python
Topology.to_gdf(self)
```

Convert the Topology to a GeoDataFrame. Remember that this will destroy the
computed Topology.

Note: This function use the TopoJSON driver within Fiona to parse the Topology
to a GeoDataFrame. If data is missing (eg. Fiona cannot parse nested
geometry collections) you can trying using the `.to_geojson()` function prior
creating the GeoDataFrame.

### to_alt
```python
Topology.to_alt(self, mesh=True, color=None, tooltip=True, projection='identity', objectname='data')
```

Display as Altair visualization.

> #### Parameters
> + ###### `mesh` : boolean
    If `True`, render arcs only (mesh object). If `False` render as geoshape.
    Default is `True`
> + ###### `color` : str
    Assign an property attribute to be used for color encoding. Remember that
    most of the time the wanted attribute is nested within properties. Moreover,
    specific type declaration is required. Eg `color='properties.name:N'`.
    Default is `None`
> + ###### `tooltip` : boolean
    Option to include or exclude tooltips on geoshape objects
    Default is `True`.
> + ###### `projection` : str
    Defines the projection of the visualization. Defaults to a non-geographic,
    Cartesian projection (known by Altair as `identity`).
> + ###### `objectname` : str
    The name of the object within the Topology to display.
    Default is `data`

### to_widget
```python
Topology.to_widget(self, slider_toposimplify={'min': 0, 'max': 10, 'step': 0.01, 'value': 0.01}, slider_topoquantize={'min': 1, 'max': 6, 'step': 1, 'value': 100000.0, '> + ###### `base': ` : 10})
```

Create an interactive widget based on Altair. The widget includes sliders to
interactively change the `toposimplify` and `topoquantize` settings.

> #### Parameters
> + ###### `slider_toposimplify` : dict
    The dict should contain the following keys: `min`, `max`, `step`, `value`
> + ###### `slider_topoquantize` : dict
    The dict should contain the following keys: `min`, `max`, `value`, `base`

### topoquantize
```python
Topology.topoquantize(self, quant_factor, inplace=False)
```

Quantization is recommended to improve the quality of the topology if the
input geometry is messy (i.e., small floating point error means that
adjacent boundaries do not have identical values); typical values are powers
of ten, such as `1e4`, `1e5` or  `1e6`.

> #### Parameters
> + ###### `quant_factor` : float
    tolerance parameter
> + ###### `inplace` : bool, optional
    If `True`, do operation inplace and return `None`. Default is `False`.

> #### Returns
> + ###### object or None
Quantized coordinates and delta-encoded arcs if `inplace` is `False`.

### toposimplify
```python
Topology.toposimplify(self, epsilon, inplace=False)
```

Apply toposimplify to remove unnecessary points from arcs after the topology
is constructed. This will simplify the constructed arcs without altering the
topological relations. Sensible values for coordinates stored in degrees are
in the range of `0.0001` to `10`.

> #### Parameters
> + ###### `epsilon` : float
    tolerance parameter.
> + ###### `inplace` : bool, optional
    If `True`, do operation inplace and return `None`. Default is `False`.

> #### Returns
> + ###### object or None
Topology object with simplified linestrings if `inplace` is `False`.
