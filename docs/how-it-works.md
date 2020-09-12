---
layout: default
title: How it works
nav_order: 4
---

# How it works

With topojson it is possible to reduce the file size of your geographical data. This is often useful if you are aiming for browser-based visualizations (eg. visualizations in JupyterLab or on the Web).

As explained before we can do so through:

1. Eliminating redundancy through computation of a topology
2. Fixed-precision integer encoding of coordinates and
3. Simplification and quantization of arcs

## Topology computation

While the 2nd and 3rd bullets from above list have a significant impact on the filesize reduction, we will describe here the 1st bullet _-the computation of the Topology-_ since it is basically the core of this library.

The following example data is used in this description:

<div class="code-example mx-1 bg-example">
<div class="example-label" markdown="1">
Example 🔧
{: .label .label-blue-000 }
</div>
<div class="example-text" markdown="1">

```python
from IPython.display import display, SVG
from shapely import geometry
import topojson as tp

data = geometry.MultiLineString([
    [(0, 0), (10, 0), (5, 5), (15, 5)], 
    [(15, 0), (15, 5), (10, 5), (0, 5)]
])

s = data._repr_svg_()
s = s.replace('stroke="#66cc99"', 'stroke="#F37929"', 1)
s = s.replace('stroke-width="0.324"', 'stroke-width="0.7"', 1)
display(SVG(s))
```
<img src="images/two_linestring_orange.svg">

The orange line starts bottom-left and goes with a zig-zag to top-right. The green line starts bottom-right and goes up and then leftwards. Resulting in a shared segment for the two linestrings in opposite directions.
</div>
</div>

The computation of the Topology consists of the following sequence:

1. `extract`:
   - Detection of geometrical type of the object
   - Extraction of linestrings from the object

<div class="code-example mx-1 bg-example">
<div class="example-label" markdown="1">
Example 🔧
{: .label .label-blue-000 }
</div>
<div class="example-text" markdown="1">

```python
from topojson.core.extract import Extract
Extract(data)
```
<pre class="code_no_highlight">
Extract(
{'bookkeeping_coords': [],
 'bookkeeping_geoms': [[0], [1]],
 'coordinates': [],
 'linestrings': [<shapely.geometry.linestring.LineString object at 0x0000020C4B5B2E08>,
                 <shapely.geometry.linestring.LineString object at 0x0000020C4B5B2AC8>],
 'objects': {0: {'arcs': [0, 1], 'type': 'MultiLineString'}},
 'type': 'Topology'}
)
</pre>
The Extract class creates an object with a fews different keys. From top to bottom are these
- `bookkeeping_coords` which stores the references to all point-coordinates. In this input are no existing point-coordinates.
- `bookkeeping_geoms` which stores the references to all geometries, such as LineStrings and Polygons.
- `coordinates` the actual point-coordinates
- `linestrings` all actual LineStrings extracted from both Polygons, LineStrings and LinearRings.
- `objects` a dictionary with all input objects. Here is presented a single MultiLineString with two referenced arcs.

The two referenced arcs `[0, 1]` refer to `0`-index and `1`-index entry in the `bookkeeping_geoms`. In this case `[0]` and `[1]` respectively.
</div>
</div>

2. `join`:
   - Quantization of input linestrings if necessary
   - Identifies junctions of shared paths
3. `cut`:
   - Split linestrings given the junctions of shared paths
   - Identifies indexes of linestrings that are duplicates
4. `dedup`:
   - Deduplication of linestrings that contain duplicates
   - Merge contiguous arcs
5. `hashmap`:
   - Resolves bookkeeping results to object arcs.

The names are borrowed from the JavaScript variant of TopoJSON, to establish a certain synergy between the packages, even though the code differs significant (and sometimes even the TopoJSON output).

The addopted approach involves secure bookkeeping on multiple levels in order to succesfully pass all steps.