---
layout: default
title: Settings and tuning possibilities
parent: Example usage
nav_order: 2
---

# Settings and tuning possibilities

The TopoJSON format is merely designed to create smaller files than its GeoJSON counterpart. It is capable of doing so through a few options of which the following are currently available: 
- compute topology 
- quantize the input and/or output
- simplify the input and/or output.

The following parameters can be used to control these options for generating the Topology() object. 

Each option should be explained with an interactive example (can it?) to see the effects.
Currently its merely copied from the docstring in the code L.

* * * 

## topology
    topology : boolean
        Specifiy if the topology should be computed for deriving the TopoJSON. 
        Default is True. 


<div class="code-example mx-8 bg-grey-lt-000">
<div class="note-label" markdown="1">
Note 📝
{: .label .label-blue }
</div>
<div class="note-text" markdown="1">

_(the following figure is for testing only)_

</div>
</div>
<div id="embed_tuning_topology"></div>

* * *         

## prequantize

    prequantize : boolean, int
        If the prequantization parameter is specified, the input geometry is quantized
        prior to computing the topology, the returned topology is quantized, and its 
        arcs are delta-encoded. Quantization is recommended to improve the quality of 
        the topology if the input geometry is messy (i.e., small floating point error 
        means that adjacent boundaries do not have identical values); typical values 
        are powers of ten, such as 1e4, 1e5 or 1e6. Default is True (which correspond 
        to a quantize factor of 1e6).

* * * 

## topoquantize

    topoquantize : boolean or int
        If the topoquantization parameter is specified, the input geometry is quantized 
        after the topology is constructed. If the topology is already quantized this 
        will be resolved first before the topoquantization is applied. 
        Default is False.

<div class="code-example mx-8 bg-grey-lt-000">
<div class="note-label" markdown="1">
Note 📝
{: .label .label-blue }
</div>
<div class="note-text" markdown="1">

1.  _This is also supported by chaining._
</div>
</div>
<div id="embed_tuning_topoquantize"></div>



* * * 

## presimplify

    presimplify : boolean, float
        Apply presimplify to remove unnecessary points from linestrings before the 
        topology is constructed. This will simplify the input geometries. 
        Default is False.

* * * 

## toposimplify

    toposimplify : boolean, float 
        Apply toposimplify to remove unnecessary points from arcs after the topology is 
        constructed. This will simplify the constructed arcs without altering the 
        topological relations. Sensible values are in the range of 0.0001 to 10. 
        Defaults to 0.0001.



<div class="code-example mx-8 bg-grey-lt-000">
<div class="note-label" markdown="1">
Note 📝
{: .label .label-blue }
</div>
<div class="note-text" markdown="1">

1.  _I noticed that the default value work best when your data is projected in degrees (eg. epsg:4326). When the projection of your data is in meters you might need to test which value should be adopted._

2.  _This is also supported by chaining._

</div>
</div>


<div class="code-example mx-8 bg-grey-lt-000">
<div class="contribution-label" markdown="1">
Contribution 🙏
{: .label .label-yellow }
</div>
<div class="contribution-text" markdown="1">

_I don't really know what the current input value means, but I do know that there is currently NO option to use a %-value (like in mapshaper.org)._

_It would be a great contribution if you can make the `toposimplifiy` setting work using percentage as input!_
</div>
</div>


* * * 

## simplify_with

    simplify_with : str
        Sets the package to use for simplifying (both pre- and toposimplify). Choose 
        between `shapely` or `simplification`. Shapely adopts solely Douglas-Peucker 
        and simplification both Douglas-Peucker and Visvalingam-Whyatt. The pacakge 
        simplification is known to be quicker than shapely. 
        Default is `shapely`.

* * * 

## simplify_algorithm

    simplify_algorithm : str
        Choose between `dp` and `vw`, for Douglas-Peucker or Visvalingam-Whyatt 
        respectively. `vw` will only be selected if `simplify_with` is set to 
        `simplification`. Default is `dp`, since it still _"produces the most accurate 
        generalization"_ (Chi & Cheung, 2006).

* * * 

## winding_order

    winding_order : str
        Determines the winding order of the features in the output geometry. Choose 
        between `CW_CCW` for clockwise orientation for outer rings and counter-clockwise
        for interior rings. Or `CCW_CW` for counter-clockwise for outer rings and 
        clockwise for interior rings. Default is `CW_CCW`.

* * * 

## Chaining
The `toposimplify` and `topoquantize` are supported by chaining as well. Meaning you could first compute the Topology (which can be cost-intensive) and afterwards apply the simplify and quantize settings on the computed Topology and visualize till pleased.


```python
import topojson as tp

tj = tp.Topology(data, prequantize=False, topology=True)
tj.toposimplify(1).topoquantize(1e6).to_svg()
```

<script type="text/javascript" src="/topojson/example/tuning_embed.js"></script>
<script type="text/javascript" src="https://cdn.jsdelivr.net/npm/vega@5"></script>
<script type="text/javascript" src="https://cdn.jsdelivr.net/npm/vega-lite@4.0.0"></script>
<script type="text/javascript" src="https://cdn.jsdelivr.net/npm/vega-embed@6"></script>