
# Types of input data

```python exec="on" session="exampleinput-types"
import threading
from concurrent.futures import ThreadPoolExecutor

import markdown_exec._internal.formatters.python as _python

# Zensical renders pages in parallel threads; GDAL and PROJ (geopandas) crash when
# they are used from more than one thread, so every example runs on one thread
with _python.__dict__.setdefault("_one_thread_lock", threading.Lock()):
    if not hasattr(_python, "_one_thread"):
        _python._one_thread = ThreadPoolExecutor(max_workers=1)
        _run = _python.exec_python

        def _exec_python(*args, **kwargs):
            return _python._one_thread.submit(_run, *args, **kwargs).result()

        _python.exec_python = _exec_python

import numpy as np
import topojson as tp


class _Drawing:
    def __getattr__(self, name):
        return lambda *args, **kwargs: self

    __or__ = __and__ = __add__ = lambda self, other: self


for _name in ["to_alt", "to_svg", "to_widget"]:
    setattr(tp.Topology, _name, lambda self, *args, **kwargs: _Drawing())
try:
    import geopandas

    geopandas.GeoDataFrame.plot = property(lambda self: lambda *a, **k: _Drawing())
except ImportError:
    pass
```

This library can be useful for you if you have if one of the following geographical input data:

1. [GeoDataFrame or GeoSeries](#geodataframe-or-geoseries)
2. [Polars DataFrame or Series](#polars-dataframe-or-series)
3. [GeoJSON data from file](#geojson-data-from-file)
4. [TopoJSON data from file](#topojson-data-from-file)
5. [FeatureCollection or Features](#featurecollection-or-features)
6. [fiona.Collection](#fionacollection)
7. [`shapely.geometry` object](#shapelygeometry-object)
8. [object that support the `__geo_interface__` ](#object-that-support-the-__geo_interface__)
9. [`list` of objects that provide a valid `__geo_interface__` or can be parsed into one](#list-of-objects-that-provide-a-valid-__geo_interface__-or-can-be-parsed-into-one)
10. [`dict` of objects that provide a valid `__geo_interface__` or can be parsed into one](#dict-of-objects-that-provide-a-valid-__geo_interface__-or-can-be-parsed-into-one)
11. [`list` of GeoDataFrames](#list-of-geodataframes)
12. [`list` of GeoJSON objects](#list-of-geojson-objects)

* * * 

## GeoDataFrame or GeoSeries
From the package `geopandas` (not a hard dependency). The index becomes the id of
each feature. A row can hold any geometry type, also a `GeometryCollection`.

!!! example


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

    ```python exec="on" session="exampleinput-types"
    import topojson as tp
    import geopandas
    from shapely import geometry

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


    <figure class="parts" data-src="../json/fig_input_geodataframe.json" data-label="The two squares abc and def"><svg></svg></figure>

    ```python
    tp.Topology(gdf, prequantize=False).to_json(pretty=True)
    ```

    ```python exec="on" session="exampleinput-types"
    tp.Topology(gdf, prequantize=False).to_json(pretty=True)
    ```

    ```python
    {
        "type": "Topology",
        "objects": {
            "data": {
                "geometries": [
                    {"properties": {"name": "abc"}, "type": "Polygon", "arcs": [[-2, 0]], "id": 0},
                    {"properties": {"name": "def"}, "type": "Polygon", "arcs": [[1, 2]], "id": 1}
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

    ```python exec="on" session="exampleinput-types"
    {
        "type": "Topology",
        "objects": {
            "data": {
                "geometries": [
                    {"properties": {"name": "abc"}, "type": "Polygon", "arcs": [[-2, 0]], "id": 0},
                    {"properties": {"name": "def"}, "type": "Polygon", "arcs": [[1, 2]], "id": 1}
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

## Polars DataFrame or Series
From the package `polars` (not a hard dependency), such as a GeoDataFrame of
[polars-st](https://github.com/oreilles/polars-st): a DataFrame with a column of
geometries as WKB or EWKB (`Binary`). The column `geometry` is used, or else the only
`Binary` column; the other columns become the properties. A Series of WKB works as
well, and a list of DataFrames with `object_name`, as for GeoDataFrames. If the
geometries share an SRID (EWKB), it becomes the CRS, also of `to_gdf()`.

!!! example

    ```python
    import polars_st as st
    import topojson as tp

    gdf = st.GeoDataFrame({
        "name": ["abc", "def"],
        "geometry": [
            "POLYGON ((0 0, 1 0, 1 1, 0 1, 0 0))",
            "POLYGON ((1 0, 2 0, 2 1, 1 1, 1 0))",
        ],
    })
    topo = tp.Topology(gdf, prequantize=False)
    print(topo.to_json(pretty=True))
    ```

    ```python exec="on" session="exampleinput-types" result="text"
    import polars_st as st
    import topojson as tp

    gdf = st.GeoDataFrame({
        "name": ["abc", "def"],
        "geometry": [
            "POLYGON ((0 0, 1 0, 1 1, 0 1, 0 0))",
            "POLYGON ((1 0, 2 0, 2 1, 1 1, 1 0))",
        ],
    })
    topo = tp.Topology(gdf, prequantize=False)
    print(topo.to_json(pretty=True))
    ```

* * *

## GeoJSON data from file
A GeoJSON file can be parsed as json dictionary.

!!! example


    ```python
    import topojson as tp
    import json

    with open("tests/files_geojson/example_data_africa.geojson", 'r') as f:
        data = json.load(f)

    assert data['type'] == 'FeatureCollection'
    topo = tp.Topology(data)

    # to visualize we use the (optional!) package Altair.
    topo.toposimplify(4).to_alt()
    ```

    ```python exec="on" session="exampleinput-types"
    import topojson as tp
    import json

    with open("tests/files_geojson/example_data_africa.geojson", 'r') as f:
        data = json.load(f)

    assert data['type'] == 'FeatureCollection'
    topo = tp.Topology(data)

    # to visualize we use the (optional!) package Altair.
    topo.toposimplify(4).to_alt()
    ```
    <div id="embed_output_mesh_altair_from_geojson">
</div>

* * * 

## TopoJSON data from file
A TopoJSON file can be post-processed using json dictionary.

!!! example


    ```python
    import topojson as tp
    import json

    with open("tests/files_topojson/naturalearth_lowres_africa.topojson", 'r') as f:
        data = json.load(f)
    # parse topojson file using `object_name`
    topo = tp.Topology(data, object_name="data")
    topo.toposimplify(4).to_svg()
    ```

    ```python exec="on" session="exampleinput-types"
    import topojson as tp
    import json

    with open("tests/files_topojson/naturalearth_lowres_africa.topojson", 'r') as f:
        data = json.load(f)
    # parse topojson file using `object_name`
    topo = tp.Topology(data, object_name="data")
    topo.toposimplify(4).to_svg()
    ```
    <figure class="parts" data-src="../json/fig_input_topojson.json" data-label="The arcs of Africa, simplified"><svg></svg></figure>


* * * 


## FeatureCollection or Features
From the package `geojson` (not a hard dependency)

!!! example


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

    tp.Topology(fc, prequantize=False).to_json(pretty=True)
    ```

    ```python exec="on" session="exampleinput-types"
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

    tp.Topology(fc, prequantize=False).to_json(pretty=True)
    ```

    ```python
    {
        "type": "Topology",
        "objects": {
            "data": {
                "geometries": [
                    {
                        "properties": {"name": "abc"}, "type": "Polygon", "arcs": [[-2, 0]], "id": "feature_0"
                    },
                    {"properties": {"name": "def"}, "type": "Polygon", "arcs": [[1, 2]], "id": "feature_1"}
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

    ```python exec="on" session="exampleinput-types"
    {
        "type": "Topology",
        "objects": {
            "data": {
                "geometries": [
                    {
                        "properties": {"name": "abc"}, "type": "Polygon", "arcs": [[-2, 0]], "id": "feature_0"
                    },
                    {"properties": {"name": "def"}, "type": "Polygon", "arcs": [[1, 2]], "id": "feature_1"}
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

## fiona.Collection
From the package `fiona` (not a hard dependency)

!!! example


    ```python
    import topojson as tp
    import fiona

    with fiona.open('tests/files_geojson/mesh2d.geojson') as fio_col:
        topo = tp.Topology(fio_col)

    topo.to_svg()
    ```

    ```python exec="on" session="exampleinput-types"
    import topojson as tp
    import fiona

    with fiona.open('tests/files_geojson/mesh2d.geojson') as fio_col:
        topo = tp.Topology(fio_col)

    topo.to_svg()
    ```
    <figure class="parts" data-src="../json/fig_input_fiona.json" data-label="The arcs of a mesh of triangles"><svg></svg></figure>


* * *

## `shapely.geometry` object
From the package `shapely`

!!! example


    ```python
    import topojson as tp
    from shapely import geometry

    data = geometry.MultiLineString([
        [(0, 0), (10, 0), (10, 5), (20, 5)], 
        [(5, 0), (25, 0), (25, 5), (16, 5), (16, 10), (14, 10), (14, 5), (0, 5)]
    ])

    tp.Topology(data).to_svg()
    ```

    ```python exec="on" session="exampleinput-types"
    import topojson as tp
    from shapely import geometry

    data = geometry.MultiLineString([
        [(0, 0), (10, 0), (10, 5), (20, 5)], 
        [(5, 0), (25, 0), (25, 5), (16, 5), (16, 10), (14, 10), (14, 5), (0, 5)]
    ])

    tp.Topology(data).to_svg()
    ```
    <figure class="parts" data-src="../json/fig_input_shapely.json" data-label="The arcs of two lines that share paths"><svg></svg></figure>


* * * 

## object that support the `__geo_interface__` 
This example use the package `pyshp` (not a hard dependency)

!!! example


    ```python
    import topojson as tp
    import shapefile

    data = shapefile.Reader("tests/files_shapefile/southamerica.shp")
    topo = tp.Topology(data)
    topo.toposimplify(4).to_svg()
    ```

    ```python exec="on" session="exampleinput-types"
    import topojson as tp
    import shapefile

    data = shapefile.Reader("tests/files_shapefile/southamerica.shp")
    topo = tp.Topology(data)
    topo.toposimplify(4).to_svg()
    ```
    <figure class="parts" data-src="../json/fig_input_geo_interface.json" data-label="The arcs of South America, simplified"><svg></svg></figure>


* * *

## `list` of objects that provide a valid `__geo_interface__` or can be parsed into one
The list should contain items that supports the `__geo_interface__`

!!! example


    ```python
    import topojson as tp

    list_in = [
        {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
        {"type": "Polygon", "coordinates": [[[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]]}
    ]

    tp.Topology(list_in, prequantize=False).to_json(pretty=True)
    ```

    ```python exec="on" session="exampleinput-types"
    import topojson as tp

    list_in = [
        {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
        {"type": "Polygon", "coordinates": [[[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]]}
    ]

    tp.Topology(list_in, prequantize=False).to_json(pretty=True)
    ```

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

    ```python exec="on" session="exampleinput-types"
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


* * * 

## `dict` of objects that provide a valid `__geo_interface__` or can be parsed into one
The dictionary should be structured like {`key1`: `obj1`, `key2`: `obj2`}.

!!! example


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

    tp.Topology(dict_in, prequantize=False).to_json(pretty=True)
    ```

    ```python exec="on" session="exampleinput-types"
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

    tp.Topology(dict_in, prequantize=False).to_json(pretty=True)
    ```

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

    ```python exec="on" session="exampleinput-types"
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


* * * 

## `list` of GeoDataFrames
From the package `geopandas` (not a hard dependency).

!!! example


    ```python
    import topojson as tp
    import geopandas as gpd
    from shapely import geometry

    gdf_1 = gpd.GeoDataFrame({
        "uniq_name": ["abc", "def"],
        "shrd_name": ["rect", "rect"],    
        "geometry": [
            geometry.Polygon([[1, 1], [2, 1], [2, 2], [1, 2], [1, 1]]),
            geometry.Polygon([[0, 1], [1, 1], [1, 2], [0, 2], [0, 1]])          
        ]
    })
    gdf_2 = gdf_1.dissolve(by='shrd_name', as_index=False)

    topo = tp.Topology(data=[gdf_1, gdf_2], object_name=['geom_1', 'geom_2'], prequantize=False)
    topo.to_dict()

    ```

    ```python exec="on" session="exampleinput-types"
    import topojson as tp
    import geopandas as gpd
    from shapely import geometry

    gdf_1 = gpd.GeoDataFrame({
        "uniq_name": ["abc", "def"],
        "shrd_name": ["rect", "rect"],    
        "geometry": [
            geometry.Polygon([[1, 1], [2, 1], [2, 2], [1, 2], [1, 1]]),
            geometry.Polygon([[0, 1], [1, 1], [1, 2], [0, 2], [0, 1]])          
        ]
    })
    gdf_2 = gdf_1.dissolve(by='shrd_name', as_index=False)

    topo = tp.Topology(data=[gdf_1, gdf_2], object_name=['geom_1', 'geom_2'], prequantize=False)
    topo.to_dict()
    ```

    ```python
    {'type': 'Topology',
     'objects': {'geom_1': {'geometries': [{'properties': {'uniq_name': 'abc',
          'shrd_name': 'rect'},
         'type': 'Polygon',
         'arcs': [[-1, 1]],
         'id': 0},
        {'properties': {'uniq_name': 'def', 'shrd_name': 'rect'},
         'type': 'Polygon',
         'arcs': [[0, 2]],
         'id': 1}],
       'type': 'GeometryCollection'},
      'geom_2': {'geometries': [{'properties': {'shrd_name': 'rect',
          'uniq_name': 'abc'},
         'type': 'Polygon',
         'arcs': [[1, 2]],
         'id': 0}],
       'type': 'GeometryCollection'}},
     'bbox': (0.0, 1.0, 2.0, 2.0),
     'arcs': [[[1.0, 2.0], [1.0, 1.0]],
      [[1.0, 2.0], [2.0, 2.0], [2.0, 1.0], [1.0, 1.0]],
      [[1.0, 1.0], [0.0, 1.0], [0.0, 2.0], [1.0, 2.0]]]}
    ```

    ```python exec="on" session="exampleinput-types"
    {'type': 'Topology',
     'objects': {'geom_1': {'geometries': [{'properties': {'uniq_name': 'abc',
          'shrd_name': 'rect'},
         'type': 'Polygon',
         'arcs': [[-1, 1]],
         'id': 0},
        {'properties': {'uniq_name': 'def', 'shrd_name': 'rect'},
         'type': 'Polygon',
         'arcs': [[0, 2]],
         'id': 1}],
       'type': 'GeometryCollection'},
      'geom_2': {'geometries': [{'properties': {'shrd_name': 'rect',
          'uniq_name': 'abc'},
         'type': 'Polygon',
         'arcs': [[1, 2]],
         'id': 0}],
       'type': 'GeometryCollection'}},
     'bbox': (0.0, 1.0, 2.0, 2.0),
     'arcs': [[[1.0, 2.0], [1.0, 1.0]],
      [[1.0, 2.0], [2.0, 2.0], [2.0, 1.0], [1.0, 1.0]],
      [[1.0, 1.0], [0.0, 1.0], [0.0, 2.0], [1.0, 2.0]]]}
    ```
    ```python
    topo.to_gdf(object_name='geom_2').plot(column='shrd_name')
    topo.to_gdf(object_name='geom_1').plot(column='uniq_name')
    ```

    ```python exec="on" session="exampleinput-types"
    topo.to_gdf(object_name='geom_2').plot(column='shrd_name')
    topo.to_gdf(object_name='geom_1').plot(column='uniq_name')
    ```
    <figure class="parts" data-src="../json/fig_input_list_of_geodataframes.json" data-label="The objects geom_2 and geom_1"><svg></svg></figure>



* * * 

## `list` of GeoJSON objects
Requires `geojson` (not a hard dependency).

!!! example


    ```python
    import json
    import topojson as tp

    with open('tests/files_geojson/geojson_1.json', 'r') as gj_1:
        geojson_1 = json.load(gj_1)
        
    with open('tests/files_geojson/geojson_2.json', 'r') as gj_2:
        geojson_2 = json.load(gj_2)
        
    topo = tp.Topology(
        data=[geojson_1, geojson_2], 
        object_name=['gjson_1', 'gjson_2']
    )
    print(topo.to_json(pretty=True))
    ```

    ```python exec="on" session="exampleinput-types" result="text"
    import json
    import topojson as tp

    with open('tests/files_geojson/geojson_1.json', 'r') as gj_1:
        geojson_1 = json.load(gj_1)
        
    with open('tests/files_geojson/geojson_2.json', 'r') as gj_2:
        geojson_2 = json.load(gj_2)
        
    topo = tp.Topology(
        data=[geojson_1, geojson_2], 
        object_name=['gjson_1', 'gjson_2']
    )
    print(topo.to_json(pretty=True))
    ```


    ```python exec="on" session="exampleinput-types"
    {
        "type": "Topology",
        "objects": {
            "gjson_1": {
                "geometries": [
                    {
                        "id": 0,
                        "type": "Feature",
                        "properties": {"shrd_name": "rect", "uniq_name": "abc"},
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [[[1.0, 1.0], [2.0, 1.0], [2.0, 2.0], [1.0, 2.0], [1.0, 1.0]]]
                        },
                        "bbox": [1.0, 1.0, 2.0, 2.0],
                        "arcs": [[[-1, 2]]]
                    },
                    {
                        "id": 1,
                        "type": "Feature",
                        "properties": {"shrd_name": "rect", "uniq_name": "def"},
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [[[0.0, 1.0], [1.0, 1.0], [1.0, 2.0], [0.0, 2.0], [0.0, 1.0]]]
                        },
                        "bbox": [0.0, 1.0, 1.0, 2.0],
                        "arcs": [[[1, 0, 3]]]
                    }
                ],
                "type": "GeometryCollection"
            },
            "gjson_2": {
                "geometries": [
                    {
                        "id": 0,
                        "type": "Feature",
                        "properties": {"shrd_name": "rect", "uniq_name": "abc"},
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [[0.0, 1.0], [0.0, 2.0], [1.0, 2.0], [2.0, 2.0], [2.0, 1.0], [1.0, 1.0], [0.0, 1.0]]
                            ]
                        },
                        "bbox": [0.0, 1.0, 2.0, 2.0],
                        "arcs": [[[1, 2, 3]]]
                    }
                ],
                "type": "GeometryCollection"
            }
        },
        "bbox": [0.0, 1.0, 2.0, 2.0],
        "transform": {
            "scale": [2.000020000200002e-05, 1.000010000100001e-05], "translate": [0.0, 1.0]
        },
        "arcs": [
            [[50000, 99999], [0, -99999]], [[0, 0], [0, 99999], [50000, 0]],
            [[50000, 99999], [49999, 0], [0, -99999], [-49999, 0]], [[50000, 0], [-50000, 0]]
        ]
    }
    ```


<script>
window.addEventListener("DOMContentLoaded", event => {
    var opt = {
        mode: "vega-lite",
        renderer: "svg",
        actions: false
    };

    var spec_mesh_altair = "../../json/example_mesh.vl.json";
    vegaEmbed("#embed_output_mesh_altair_from_geojson", spec_mesh_altair, opt).catch(console.err); 

});
</script>
<script type="text/javascript" src="https://cdn.jsdelivr.net/npm/vega@6"></script>
<script type="text/javascript" src="https://cdn.jsdelivr.net/npm/vega-lite@6"></script>
<script type="text/javascript" src="https://cdn.jsdelivr.net/npm/vega-embed@7"></script>
<script src="../js/steps.js" defer></script>
