---
layout: default
title: Types of input data
parent: Example usage
nav_order: 1
---

# Types of input data

This library can be useful for you if you have if one of the following geographical input data:

- `geojson.Feature` or a `geojson.FeatureCollection`
- `geopandas.GeoDataFrame` or a `geopandas.GeoSeries`
- any `shapely.geometry` object (eg. `Multi-``LineString` / `Multi-``Polygon` / `Multi-``Point` / `GeometryCollection`)
- any object that support the `__geo_interface__`
- any object that can be parsed into a `__geo_interface__`
- `dict` of objects that provide a valid `__geo_interface__` or can be parsed into one
- `list` of objects that provide a valid `__geo_interface__` or can be parsed into one

* * * 

### Type: `list`
The list should contain items that supports the `__geo_interface__`

```python
import topojson as tp

list_in = [
    {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
    {"type": "Polygon", "coordinates": [[[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]]}
]

tp.Topology(list_in, prequantize=False).to_json()
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

* * * 

### Type: `dict`
The dictionary should be structured like {`key1`: `obj1`, `key2`: `obj2`}.

```python
import topojson as tp

dict_in = {
    0: {
        "type": "Polygon",
        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
    },
    1: {
        "type": "Polygon",
        "coordinates": [[[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]],
    }
}

tp.Topology(dict_in, prequantize=False).to_json()
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

* * * 

### Type: `GeoDataFrame` 
From the package `geopandas` (if installed)

```python
import geopandas
from shapely import geometry
import topojson as tp
%matplotlib inline

gdf = geopandas.GeoDataFrame({
    "name": ["abc", "def"],
    "geometry": [
        geometry.Polygon([[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]),
        geometry.Polygon([[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]])
    ]
})
gdf.plot(column="name")
gdf.head()
```

|   | name| geometry                            |
|:--|:----|:------------------------------------|
| 0 | abc | POLYGON ((0 0, 1 0, 1 1, 0 1, 0 0)) |
| 1 | def | POLYGON ((1 0, 2 0, 2 1, 1 1, 1 0)) |


<img src="{{site.baseurl}}/images/geodataframe_plot.png" alt="Plot GeoDataFrame">

```python
tp.Topology(gdf, prequantize=False).to_json()
```

```python
{
    "type": "Topology",
    "objects": {
        "data": {
            "geometries": [
                {
                    "id": "0",
                    "type": "Polygon",
                    "properties": {"name": "abc"},
                    "bbox": [0.0, 0.0, 1.0, 1.0],
                    "arcs": [[-2, 0]]
                },
                {
                    "id": "1",
                    "type": "Polygon",
                    "properties": {"name": "def"},
                    "bbox": [1.0, 0.0, 2.0, 1.0],
                    "arcs": [[1, 2]]
                }
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

* * * 

### Type: `FeatureCollection` 
From the package `geojson` (if installed)

```python
from geojson import Feature, Polygon, FeatureCollection
import topojson as tp

feat_1 = Feature(
    geometry=Polygon([[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]),
    properties={"name":"abc"}
)
feat_2 = Feature(
    geometry=Polygon([[[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]]),
    properties={"name":"def"}
)
fc = FeatureCollection([feat_1, feat_2])

tp.Topology(fc, prequantize=False).to_json()
```

```python
{
    "type": "Topology",
    "objects": {
        "data": {
            "geometries": [
                {"type": "Polygon", "properties": {"name": "abc"}, "arcs": [[-2, 0]]},
                {"type": "Polygon", "properties": {"name": "def"}, "arcs": [[1, 2]]}
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
