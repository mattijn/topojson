---
layout: default
title: Settings and tuning
parent: Example usage
nav_order: 2
---

# Settings and tuning

The TopoJSON format is merely designed to create smaller files than its GeoJSON counterpart. It is capable of doing so through a few options of which the following are currently available: 
- compute topology 
- quantize the input and/or output
- simplify the input and/or output.

The following parameters can be used to control these options for generating the `Topology()` object. 

Each option should be explained with an interactive example (can it?) to see the effects.
Currently its merely copied from the docstring in the code L.

* * * 

## topology

> ###### boolean
Specifiy if the topology should be computed for deriving the TopoJSON.
Default is `True`.


<!-- **Note:** The following figure is here to test if interactivity is possible

<div id="embed_tuning_topology"></div> -->


* * *         

## prequantize

> ###### boolean, int
If the prequantization parameter is specified, the input geometry is 
quantized prior to computing the topology, the returned topology is 
quantized, and its arcs are delta-encoded. Quantization is recommended to 
improve the quality of the topology if the input geometry is messy (i.e., 
small floating point error means that adjacent boundaries do not have 
identical values); typical values are powers of ten, such as `1e4`, `1e5` or 
`1e6`. Default is `True` (which correspond to a quantize factor of `1e6`).

* * * 

## topoquantize

> ###### boolean or int
If the topoquantization parameter is specified, the input geometry is quantized 
after the topology is constructed. If the topology is already quantized this 
will be resolved first before the topoquantization is applied. See for more 
details the `prequantize` parameter. Default is `False`.

**Note:** This is also supported by chaining.

<div id="embed_tuning_topoquantize"></div>



* * * 

## presimplify

> ###### boolean, float
Apply presimplify to remove unnecessary points from linestrings before the 
topology is constructed. This will simplify the input geometries. Use with care. 
Default is `False`.

* * * 

## toposimplify

> ###### boolean, float 
Apply toposimplify to remove unnecessary points from arcs after the topology 
is constructed. This will simplify the constructed arcs without altering the 
topological relations. Sensible values for coordinates stored in degrees are 
in the range of `0.0001` to `10`. Defaults to `False`.


**Note 1:** The units of `toposimplify` are corresoponding to the input space. The provided _sensible_ values are for dgrees (eg. epsg:4326). When the projection of your data is in meters you might need to test which value should be adopted.

**Note 2:** This is also supported by chaining.


<!-- <div class="code-example mx-8 bg-contribution">
<div class="contribution-label" markdown="1">
Contribution 🙏
{: .label .label-yellow }
</div>
<div class="contribution-text" markdown="1">

_I don't really know what the current input value means, but I do know that there is currently NO option to use a %-value (like in mapshaper.org)._

_It would be a great contribution if you can make the `toposimplifiy` setting work using percentage as input!_
</div>
</div> -->

* * * 

## shared_coords

> ###### boolean
Sets the strategy to detect junctions. When set to `True` a path is 
considered shared when all coordinates appear in both paths 
(`coords-connected`). When set to `False` a path is considered shared when 
coordinates are the same path (`path-connected`). The path-connected strategy 
is more 'correct', but slower. Default is `True`.


* * * 

## simplify_with

> ###### boolean
If this setting is set to `True`, the simplification is slower, but the 
likelihood of producing valid geometries is higher as it prevents 
oversimplification. Simplification happens on paths separately, so this 
setting is especially relevant for rings with no partial shared paths. This 
is also known as a topology-preserving variant of simplification. 
Default is `True`. 

* * * 

## simplify_with

> ###### str
Sets the package to use for simplifying (both pre- and toposimplify). Choose 
between `shapely` or `simplification`. Shapely adopts solely Douglas-Peucker 
and simplification both Douglas-Peucker and Visvalingam-Whyatt. The pacakge 
simplification is known to be quicker than shapely. 
Default is `shapely`.

* * * 

## simplify_algorithm

> ###### str
Choose between `dp` and `vw`, for Douglas-Peucker or Visvalingam-Whyatt 
respectively. `vw` will only be selected if `simplify_with` is set to 
`simplification`. Default is `dp`, since it still "produces the most accurate 
generalization" (Chi & Cheung, 2006).

* * * 

## winding_order

> ###### str
Determines the winding order of the features in the output geometry. Choose 
between `CW_CCW` for clockwise orientation for outer rings and counter-
clockwise for interior rings. Or `CCW_CW` for counter-clockwise for outer 
rings and clockwise for interior rings. Default is `CW_CCW`.

* * * 

## Chaining
The `toposimplify` and `topoquantize` are supported by chaining as well. Meaning you could first compute the Topology (which can be cost-intensive) and afterwards apply the simplify and quantize settings on the computed Topology and visualize till pleased.


```python
import topojson as tp

tj = tp.Topology(data, prequantize=False, topology=True)
tj.toposimplify(1).topoquantize(1e6).to_svg()
```


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