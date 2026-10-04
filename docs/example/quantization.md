---
layout: default
title: Quantization
parent: Example usage
nav_order: 5
---

# Quantization
{: .no_toc}

By default, a Topology snaps all coordinates to a grid of integers before it computes
the topology (`prequantize`). Borders that are almost equal become exactly equal, so
shared paths are found reliably, and the integer coordinates are stored as small
differences (delta encoding). This page shows what the grid looks like and how to
choose it yourself.

1. TOC
{:toc}

* * *

## The grid

The grid is a TopoJSON transform: a `translate` (`x0`, `y0`), the bottom-left corner,
and a `scale` (`kx`, `ky`), the size of a cell along each axis. A coordinate `(x, y)`
becomes the integer coordinate `(round((x - x0) / kx), round((y - y0) / ky))`: each
vertex moves to the nearest point of the grid.

With `prequantize=n` (default `True`, which is `1e5`), the grid is derived from the
bounding box of the input: each axis is divided into the same number of steps,

```
kx = (x1 - x0) / (n - 1)
ky = (y1 - y0) / (n - 1)
```

so both axes are quantized, each with its own cell size.

Below, a line of 6 vertices (blue) on two coarse grids (dots). Each vertex moves to
the nearest point of the grid, which gives the quantized line (dashed). On the left
the grid of `prequantize=5`, on the right a grid with square cells of 2 (see
[square cells](#square-cells)):

<div class="code-example mx-1 bg-example">
<div class="example-label" markdown="1">
Example 🔧
{: .label .label-blue-000 }
</div>
<div class="example-text" markdown="1">

```python
import topojson as tp
from shapely.geometry import LineString

line = LineString([(0, 1), (2.6, 4.6), (5.3, 3.9), (7.1, 6), (9.6, 0), (12, 3.4)])
topo = tp.Topology(line, prequantize=5)
topo.output["transform"]
```
<pre class="code_no_highlight">
{'scale': [3.0, 1.5], 'translate': [0.0, 0.0]}
</pre>
<div id="embed_quantization_snap"></div>
</div>
</div>

* * *

## The cells follow the bounding box

As both axes get the same number of steps, a cell has the shape of the bounding box.
The line above is 12 wide and 6 high, so with `prequantize=5` its cells are 3 wide
and 1.5 high. A vertex can move up to half a cell, so up to 1.5 along `x` and only
0.75 along `y`.

The same happens with real data. Mainland Chile is 12.6° wide and 38.4° high, so its
cells are about three times higher than wide:

<div class="code-example mx-1 bg-example">
<div class="example-label" markdown="1">
Example 🔧
{: .label .label-blue-000 }
</div>
<div class="example-text" markdown="1">

```python
import geopandas as gpd

countries = gpd.read_file(
    "https://d2ad6b4ur7yvpq.cloudfront.net/naturalearth-3.3.0/"
    "ne_50m_admin_0_countries.geojson"
)
chile = countries.query("name == 'Chile'")[["name", "geometry"]]
chile = chile.clip((-80, -60, -60, -15))  # the mainland, without Easter Island

topo = tp.Topology(chile)
topo.output["transform"]
```
<pre class="code_no_highlight">
{'scale': [0.00012553787647251398, 0.0003838602839153395],
 'translate': [-78.98945312499993, -55.891699218750006]}
</pre>
</div>
</div>

Halfway Chile (36.7°S), that is a cell of 11 m east-west by 42 m north-south. On a
coarse grid (`prequantize=40`) the difference is easy to see. On the left the grid
from the bounding box, on the right a grid with square cells (see
[below](#square-cells)):

<div class="code-example mx-1 bg-example">
<div class="example-label" markdown="1">
Example 🔧
{: .label .label-blue-000 }
</div>
<div class="example-text" markdown="1">
<div id="embed_quantization_cells"></div>
</div>
</div>

The bounding box also depends on all features. With Easter Island, more than 3,500 km
to the west, Chile is 43° wide, and the cells become 0.00043° wide: 3.4 times coarser
east-west for every coordinate of the mainland.

* * *

## Choose the grid yourself

Instead of a number, `prequantize` accepts a transform as a dict,
`{"scale": [kx, ky], "translate": [x0, y0]}`. The grid then does not depend on the
input, and the precision is what you choose.

### Precision in the units of the data

For data in a projected coordinate system in metres, a scale of `[0.01, 0.01]` keeps
coordinates to the centimetre, whatever the size of the dataset:

```python
topo = tp.Topology(data, prequantize={"scale": [0.01, 0.01], "translate": [0, 0]})
```

### Square cells

With the same cell size along both axes, a vertex moves at most the same distance in
each direction, as in the right panel of the [figure above](#the-grid):

```python
topo = tp.Topology(line, prequantize={"scale": [2, 2], "translate": [0, 0]})
```

For data in degrees, a cell is square on the ground when `kx = ky / cos(latitude)`.
For Chile, at its middle latitude, with cells of about 44 m:

<div class="code-example mx-1 bg-example">
<div class="example-label" markdown="1">
Example 🔧
{: .label .label-blue-000 }
</div>
<div class="example-text" markdown="1">

```python
import numpy as np

x0, y0, x1, y1 = chile.total_bounds
k = 0.0004  # about 44 m north-south
square = {
    "scale": [k / np.cos(np.radians((y0 + y1) / 2)), k],
    "translate": [x0, y0],
}
topo = tp.Topology(chile, prequantize=square)
topo.output["transform"]
```
<pre class="code_no_highlight">
{'scale': [0.0004988853914682203, 0.0004],
 'translate': [-78.98945312499993, -55.891699218750006]}
</pre>
</div>
</div>

A long country spans many latitudes, so the cells are square only near the middle;
to the south they become narrower on the ground, to the north wider.

### Aligned with a raster

With the cell size and corner of a raster, the integer coordinates are the corners
of its pixels. Polygons derived from the raster, or drawn on top of it, then follow
its cells exactly:

<div class="code-example mx-1 bg-example">
<div class="example-label" markdown="1">
Example 🔧
{: .label .label-blue-000 }
</div>
<div class="example-text" markdown="1">

```python
from shapely.geometry import box

# a raster of 1 m cells, 400 rows, with its top-left corner at (155000, 463000)
left, top, cell, rows = 155000, 463000, 1.0, 400
grid = {"scale": [cell, cell], "translate": [left, top - rows * cell]}

parcel = gpd.GeoDataFrame(geometry=[box(155010.3, 462900.7, 155120.2, 462990.4)])
tp.Topology(parcel, prequantize=grid).to_gdf().geometry[0].exterior.coords[:]
```
<pre class="code_no_highlight">
[(155120.0, 462901.0),
 (155120.0, 462990.0),
 (155010.0, 462990.0),
 (155010.0, 462901.0),
 (155120.0, 462901.0)]
</pre>
</div>
</div>

### Different precision per axis

The two axes do not need the same unit. For a profile along a river, with the
distance in metres on `x` and the bed level in metres on `y`, a scale of `[1, 0.01]`
keeps the distance to the metre and the level to the centimetre.

* * *

## One grid for several topologies

Topologies computed on the same grid have exactly the same integer coordinates where
their inputs meet, also when they are computed separately: for example a layer of
countries and a layer of provinces, or a job that runs every day (see
[incremental updates](incremental-updates.html)). Take the transform of the first and
pass it to the others:

```python
grid = tp.Topology(provinces).output["transform"]
topo = tp.Topology(countries, prequantize=grid)
```

When the inputs are in one Topology (a list of objects, see
[input types](input-types.html)), they share one grid already.

* * *

## prequantize and topoquantize

`prequantize` sets the grid on which the topology is computed. `topoquantize` puts the
finished topology on a coarser grid, to make the file smaller; it takes a number
and derives the grid from the bounding box, as `prequantize` does:

<div class="code-example mx-1 bg-example">
<div class="example-label" markdown="1">
Example 🔧
{: .label .label-blue-000 }
</div>
<div class="example-text" markdown="1">

```python
topo = tp.Topology(chile)
len(topo.to_json()), len(topo.topoquantize(1e4).to_json())
```
<pre class="code_no_highlight">
(21960, 18093)
</pre>
</div>
</div>

A fine `prequantize` and a coarser `topoquantize` keep the topology exact and the
output small.

### Nested grids

`topoquantize` accepts a transform as a dict as well. A grid derived from the
bounding box is almost never a whole multiple of the grid of `prequantize`, so the
coarse points fall between the points of the fine grid. With cells that are a
multiple of the fine cells, from the same origin, every coarse point is a point of
the fine grid as well.

Below, the line on a fine grid with cells of 1 (dots, blue), put on a coarser grid
(lines, dashed). A vertex is filled when it lies on a point of the fine grid:

<div class="code-example mx-1 bg-example">
<div class="example-label" markdown="1">
Example 🔧
{: .label .label-blue-000 }
</div>
<div class="example-text" markdown="1">

```python
topo = tp.Topology(line, prequantize={"scale": [1, 1], "translate": [0, 0]})
left = topo.topoquantize(6)
right = topo.topoquantize({"scale": [3, 3], "translate": [0, 0]})
left.output["transform"], right.output["transform"]
```
<pre class="code_no_highlight">
({'scale': [2.4, 1.2], 'translate': [0.0, 0.0]},
 {'scale': [3.0, 3.0], 'translate': [0.0, 0.0]})
</pre>
<div id="embed_quantization_nested"></div>
</div>
</div>

Versions of the same data at several levels of detail then line up exactly, and the
output can be put on a grid with a meaning, such as 1 m, instead of one that follows
the bounding box.

* * *

## What quantization does not do

**It does not close gaps reliably.** Two coordinates closer than a cell can still
round to two neighbouring integers, when a cell boundary lies between them. Below,
the gap between `a1` and `a2` (0.04) is closed on a grid with cells of 0.1, while the
smaller gap between `b1` and `b2` (0.02) stays open, because 1.04 rounds to 10 and
1.06 to 11. The figure zooms in on the gaps:

<div class="code-example mx-1 bg-example">
<div class="example-label" markdown="1">
Example 🔧
{: .label .label-blue-000 }
</div>
<div class="example-text" markdown="1">

```python
rectangles = gpd.GeoDataFrame(
    {"name": ["a1", "a2", "b1", "b2"]},
    geometry=[
        box(0, 0, 1.0, 1),         # a1 and a2: a gap of 0.04
        box(1.04, 0, 2, 1),
        box(0, 1.2, 1.04, 2.2),    # b1 and b2: a gap of 0.02
        box(1.06, 1.2, 2, 2.2),
    ],
)
topo = tp.Topology(rectangles, prequantize=21)
[g["arcs"] for g in topo.output["objects"]["data"]["geometries"]]
```
<pre class="code_no_highlight">
[[[0, -2]], [[1, 2]], [[3]], [[4]]]
</pre>

`a1` and `a2` share arc `1` (`-2` is arc `1` reversed); `b1` and `b2` share nothing.

<div id="embed_quantization_gap"></div>
</div>
</div>

Quantization takes away small differences in coordinates that should be equal, such
as floating point noise. To close gaps, clean the input first, for example with
`shapely.snap`.

**A small ring can collapse.** A ring smaller than a cell can end up as a single
point or a line, without area. Such a ring is dropped: a small island from its
`MultiPolygon`, a small hole from its polygon. A feature of which nothing is left
keeps its properties, with an empty (`null`) geometry. Choose a grid that is fine
enough for the smallest features you want to keep.

<script>
window.addEventListener("DOMContentLoaded", event => {
    var opt = {
        mode: "vega-lite",
        renderer: "svg",
        actions: false
    };

    var spec_quantization_snap = "{{site.baseurl}}/json/example_quantization_snap.vl.json";
    vegaEmbed("#embed_quantization_snap", spec_quantization_snap, opt).catch(console.err);

    var spec_quantization_nested = "{{site.baseurl}}/json/example_quantization_nested.vl.json";
    vegaEmbed("#embed_quantization_nested", spec_quantization_nested, opt).catch(console.err);

    var spec_quantization_cells = "{{site.baseurl}}/json/example_quantization_cells.vl.json";
    vegaEmbed("#embed_quantization_cells", spec_quantization_cells, opt).catch(console.err);

    var spec_quantization_gap = "{{site.baseurl}}/json/example_quantization_gap.vl.json";
    vegaEmbed("#embed_quantization_gap", spec_quantization_gap, opt).catch(console.err);
});
</script>
<script type="text/javascript" src="https://cdn.jsdelivr.net/npm/vega@6"></script>
<script type="text/javascript" src="https://cdn.jsdelivr.net/npm/vega-lite@6"></script>
<script type="text/javascript" src="https://cdn.jsdelivr.net/npm/vega-embed@7"></script>
