---
layout: default
title: Types of input data
parent: Example usage
nav_order: 1
---

# Types of input data
{: .no_toc}

This library can be useful for you if you have if one of the following geographical input data:

1. TOC
{:toc}

* * * 

## GeoDataFrame or GeoSeries
From the package `geopandas` (not a hard dependency)

<div class="code-example mx-1 bg-example">
<div class="example-label" markdown="1">
Example 🔧
{: .label .label-blue-000 }
</div>
<div class="example-text" markdown="1">

```python
import topojson as tp
import geopandas
from shapely import geometry
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
</div>
</div>

* * * 


## FeatureCollection or Features
From the package `geojson` (not a hard dependency)

<div class="code-example mx-1 bg-example">
<div class="example-label" markdown="1">
Example 🔧
{: .label .label-blue-000 }
</div>
<div class="example-text" markdown="1">

```python
import topojson as tp
from geojson import Feature, Polygon, FeatureCollection


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
</div>
</div>

* * * 

## fiona.Collection
From the package `fiona` (not a hard dependency)

<div class="code-example mx-1 bg-example">
<div class="example-label" markdown="1">
Example 🔧
{: .label .label-blue-000 }
</div>
<div class="example-text" markdown="1">

```python
import topojson as tp
import fiona

with fiona.open('tests/files_shapefile/mesh2d.geojson') as fio_col:
    topo = tp.Topology(fio_col)

topo.to_svg()
```
<img src="../images/mesh2d.svg">
</div>
</div>

* * *

## `shapely.geometry` object
From the package `shapely`

<div class="code-example mx-1 bg-example">
<div class="example-label" markdown="1">
Example 🔧
{: .label .label-blue-000 }
</div>
<div class="example-text" markdown="1">

```python
import topojson as tp
from shapely import geometry

data = geometry.MultiLineString([
    [(0, 0), (10, 0), (10, 5), (20, 5)], 
    [(5, 0), (25, 0), (25, 5), (16, 5), (16, 10), (14, 10), (14, 5), (0, 5)]
])

tp.Topology(data).to_svg()
```
<img src="../images/shared_paths.svg">
</div>
</div>

* * * 

## object that support the `__geo_interface__` 
This example use the package `pyshp` (not a hard dependency)

<div class="code-example mx-1 bg-example">
<div class="example-label" markdown="1">
Example 🔧
{: .label .label-blue-000 }
</div>
<div class="example-text" markdown="1">

```python
import topojson as tp
import shapefile

data = shapefile.Reader("tests/files_shapefile/southamerica.shp")
topo = tp.Topology(data)
topo.toposimplify(4).to_svg()
```
<img src="../images/southamerica_toposimp.svg">
</div>
</div>

* * *

## `list` of objects that provide a valid `__geo_interface__` or can be parsed into one
The list should contain items that supports the `__geo_interface__`

<div class="code-example mx-1 bg-example">
<div class="example-label" markdown="1">
Example 🔧
{: .label .label-blue-000 }
</div>
<div class="example-text" markdown="1">

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
</div>
</div>

* * * 

## `dict` of objects that provide a valid `__geo_interface__` or can be parsed into one
The dictionary should be structured like {`key1`: `obj1`, `key2`: `obj2`}.

<div class="code-example mx-1 bg-example">
<div class="example-label" markdown="1">
Example 🔧
{: .label .label-blue-000 }
</div>
<div class="example-text" markdown="1">

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
</div>
</div>

* * * 

## TopoJSON file loaded as json-dict
A TopoJSON file can be postprocessed.

<div class="code-example mx-1 bg-example">
<div class="example-label" markdown="1">
Example 🔧
{: .label .label-blue-000 }
</div>
<div class="example-text" markdown="1">

```python
import topojson as tp
import json

with open("tests/files_topojson/naturalearth_lowres_africa.topojson", 'r') as f:
    data = json.load(f)
# parse topojson file using `object_name`
topo = topojson.Topology(data, object_name="data")
topo.toposimplify(4).to_svg()
```
<img src="../images/africa_toposimp.svg">
</div>
</div>