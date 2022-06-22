---
layout: default
title: Installation
nav_order: 2
---

# Installation

Topojson can be installed through PyPI by the following command:

```
python -m pip install topojson
```

And through conda using the following command:

```
conda install topojson -c conda-forge
```

The library is installed successfully if the following code.

```python
import topojson as tp

data = [
    {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
    {"type": "Polygon", "coordinates": [[[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]]}
]

topo = tp.Topology(data, prequantize=False)
print(topo.to_json(pretty=True))
```
Returns something as such:

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

* * *

#### Hard Dependencies
Topojson requires `numpy` and `shapely`. These are installed automatically if not available.

* * *

#### Soft Dependencies

To improve the speed of the `presimplify`/`toposimplify` parameter settings or if you want to use another simplification algorithm you can install (_optional_):

- `simplification`

To visualize the output as a mesh and/or return the output as geodataframe you will need (_optional_):

- `altair`
- `geopandas`

To interactively analyze the effects of `toposimplify` and `topoquantize` as a widget, you also need (_optional_):

- `ipywidgets`
- `ipywidgets` JupyterLab extension


## Development Install

To run the full test suite a few additional dependencies are required, next to the hard and soft dependencies:

- `pytest`
- `geojson`
- `pyshp` (to be able to do `import shapefile`)
