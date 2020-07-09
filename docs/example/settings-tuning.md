---
layout: default
title: Settings and tuning
parent: Example usage
nav_order: 2
---

# Settings and tuning
{: .no_toc}

By adopting the TopoJSON format is possible to store geographical data as topology. Adopting this approach can make it possible to create smaller files than its GeoJSON counterpart. In this process are a few options, which are described below by the following options:

1. TOC
{:toc}

* * * 

## topology

###### boolean
{: .no_toc}
Specifiy if the topology should be computed for deriving the TopoJSON.
Default is `True`.

<div class="code-example mx-1 bg-example">
<div class="example-label" markdown="1">
Example 🔧
{: .label .label-blue-000 }
</div>
<div class="example-text" markdown="1">

Given the following two polygon with one side sharing:
```python
import topojson as tp
from shapely import geometry

data = geometry.MultiLineString([
    [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]], 
    [[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]
])
data
```
<img src="../images/two_polygon.svg">

By setting `topology=False` a TopoJSON structured file format is created without considering shared segments (the setting `prequantize=False` avoids computing the delta-encoding):
```python
tp.Topology(data, topology=False, prequantize=False)
```
```bash
Topology(
{'arcs': [[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0]],
          [[1.0, 0.0], [2.0, 0.0], [2.0, 1.0], [1.0, 1.0], [1.0, 0.0]]],
 'bbox': (0.0, 0.0, 2.0, 1.0),
 'coordinates': [],
 'objects': {'data': {'geometries': [{'arcs': [[0], [1]],
                                      'type': 'MultiLineString'}],
                      'type': 'GeometryCollection'}},
 'type': 'Topology'}
)
```
As can be seen, the geometries are referenced by two segments (`'arcs': [[0], [1]]`), where each segment is a single Polygon (see: `arcs`).

When doing the same with `topology=True`, there are three `arcs`. Where one arc is referenced two times, namely arc `2` (arc `-3` is arc `2` reversed).
```python
tp.Topology(data, topology=False, prequantize=False)
```
```bash
Topology(
{'arcs': [[[1.0, 1.0], [0.0, 1.0], [0.0, 0.0], [1.0, 0.0]],
          [[1.0, 0.0], [2.0, 0.0], [2.0, 1.0], [1.0, 1.0]],
          [[1.0, 1.0], [1.0, 0.0]]],
 'bbox': (0.0, 0.0, 2.0, 1.0),
 'coordinates': [],
 'objects': {'data': {'geometries': [{'arcs': [[-3, 0], [1, 2]],
                                      'type': 'MultiLineString'}],
                      'type': 'GeometryCollection'}},
 'type': 'Topology'}
)
```
</div>
</div>


<!-- **Note:** The following figure is here to test if interactivity is possible

<div id="embed_tuning_topology"></div> -->


* * *         

## prequantize

###### boolean, int
{: .no_toc}

If the prequantization parameter is specified, the input geometry is 
quantized prior to computing the topology. The returned topology is 
quantized, and its arcs are delta-encoded. 

Quantization is recommended to 
improve the quality of the topology if the input geometry is messy (i.e., 
small floating point error means that adjacent boundaries do not have 
identical values); typical values are powers of ten, such as `1e4`, `1e5` or 
`1e6`. Default is `True` (which correspond to a quantize factor of `1e6`).

<div class="code-example mx-1 bg-example">
<div class="example-label" markdown="1">
Example 🔧
{: .label .label-blue-000 }
</div>
<div class="example-text" markdown="1">

Quantization is a two-step process, namely normalization and delta-encoding. Given the following two polygon with no sides shared, as the left-polygon has the x-max coordinate at `0.97` and the right-polygon has the x-min coordinate at `1.03`:
```python
import topojson as tp
from shapely import geometry

data = geometry.MultiLineString([
    [[0, 0], [0.97, 0], [0.97, 1], [0, 1], [0, 0]], 
    [[1.03, 0], [2, 0], [2, 1], [1.03, 1], [1.03, 0]]
])
data
```
<img src="../images/two_no_touching_polygon.svg">

