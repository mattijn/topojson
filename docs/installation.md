---
layout: default
title: Installation
nav_order: 2
---

# Installation

Topojson is available on PyPI and conda-forge:

```bash
pip install topojson
```

In a project managed with [uv](https://docs.astral.sh/uv/):

```bash
uv add topojson
```

Or with conda:

```bash
conda install -c conda-forge topojson
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
                {"type": "Polygon", "arcs": [[-2, 0]], "id": 0},
                {"type": "Polygon", "arcs": [[1, 2]], "id": 1}
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

For other simplification options in the `presimplify`/`toposimplify` parameter settings you can install (_optional_):

- `simplification`: Visvalingam-Whyatt, and a Douglas-Peucker that is quicker on long lines but does not prevent oversimplification.

For polygons, `presimplify` with `simplify_with="geos"` uses Visvalingam-Whyatt from shapely without this package, and keeps shared borders matched.

To visualize the output as a mesh and/or return the output as geodataframe you will need (_optional_):

- `altair`
- `geopandas`

To interactively analyze the effects of `toposimplify` and `topoquantize` as a widget, you also need (_optional_):

- `ipywidgets`


## Development Install

To run the full test suite a few additional dependencies are required, next to the hard and soft dependencies:

- `pytest`
- `geojson`
- `pyshp` (to be able to do `import shapefile`)
