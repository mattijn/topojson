---
layout: default
title: Installation
nav_order: 3
---

<h1>Installation</h1>

Topojson can be installed through PyPI by the following command:

```
python3 -m pip install topojson
```

The library is installed succesfully if the following code will not give you any errors.

```python
import topojson

data = [
    {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
    {"type": "Polygon", "coordinates": [[[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]]}
]

topojson.topology(data)
```

```

    {'type': 'Topology',
     'objects': {'data': {'geometries': [{'type': 'Polygon', 'arcs': [[0, -4, 1]]},
        {'type': 'Polygon', 'arcs': [[2, 3]]}],
       'type': 'GeometryCollection'}},
     'arcs': [[[0.0, 0.0], [1.0, 0.0]],
      [[1.0, 1.0], [0.0, 1.0], [0.0, 0.0]],
      [[1.0, 0.0], [2.0, 0.0], [2.0, 1.0], [1.0, 1.0]],
      [[1.0, 1.0], [1.0, 0.0]]]}

```

<h2>Dependencies</h2>
Topojson has the following minimal dependencies, all of which are installed automatically with the above installation commands:

- numpy
- shapely

If speed is any issue for you than the following optional packages might give you another boost in the topology computation:

- simplification
- numba (not yet included)

To run the full test suite and for buidling the documentation a few additional dependencies are required:

- unittest
- geojson
- fiona
- geopandas

<h2>Development Install</h2>

How to install?
