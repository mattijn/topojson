---
layout: default
title: Example usage
nav_order: 3
has_children: true
permalink: /example-usage
--- 

# Example usage

The most common usage op topojson is to first compute the topology.

Using the computed topology apply the `toposimplify` and `topoquantize` settings and visualize till pleased.

The following code-snippet is an example of such:

```python
import topojson as tp

tj = tp.Topology(your_geo_data)
tj.toposimplify(1).topoquantize(1e6).to_svg()
```

This page is further subdivided in the following three sections for more detailed description and usages: 

- The first section describes what type of data types can be parsed into Python TopoJSON.
- The second sections is going about what type of settings can be provided in order to derive the TopoJSON.
- In the third section is shown how to derive different types of output from the computed TopoJSON.


