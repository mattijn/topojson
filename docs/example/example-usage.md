---
layout: default
title: Example usage
nav_order: 3
nav_active_show: 2
has_children: true
permalink: /example-usage
--- 

# Example usage

The most common usage of Python Topojson is to first compute the Topology.

Using the computed Topology apply the `toposimplify` and `topoquantize` settings and visualize till pleased.

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

- The first section describes what type of data types can be parsed into Python TopoJSON.
- The second sections is going about what type of settings can be provided in order to derive the TopoJSON.
- In the third section is shown how to derive different types of output from the computed TopoJSON.


