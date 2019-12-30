---
layout: default
title: Installation
nav_order: 2
---

# Installation

Topojson can be installed through PyPI by the following command:

```
python3 -m pip install topojson
```

The library is installed succesfully if the following code will not give you any errors.

```python
import topojson as tp

data = [
    {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
    {"type": "Polygon", "coordinates": [[[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]]}
]

tp.Topology(data, prequantize=False).to_json()
```

```python
{
    "type": "Topology",
    "objects": {
        "data": {
            "geometries": [
                {"type": "Polygon", "arcs": [[-2, 0]]}, {"type": "Polygon", "arcs": [[1, 2]]}
            ],
            "type": "GeometryCollection"
        }
    },
    "bbox": [0.0, 0.0, 2.0, 1.0],
    "arcs": [
        [[1.0, 0.0], [0.0, 0.0], [0.0, 1.0], [1.0, 1.0]], [[1.0, 0.0], [1.0, 1.0]],
        [[1.0, 1.0], [2.0, 1.0], [2.0, 0.0], [1.0, 0.0]]
    ]
}
```

## Dependencies

Topojson has the following minimal dependencies, all of which are installed automatically with the above installation commands:

- numpy
- shapely

To improve the speed of `pre`/`toposimplify` or if you want to use another simplification algorithm you can install (_optional_):

- simplification

To visualise the output as a mesh and/or return the output as geodataframe you also will need (_optional_):

- altair
- geopandas

## Development Install

To run the full test suite a few additional dependencies are required:

- unittest
- fiona
- geopandas
- geojson
- pyshp
