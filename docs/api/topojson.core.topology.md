---
layout: default
title: topojson.core.topology
parent: API reference
nav_order: 1
---


# topojson.core.topology

## Topology
```python
Topology(self,
         data,
         topology=True,
         prequantize=True,
         topoquantize=False,
         presimplify=False,
         toposimplify=False,
         shared_coords=False,
         prevent_oversimplify=True,
         simplify_with='shapely',
         simplify_algorithm='dp',
         winding_order='CW_CCW',
         object_name='data',
         ignore_index=False)
```

Returns a TopoJSON topology for the specified geometric object. TopoJSON is an
extension of GeoJSON providing multiple approaches to compress the geographical
input data. These options include simplifying the linestrings or quantizing the
coordinates but foremost the computation of a topology.

> #### Parameters
> + ###### `data` : _any_ geometric type
    Geometric data that should be converted into TopoJSON.
    It is possible to provide a list of multiple geopandas.GeoDataFrames as
    separate objects. In this case it is required to provide an equal length list of
    the names of the objects for parameter `object_name`.
> + ###### `topology` : boolean
    Specify if the topology should be computed for deriving the TopoJSON.
    Default is `True`.
> + ###### `prequantize` : boolean, int, dict
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
> + ###### `topoquantize` : boolean, int or dict
    If the topoquantization parameter is specified, the input geometry is quantized
    after the topology is constructed. If the topology is already quantized this
    will be resolved first before the topoquantization is applied. As for
    `prequantize`, a fixed TopoJSON transform can be given as a dict. See for more
    details the `prequantize` parameter.
    Default is `False`.
> + ###### `presimplify` : boolean, float
    Apply presimplify to remove unnecessary points from linestrings before the
    topology is constructed. This will simplify the input geometries; lines are
    simplified one by one, so shared borders can drift apart, unless
    `simplify_with` is `geos`. `True` uses a tolerance of `2`.
    Default is `False`.
> + ###### `toposimplify` : boolean, float
    Apply toposimplify to remove unnecessary points from arcs after the topology
    is constructed. This will simplify the constructed arcs without altering the
    topological relations. Sensible values for coordinates stored in degrees are
    in the range of `0.0001` to `10`.
    Defaults to `False`.
> + ###### `shared_coords` : boolean
    Sets the strategy to detect junctions. When set to `False` a path is considered
    shared when coordinates are the same path (`path-connected`). The path-connected
    strategy is more 'correct', but slightly slower. When set to `True` a path is
    considered shared when all coordinates appear in both paths
    (`coords-connected`).
    Default is `False`.
> + ###### `prevent_oversimplify` : boolean
    If this setting is set to `True`, the simplification is slower, but the
    likelihood of producing valid geometries is higher as it prevents
    oversimplification. Simplification happens on paths separately, so this
    setting is especially relevant for rings with no partial shared paths. This
    is also known as a topology-preserving variant of simplification. With
    toposimplify, a ring that would be reduced to fewer than three points keeps
    the vertices to stay a triangle.
    Default is `True`.
> + ###### `simplify_with` : str
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
> + ###### `simplify_algorithm` : str
    Choose between `dp` and `vw`, for Douglas-Peucker or Visvalingam-Whyatt
    respectively. `vw` will only be selected if `simplify_with` is set to
    `simplification`.
    Default is `dp`.
> + ###### `winding_order` : str
    Determines the winding order of the features in the output geometry. Choose
    between `CW_CCW` for clockwise orientation for outer rings and counter-
    clockwise for interior rings. Or `CCW_CW` for counter-clockwise for outer
    rings and clockwise for interior rings.
    Default is `CW_CCW` for TopoJSON.
> + ###### `object_name` : Union[str, list[str]]
    Name to use as key for the objects in the topojson file. This name is used for
    writing and reading topojson file formats.
    It is possible to define multiple objects within the topojson file. In this
    case it is required to provide a list of the referenced `object_name` in
    combination with an equal length list of `data` objects.
    Default is a single object named `data`.
> + ###### `ignore_index` : bool
    If set to true existing ids/indexes of geojson FeatureCollections will be
    ignored and overwritten. Otherwise features with ids will use their existing one.
    If indexes are not ignored and a duplicate id exists an exception will be raised.
    Default is false.

