---
layout: default
title: Incremental updates
parent: Example usage
nav_order: 4
---

# Incremental updates
{: .no_toc}

A Topology can be updated with features that are added, removed or changed,
without computing it again from the start. This is useful for a job that runs
often on a set of features of which most stay the same.

1. TOC
{:toc}

* * *

## add and remove

`add` puts new features in the Topology and `remove` takes features out, by their
id (the index of a GeoDataFrame). Arcs that are no longer used are removed, arcs
are cut where a new feature meets them, and shared borders stay shared.

Below, a Topology of the squares A, B and C (5 arcs). After `add(D)` the shared
sides are cut (8 arcs). After `remove(D)` they merge again:

<div class="code-example mx-1 bg-example">
<div class="example-label" markdown="1">
Example 🔧
{: .label .label-blue-000 }
</div>
<div class="example-text" markdown="1">

```python
import geopandas as gpd
import topojson as tp
from shapely.geometry import box

gdf = gpd.GeoDataFrame(
    geometry=[
        box(0, 1, 1, 2),
        box(1, 1, 2, 2),
        box(0, 0, 1, 1),
        box(1, 0, 2, 1),
    ],
    index=list("ABCD"),
)
topo = tp.Topology(gdf.loc[["A", "B", "C"]])
n0 = len(topo.output["arcs"])
topo.add(gdf.loc[["D"]])
n1 = len(topo.output["arcs"])
topo.remove(["D"])
n0, n1, len(topo.output["arcs"])
```
<pre class="code_no_highlight">
(5, 8, 5)
</pre>
<figure class="parts" data-src="{{site.baseurl}}/json/fig_incremental_add_remove.json" data-label="Add a square that shares two sides, then remove it"><svg></svg></figure>
</div>
</div>

* * *

## sync

`sync` makes the Topology equal to a complete set of features: new features are
added, features that are gone are removed, and features with a changed geometry
are replaced. Features are compared by a hash of their input geometry. What
happened is stored in `last_sync`.

To continue in a next run, write the Topology with `to_json(..., state=True)` and
read it with `Topology.read_json`. The file is a plain TopoJSON file with two extra
top-level members: `options`, the options of the Topology, and `source_hashes`, the
hash of the input geometry of each feature.

<div class="code-example mx-1 bg-example">
<div class="example-label" markdown="1">
Example 🔧
{: .label .label-blue-000 }
</div>
<div class="example-text" markdown="1">

Below, the next run drops A, changes C and adds E:
```python
tp.Topology(gdf).to_json("state.json", state=True)

second = gdf.loc[["B", "C", "D"]].copy()
second.loc["C", "geometry"] = second.loc["C", "geometry"].buffer(0.2)
second.loc["E", "geometry"] = box(2, 1, 3, 2)

topo = tp.Topology.read_json("state.json").sync(second)
topo.last_sync
```
<pre class="code_no_highlight">
{'added': 1, 'removed': 1, 'changed': 1, 'unchanged': 2}
</pre>
<figure class="parts" data-src="{{site.baseurl}}/json/fig_incremental_sync.json" data-label="A next run that drops A, changes C and adds E"><svg></svg></figure>

The same on a larger set, 40 features of which 5 are gone, 5 are new and one has
changed:
```python
africa = tp.Topology(tp.utils.example_data_africa(), prequantize=False).to_gdf()
tp.Topology(africa.iloc[:40]).to_json("state.json", state=True)

more = africa.iloc[5:45].copy()
more.loc[5, "geometry"] = more.loc[5, "geometry"].buffer(0.1)

tp.Topology.read_json("state.json").sync(more).last_sync
```
<pre class="code_no_highlight">
{'added': 5, 'removed': 5, 'changed': 1, 'unchanged': 34}
</pre>

A job that runs every few minutes on the complete set of features:
```python
from pathlib import Path

if not Path("state.json").exists():
    topo = tp.Topology(africa)
else:
    topo = tp.Topology.read_json("state.json").sync(africa)

topo.to_json("state.json", state=True)
topo.toposimplify(1).to_json("publish.json")
```
</div>
</div>

* * *

## Requirements

- The Topology is quantized (the default). The grid of the first Topology is kept,
  so new features are quantized on the same grid, see the fixed grid of
  [prequantize](settings-tuning.html#prequantize).
- Junctions are path-connected (`shared_coords=False`, the default).
- `add`, `remove` and `sync` work on the unsimplified arcs: apply `toposimplify` or
  `topoquantize` to the result, as in the job above, not to the Topology that is
  updated.
- The result has the same features, arcs and junctions as a Topology computed from
  the start on the same grid. After `remove` on its own, a ring can start at
  another vertex, and the bbox can differ by up to half a grid cell.

<script src="{{site.baseurl}}/js/steps.js" defer></script>
