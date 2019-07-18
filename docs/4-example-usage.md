---
layout: default
title: Example usage
nav_order: 4
---

<h1>Example Usage</h1>

If you have geographical input data which object type is in the following list, you have good luck this library is useful for you:

- `geojson.Feature`
- `geojson.FeatureCollection`
- `geopandas.GeoDataFrame`
- `geopandas.GeoSeries`
- `shapely.geometry.LineString`
- `shapely.geometry.MultiLineString`
- `shapely.geometry.Polygon`
- `shapely.geometry.MultiPolygon`
- `shapely.geometry.Point`
- `shapely.geometry.MultiPoint`
- `shapely.geometry.GeometryCollection`
- `dict` of objects that provide a valid `__geo_interface__`
- `list` of objects that provide a valid `__geo_interface__`

### Type: `list`

The list should contain items that supports the **geo**interface\_\_

```python
import topojson

list_geoms = [
    {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
    {"type": "Polygon", "coordinates": [[[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]]}
]
```

#

```python
topojson.topology(list_geoms)
```

```python
    {'type': 'Topology',
     'objects': {'data': {'geometries': [{'type': 'Polygon', 'arcs': [[-3, 0]]},
        {'type': 'Polygon', 'arcs': [[1, 2]]}],
       'type': 'GeometryCollection'}},
     'arcs': [[[1.0, 1.0], [0.0, 1.0], [0.0, 0.0], [1.0, 0.0]],
      [[1.0, 0.0], [2.0, 0.0], [2.0, 1.0], [1.0, 1.0]],
      [[1.0, 1.0], [1.0, 0.0]]]}
```

#

### Type: `dict`

The dictionary should be structured like {`key1`: `obj1`, `key2`: `obj2`}.

```python
import topojson

dictionary = {
    "abc": {
        "type": "Polygon",
        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
    },
    "def": {
        "type": "Polygon",
        "coordinates": [[[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]],
    }
}
```

#

```python
topojson.topology(dictionary)
```

```python
    {'type': 'Topology',
     'objects': {'data': {'geometries': [{'type': 'Polygon', 'arcs': [[-3, 0]]},
        {'type': 'Polygon', 'arcs': [[1, 2]]}],
       'type': 'GeometryCollection'}},
     'arcs': [[[1.0, 1.0], [0.0, 1.0], [0.0, 0.0], [1.0, 0.0]],
      [[1.0, 0.0], [2.0, 0.0], [2.0, 1.0], [1.0, 1.0]],
      [[1.0, 1.0], [1.0, 0.0]]]}
```

#

### Type: `GeoDataFrame` from package `geopandas` (if installed)

```python
import geopandas
import topojson
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

<div>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>name</th>
      <th>geometry</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>abc</td>
      <td>POLYGON ((0 0, 1 0, 1 1, 0 1, 0 0))</td>
    </tr>
    <tr>
      <th>1</th>
      <td>def</td>
      <td>POLYGON ((1 0, 2 0, 2 1, 1 1, 1 0))</td>
    </tr>
  </tbody>
</table>
</div>

<img src="../images/geodataframe_plot.png" alt="Plot GeoDataFrame">

#

```python
topojson.topology(gdf)
```

```python
    {'type': 'Topology',
     'objects': {'data': {'geometries': [{'id': '0',
         'type': 'Polygon',
         'properties': {'name': 'abc'},
         'bbox': (0.0, 0.0, 1.0, 1.0),
         'arcs': [[-3, 0]]},
        {'id': '1',
         'type': 'Polygon',
         'properties': {'name': 'def'},
         'bbox': (1.0, 0.0, 2.0, 1.0),
         'arcs': [[1, 2]]}],
       'type': 'GeometryCollection'}},
     'arcs': [[[1.0, 1.0], [0.0, 1.0], [0.0, 0.0], [1.0, 0.0]],
      [[1.0, 0.0], [2.0, 0.0], [2.0, 1.0], [1.0, 1.0]],
      [[1.0, 1.0], [1.0, 0.0]]]}
```

#

### Type: `FeatureCollection` from package `geojson` (if installed)

```python
from geojson import Feature, Polygon, FeatureCollection

feature_1 = Feature(
    geometry=Polygon([[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]),
    properties={"name":"abc"}
)
feature_2 = Feature(
    geometry=Polygon([[[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]]),
    properties={"name":"def"}
)
feature_collection = FeatureCollection([feature_1, feature_2])
```

#

```python
topojson.topology(feature_collection)
```

```python
    {'type': 'Topology',
     'objects': {'data': {'geometries': [{"arcs": [[-3, 0]], "properties": {"name": "abc"}, "type": "Polygon"},
        {"arcs": [[1, 2]], "properties": {"name": "def"}, "type": "Polygon"}],
       'type': 'GeometryCollection'}},
     'arcs': [[[1.0, 1.0], [0.0, 1.0], [0.0, 0.0], [1.0, 0.0]],
      [[1.0, 0.0], [2.0, 0.0], [2.0, 1.0], [1.0, 1.0]],
      [[1.0, 1.0], [1.0, 0.0]]]}
```