### to_dict
```python
Topology.to_dict(options=False, state=False)
```

Convert the Topology to a dictionary.

> #### Parameters
> + ###### `options` : boolean
    If `True`, the options also will be included.
    Default is `False`
> + ###### `state` : boolean
    If `True`, the options and a hash of the input geometry of each feature
    (`source_hashes`) are included, so that `Topology.read_json` and `sync`
    can continue from it.
    Default is `False`

### to_svg
```python
Topology.to_svg(separate=False)
```

Display the arcs and junctions as SVG.

> #### Parameters
> + ###### `separate` : boolean
    If `True`, each of the arcs will be displayed separately.
    Default is `False`

### to_json
```python
Topology.to_json(fp=None,
                 options=False,
                 pretty=False,
                 indent=4,
                 maxlinelength=88,
                 state=False)
```

Convert the Topology to a JSON object.

> #### Parameters
> + ###### `fp` : str
    If set, writes the object to a file on drive.
    Default is `None`.
> + ###### `options` : boolean
    If `True`, the options also will be included.
    Default is `False`.
> + ###### `pretty` : boolean
    If `pretty=True`, the JSON object will be 'pretty', depending on the
    `ident` and `maxlinelength` options. If `pretty=False`, it will `compact`,
    eliminating whitespace.
    Default is `False`.
> + ###### `indent` : int
    If `style='pretty'`, declares the indentation of the objects.
    Default is `4`.
> + ###### `maxlinelength` : int
    If `style='pretty'`, declares the maximum length of each line.
    Default is `88`.
> + ###### `state` : boolean
    If `True`, the options and a hash of the input geometry of each feature
    (`source_hashes`) are included, so that `Topology.read_json` and `sync`
    can continue from it in a next run.
    Default is `False`.

### to_geojson
```python
Topology.to_geojson(fp=None,
                    pretty=False,
                    indent=4,
                    maxlinelength=88,
                    validate=False,
                    winding_order='CCW_CW',
                    decimals=None,
                    object_name=0)
```

Convert the Topology to a GeoJSON object. Remember that this will destroy the
computed Topology.

> #### Parameters
> + ###### `fp` : str
    If set, writes the object to a file on drive.
    Default is `None`
> + ###### `pretty` : boolean
    If `pretty=True`, the JSON object will be 'pretty', depending on the
    `ident` and `maxlinelength` options. If `pretty=False`, it will `compact`,
    eliminating whitespace.
    Default is `False`.
> + ###### `indent` : int
    If `pretty=True`, declares the indentation of the objects.
    Default is `4`.
> + ###### `maxlinelength` : int
    If `pretty=True`, declares the maximum length of each line.
    Default is `88`.
> + ###### `validate` : boolean
    Set to `True` to validate each feature before inclusion in the GeoJSON. Only
    features that are valid geometries objects will be included.
    Default is `False`.
> + ###### `winding_order` : str
    Determines the winding order of the features in the output geometry. Choose
    between `CW_CCW` for clockwise orientation for outer rings and counter-
    clockwise for interior rings. Or `CCW_CW` for counter-clockwise for outer
    rings and clockwise for interior rings.
    Default is `CCW_CW` for GeoJSON.
> + ###### `decimals` : int or None
    Evenly round the coordinates to the given number of decimals.
    Default is None, which means no rounding is applied.
> + ###### `object_name` : str, int
    The name or the index of the object within the Topology to display.
    Default is index 0.

### to_gdf
```python
Topology.to_gdf(crs=None,
                validate=False,
                winding_order='CCW_CW',
                object_name=0)
```

Convert the Topology to a GeoDataFrame. Remember that this will destroy the
computed Topology.

Note: This function use not the TopoJSON driver within Fiona, but a custom
implemented more robust variant. See for info the `to_geojson()` function.

> #### Parameters
> + ###### `crs` : str, dict
    coordinate reference system to set on the resulting frame.
    Default tries to use crs from data-input, otherwise is `None`.
