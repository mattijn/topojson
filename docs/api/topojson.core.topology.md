---
layout: default
title: topojson.core.topology
parent: API reference
nav_order: 1
---


# topojson.core.topology

## Topology
```python
Topology(self, data, topology=True, prequantize=True, topoquantize=False, presimplify=False, toposimplify=0.0001, simplify_with='shapely', simplify_algorithm='dp', winding_order='CW_CCW')
```

Returns a TopoJSON topology for the specified geometric object. TopoJSON is an
extension of GeoJSON providing multiple approaches to compress the geographical
input data. These options include simplifying the linestrings or quantizing the
coordinates but foremost the computation of a topology.

>#### Parameters
> + 
###### `data` : (_any_ geometric type)
    Geometric data that should be converted into TopoJSON
> + 
###### `topology` : (boolean)
    Specifiy if the topology should be computed for deriving the TopoJSON.
    Default is True.
> + 
###### `prequantize` : (boolean, int)
    If the prequantization parameter is specified, the input geometry is quantized
    prior to computing the topology, the returned topology is quantized, and its
    arcs are delta-encoded. Quantization is recommended to improve the quality of
    the topology if the input geometry is messy (i.e., small floating point error
    means that adjacent boundaries do not have identical values); typical values
    are powers of ten, such as 1e4, 1e5 or 1e6. Default is True (which correspond
    to a quantize factor of 1e6).
> + 
###### `topoquantize` : (boolean or int)
    If the topoquantization parameter is specified, the input geometry is quantized
    after the topology is constructed. If the topology is already quantized this
    will be resolved first before the topoquantization is applied.
    Default is False.
> + 
###### `presimplify` : (boolean, float)
    Apply presimplify to remove unnecessary points from linestrings before the
    topology is constructed. This will simplify the input geometries.
    Default is False.
> + 
###### `toposimplify` : (boolean,float)
    Apply toposimplify to remove unnecessary points from arcs after the topology is
    constructed. This will simplify the constructed arcs without altering the
    topological relations. Sensible values are in the range of 0.0001 to 10.
    Defaults to 0.0001.
> + 
###### `simplify_with` : (str)
    Sets the package to use for simplifying (both pre- and toposimplify). Choose
    between `shapely` or `simplification`. Shapely adopts solely Douglas-Peucker
    and simplification both Douglas-Peucker and Visvalingam-Whyatt. The pacakge
    simplification is known to be quicker than shapely.
    Default is `shapely`.
> + 
###### `simplify_algorithm` : (str)
    Choose between 'dp' and 'vw', for Douglas-Peucker or Visvalingam-Whyatt
    respectively. 'vw' will only be selected if `simplify_with` is set to
    `simplification`. Default is `dp`, since it still "produces the most accurate
    generalization" (Chi & Cheung, 2006).
> + 
###### `winding_order` : (str)
    Determines the winding order of the features in the output geometry. Choose
    between `CW_CCW` for clockwise orientation for outer rings and counter-clockwise
    for interior rings. Or `CCW_CW` for counter-clockwise for outer rings and
    clockwise for interior rings. Default is `CW_CCW`.


