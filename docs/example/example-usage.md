---
layout: default
title: Example usage
nav_order: 3
nav_active_show: 2
has_children: true
permalink: /example-usage
nav_no_fold : true
--- 

# Example usage


The most common usage of Python Topojson is to first compute the Topology, often including prequantization (`prequantize`).

Using the computed Topology apply the `toposimplify` and settings and visualize till pleased.


The following code-snippet is an example of such:

```python
import topojson as tp

# load example data representing continental Africa
data = tp.utils.example_data_africa()  

# compute the topology
topo = tp.Topology(data)  

# apply simplification on the topology and render as SVG
topo.toposimplify(10).to_svg()
```
<img src="./images/africa_toposimp.svg">

This page is further subdivided in the following three sections for more detailed description and usages: 