> + ###### `validate` : boolean
    Set to `True` to validate each feature before inclusion in the GeoJSON. Only
    features that are valid geometries objects will be included.
    Default is `False`.
> + ###### `winding_order` : str
    Determines the winding order of the features in the output geometry. Choose
    between `CW_CCW` for clockwise orientation for outer rings and counter-
    clockwise for interior rings. Or `CCW_CW` for counter-clockwise for outer
    rings and clockwise for interior rings.
    Default is `CCW_CW` for GeoJSON.
> + ###### `object_name` : str, int
    Name or index of the object.
    Default is index `0` to select the first object.

### to_alt
```python
Topology.to_alt(color=None,
                tooltip=True,
                projection='identity',
                object_name=0)
```

Display as Altair visualization.

> #### Parameters
> + ###### `color` : str
    Assign an property attribute to be used for color encoding and renders the
    Altair visualization as geoshape. Remember that most of the time the wanted
    attribute is nested within properties. Moreover, specific type declaration
    is required. Eg `color='properties.name:N'`.
    Default is `None` (render as mesh).
> + ###### `tooltip` : boolean
    Option to include or exclude tooltips on geoshape objects
    Default is `True`.
> + ###### `projection` : str
    Defines the projection of the visualization. Defaults to a non-geographic,
    Cartesian projection (known by Altair as `identity`).
> + ###### `object_name` : str, int
    The name or the index of the object within the Topology to display.
    Default is index 0.

### to_widget
```python
Topology.to_widget(
  slider_toposimplify={'min': 0, 'max': 10, 'step': 0.01, 'value': 0.01},
  slider_topoquantize={'min': 1, 'max': 6, 'step': 1, 'value': 100000.0, 'base': 10},
  slider_keep={'min': 0, 'max': 1, 'step': 0.01, 'value': 0.1})
```

Create an interactive widget based on Altair. The widget includes sliders to
interactively change the `toposimplify` and `topoquantize` settings. With
an algorithm "share of vertices", the `keep` slider sets the share of the
vertices to keep instead of the tolerance.

> #### Parameters
> + ###### `slider_toposimplify` : dict
    The dict should contain the following keys: `min`, `max`, `step`, `value`.
    Default is `{"min": 0, "max": 10, "step": 0.01, "value": 0.01}`.
> + ###### `slider_topoquantize` : dict
    The dict should contain the following keys: `min`, `max`, `value`, `base`.
    Default is `{"min": 1, "max": 6, "step": 1, "value": 1e5, "base": 10}`.
> + ###### `slider_keep` : dict
    The dict should contain the following keys: `min`, `max`, `step`, `value`.
    Default is `{"min": 0, "max": 1, "step": 0.01, "value": 0.1}`.

### topoquantize
```python
Topology.topoquantize(quant_factor, inplace=False)
```

Quantization is recommended to improve the quality of the topology if the
input geometry is messy (i.e., small floating point error means that
adjacent boundaries do not have identical values); typical values are powers
of ten, such as `1e4`, `1e5` or  `1e6`.

> #### Parameters
> + ###### `quant_factor` : float or dict
    Quantization factor: the number of steps on each axis of the bounding
    box. Or a fixed TopoJSON transform as a dict
    (`{"scale": [kx, ky], "translate": [x0, y0]}`), for example a grid with
    cells that are a multiple of those of `prequantize`, so that each
    quantized point is also a point of the finer grid.
> + ###### `inplace` : bool, optional
    If `True`, do operation inplace and return `None`.
    Default is `False`.

> #### Returns
> + ###### object or None
Quantized coordinates and delta-encoded arcs if `inplace` is `False`.

### toposimplify
```python
Topology.toposimplify(epsilon=None,
                      simplify_algorithm=None,
                      simplify_with=None,
                      prevent_oversimplify=None,
                      inplace=False,
                      keep=None)
```

Apply toposimplify to remove unnecessary points from arcs after the topology
is constructed. This will simplify the constructed arcs without altering the
topological relations. Sensible values for coordinates stored in degrees are
in the range of `0.0001` to `10`.

> #### Parameters
> + ###### `epsilon` : float, optional
    tolerance parameter. Give either `epsilon` or `keep`.