The `prequantize` option is defined as an integer number. It can be best understand as a value that defines the size of a rectangular grid, with the bottom left coordinate at `(0,0)`. Next, the `x`-numbers and `y`-numbers of all coordinates are indepentenly scaled and shifted on this rectangular grid (normalization on range):
```python
# get the x-numbers of all coordinates
x = np.array([ls.xy[0] for ls in data])
print(f'x:\n{x}')

# compute the scaling factor (kx) given the quantize factor (qf)
qf = 33
kx = (x.max() - x.min()) / (qf - 1)
print(f'kx: {kx}')

# shift and apply the scaling factor to map the x-numbers on the integer range
xnorm = np.round((x - x.min()) / kx).astype(int)
print(f'x-normalized:\n{xnorm}')

# denormalize happens as follow
print(f'x-denormalized:\n{xnorm * kx + x.min()}')
```
```bash
x:
[[0.   0.97 0.97 0.   0.  ]
 [1.03 2.   2.   1.03 1.03]]
kx: 0.0625
x-normalized:
[[ 0 16 16  0  0]
 [16 32 32 16 16]]
x-denormalized:
[[0. 1. 1. 0. 0.]
 [1. 2. 2. 1. 1.]]
```
The delta-encoding is applied on the normalized coordinates and starting from the first coordinate, only the delta towards the following coordinate is stored. It is a character-reducing process, since the delta between two points is normally smaller than storing both coordinates. Here an example is shown for the `x`-numbers only (1D), where in real it is a 2D process:
```python
# delta encoding of normalized x-numbers
x_quant = np.insert(np.diff(xnorm), 0, xnorm[:,0], axis=1)
print(f'x-quantized (normalized-delta-encoded):\n{x_quant}')

# dequantization of quantized x-numbers
x_dequant = x_quant.cumsum(axis=1) * kx + x.min()
print(f'x-dequantized:\n{x_dequant}')
```
```bash
x-quantized (normalized-delta-encoded):
[[  0  16   0 -16   0]
 [ 16  16   0 -16   0]]
x-dequantized:
[[0. 1. 1. 0. 0.]
 [1. 2. 2. 1. 1.]]
 ```

So, to apply this `prequantize` value on the two no touching polygons, the polygons are touching as a result of it:
```python
topo = tp.Topology(data, prequantize=33)
topo.to_svg()
```
<img src="../images/two_polygon.svg">
</div>
</div>

* * * 

## topoquantize

###### boolean or int
{: .no_toc}

If the topoquantization parameter is specified, the input geometry is quantized 
after the topology is constructed. If the topology is already quantized this 
will be resolved first before the topoquantization is applied. See for more 
details the `prequantize` parameter. Default is `False`.

See [prequantize](settings-tuning.html#prequantize) for an explained example.

**Note:** This is also supported by chaining. Meaning you could first compute the Topology (which can be cost-intensive) and afterwards apply the `topoquantize` on the computed Topology.

<div id="embed_tuning_topoquantize"></div>



* * * 

## presimplify

###### boolean, float
{: .no_toc}

Apply presimplify to remove unnecessary points from linestrings before the 
topology is constructed. This will simplify the input geometries. Use with care. 
Default is `False`.

* * * 

## toposimplify

###### boolean, float 
{: .no_toc}

Apply toposimplify to remove unnecessary points from arcs after the topology 
is constructed. This will simplify the constructed arcs without altering the 
topological relations. Sensible values for coordinates stored in degrees are 
in the range of `0.0001` to `10`. Defaults to `False`.


**Note 1:** The units of `toposimplify` are corresoponding to the input space. The provided _sensible_ values are for dgrees (eg. epsg:4326). When the projection of your data is in meters you might need to test which value should be adopted.

**Note 2:** This is also supported by chaining.




* * * 

## shared_coords

###### boolean
{: .no_toc}
Sets the strategy to detect junctions. When set to `True` a path is 
considered shared when all coordinates appear in both paths 
(`coords-connected`). When set to `False` a path is considered shared when 
coordinates are the same path (`path-connected`). The path-connected strategy 
is more 'correct', but slower. Default is `True`.


* * * 

## simplify_with

###### boolean
{: .no_toc}

If this setting is set to `True`, the simplification is slower, but the 
likelihood of producing valid geometries is higher as it prevents 
oversimplification. Simplification happens on paths separately, so this 
setting is especially relevant for rings with no partial shared paths. This 
is also known as a topology-preserving variant of simplification. 
Default is `True`. 

* * * 

## simplify_with

###### str
{: .no_toc}
Sets the package to use for simplifying (both pre- and toposimplify). Choose 
between `shapely` or `simplification`. Shapely adopts solely Douglas-Peucker 
and simplification both Douglas-Peucker and Visvalingam-Whyatt. The pacakge 
simplification is known to be quicker than shapely. 
Default is `shapely`.

* * * 

## simplify_algorithm

###### str
{: .no_toc}

Choose between `dp` and `vw`, for Douglas-Peucker or Visvalingam-Whyatt 
respectively. `vw` will only be selected if `simplify_with` is set to 
`simplification`. Default is `dp`, since it still "produces the most accurate 
generalization" (Chi & Cheung, 2006).

* * * 

## winding_order

###### str
{: .no_toc}

Determines the winding order of the features in the output geometry. Choose 
between `CW_CCW` for clockwise orientation for outer rings and counter-
clockwise for interior rings. Or `CCW_CW` for counter-clockwise for outer 
rings and clockwise for interior rings. Default is `CW_CCW`.




<script>
window.addEventListener("DOMContentLoaded", event => {
    var opt = {
        mode: "vega-lite",
        renderer: "svg",
        actions: false
    };

    var spec_topology = "{{site.baseurl}}/json/example_topology.vl.json";
    vegaEmbed("#embed_tuning_topology", spec_topology, opt).catch(console.err);
});
</script>
<script type="text/javascript" src="https://cdn.jsdelivr.net/npm/vega@5"></script>
<script type="text/javascript" src="https://cdn.jsdelivr.net/npm/vega-lite@4.0.0"></script>
<script type="text/javascript" src="https://cdn.jsdelivr.net/npm/vega-embed@6"></script>