> + ###### `simplify_algorithm` : str, optional
    Choose between `dp` and `vw`, for Douglas-Peucker or Visvalingam-Whyatt
    respectively. `vw` will only be selected if `simplify_with` is set to
    `simplification`.
    Default is `None`, meaning that the default (`dp`) is not overwritten.
> + ###### `simplify_with` : str, optional
    Sets the package to use for simplifying. Choose between `shapely` or
    `simplification`. Shapely adopts solely Douglas-Peucker and simplification
    both Douglas-Peucker and Visvalingam-Whyatt. The package simplification is
    known to be quicker than shapely. `geos` applies to presimplify only and
    raises a `ValueError` here.
    Default is `None`, meaning that the default (`shapely`) is not overwritten.
> + ###### `prevent_oversimplify` : boolean, optional
    If this setting is set to `True`, the simplification is slower, but the
    likelihood of producing valid geometries is higher as it prevents
    oversimplification. Simplification happens on paths separately, so this
    setting is especially relevant for rings with no partial shared paths. This
    is also known as a topology-preserving variant of simplification. With
    toposimplify, a ring that would be reduced to fewer than three points keeps
    the vertices to stay a triangle.
    Default is `None`, meaning that the default (`True`) is not overwritten.
> + ###### `inplace` : bool, optional
    If `True`, do operation inplace and return `None`.
    Default is `False`.
> + ###### `keep` : float, optional
    Instead of `epsilon`, the share of the vertices to keep, between `0` and
    `1`: the inner vertices of the arcs that the algorithm removes last are
    kept, the ends of the arcs always. The result is that of the matching
    `epsilon`. Douglas-Peucker uses its own implementation, whatever
    `simplify_with`; Visvalingam-Whyatt (`simplify_algorithm="vw"`) uses the
    package simplification. With `prevent_oversimplify` a ring stays at least
    a triangle.

> #### Returns
> + ###### object or None
Topology object with simplified linestrings if `inplace` is `False`.

### read_json
```python
Topology.read_json(fp)
```

Read a Topology from a TopoJSON file. If the file was written with
`to_json(..., state=True)`, the options and source hashes are restored, so that
`add`, `remove` and `sync` can continue from it.

> #### Parameters
> + ###### `fp` : str, path or file-like object
    TopoJSON file to read.

> #### Returns
Topology

### add
```python
Topology.add(data, object_name=None)
```

Add features to the Topology without recomputing it. Existing arcs are cut
where the new features share a path with them; the result is the same as a
full build on the same quantization grid.

> #### Parameters
> + ###### `data` : geopandas.GeoDataFrame or geopandas.GeoSeries
    Features to add. The index is used as feature id and must not exist yet.
> + ###### `object_name` : str, optional
    Object to add the features to. Only needed if the Topology has more than
    one object.

> #### Returns
> + ###### Topology
`self`, so that calls can be chained.

### remove
```python
Topology.remove(ids, object_name=None)
```

Remove features from the Topology without recomputing it. Arcs that are no
longer used are dropped and arcs are merged where a point is no longer a
junction. Compared to a full build, a ring that is no longer cut can start at
another vertex, and the bbox (recomputed from the quantized data) can differ
by at most half a grid cell.

> #### Parameters
> + ###### `ids` : iterable
    Ids of the features to remove.
> + ###### `object_name` : str, optional
    Object to remove the features from. Only needed if the Topology has more
    than one object.

> #### Returns
> + ###### Topology
`self`, so that calls can be chained.

### sync
```python
Topology.sync(data, object_name=None)
```

Make the Topology equal to `data`: features that are new are added, features
that are gone are removed and features with a changed geometry are replaced.
Unchanged features are left as they are. What happened is stored in
`self.last_sync`.

Comparing uses a hash of the input geometry of each feature. These hashes are
kept on the Topology and written with `to_json(..., state=True)`.

> #### Parameters
> + ###### `data` : geopandas.GeoDataFrame or geopandas.GeoSeries
    The complete set of features; the index is the feature id.
> + ###### `object_name` : str, optional
    Object to synchronise. Only needed if the Topology has more than one
    object.

> #### Returns
> + ###### Topology
`self`, so that calls can be chained.


