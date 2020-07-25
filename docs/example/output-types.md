---
layout: default
title: Retrieval data types
parent: Example usage
nav_order: 3
---

# Retrieval data types
{: .no_toc}

Multiple functions are available to serialize the Topology object. All of them are shown in this table below including the required hard and soft dependencies and further described below.

| Functions                       | Required Packages                                                       |
| ------------------------------- | ----------------------------------------------------------------------- |
| topojson.Topology().to_json()   | Shapely, NumPy                                                          |
| topojson.Topology().to_dict()   | Shapely, NumPy                                                          |
| topojson.Topology().to_svg()    | Shapely, NumPy                                                          |
| topojson.Topology().to_geojson()    | Shapely, NumPy                                                          |
| topojson.Topology().to_alt()    | Shapely, NumPy, _Altair\*_                                                |
| topojson.Topology().to_gdf()    | Shapely, NumPy, _GeoPandas\*_                                             |
| topojson.Topology().to_widget() | Shapely, NumPy, _Altair*_, _Simplification\*_, _ipywidgets* (+ labextension)_ |

_\* optional dependencies_

**Note:** Only the serialization to different output types is described here. See ['settings and tuning']({{site.baseurl}}/example/settings-tuning.html) for detailed examples of all options regarding creating the Topology object. 

1. TOC
{:toc}


* * *

## .to_json()

Serialize the Topology object into JSON. This is what is called TopoJSON.

<div class="code-example mx-1 bg-example">
<div class="example-label" markdown="1">
Example 🔧
{: .label .label-blue-000 }
</div>
<div class="example-text" markdown="1">

Given the following two polygons:
```python
import topojson as tp
from shapely import geometry

data = [
    {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
    {"type": "Polygon", "coordinates": [[[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]]}
]
geometry.GeometryCollection([geometry.shape(g) for g in data])
```
<img src="../images/two_polygon.svg">

The Topology can be computed

```python
topo = tp.Topology(data)
```

And serialized and saved into a JSON (TopoJSON) file:
```python
topo.to_json('my_file.topo.json')
```

To inspect the JSON object first, leave out the filepath (`fp`) argument.
```
print(topo.to_json())
```
<pre class="code_no_highlight">
{"type":"Topology","objects":{"data":{"geometries":[{"type":"Polygon","arcs":[[-2,0]]},{"type":"Polygon","arcs":[[1,2]]}],"type":"GeometryCollection"}},"bbox":[0.0,0.0,2.0,1.0],"transform":{"scale":[2.000002000002e-06,1.000001000001e-06],"translate":[0.0,0.0]},"arcs":[[[500000,0],[-500000,0],[0,999999],[500000,0]],[[500000,0],[0,999999]],[[500000,999999],[499999,0],[0,-999999],[-499999,0]]]}
</pre>
Default is a compact form of JSON. If you like a more readable format, set `pretty=True`.
```python
print(topo.to_json(pretty=True))
```
<pre class="code_no_highlight">
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
    "transform": {
        "scale": [2.000002000002e-06, 1.000001000001e-06], "translate": [0.0, 0.0]
    },
    "arcs": [
        [[500000, 0], [-500000, 0], [0, 999999], [500000, 0]], [[500000, 0], [0, 999999]],
        [[500000, 999999], [499999, 0], [0, -999999], [-499999, 0]]
    ]
}
</pre>
The `pretty` option depends on the setting `indent` and `maxlinelength`, these default to `4` and `88` respectively.
</div>
</div>

* * * 

## .to_dict()

Serialize the Topology object into a Python Dictionary.

<div class="code-example mx-1 bg-example">
<div class="example-label" markdown="1">
Example 🔧
{: .label .label-blue-000 }
</div>
<div class="example-text" markdown="1">

We use the data as is prepared in the [.to_json()](output-types.html#to_json) section.

```python
topo.to_dict()
```
<pre class="code_no_highlight">
{'type': 'Topology',
 'objects': {'data': {'geometries': [{'type': 'Polygon', 'arcs': [[-2, 0]]},
    {'type': 'Polygon', 'arcs': [[1, 2]]}],
   'type': 'GeometryCollection'}},
 'bbox': (0.0, 0.0, 2.0, 1.0),
 'transform': {'scale': [2.000002000002e-06, 1.000001000001e-06],
  'translate': [0.0, 0.0]},
 'arcs': [[[500000, 0], [-500000, 0], [0, 999999], [500000, 0]],
  [[500000, 0], [0, 999999]],
  [[500000, 999999], [499999, 0], [0, -999999], [-499999, 0]]]}
</pre>
In the computation of the Topology object a few options are adopted. To include these options in the Python Dictionary use `options=True`.

```python
topo.to_dict(options=True)
```
<pre class="code_no_highlight">
{'type': 'Topology',
 'objects': {'data': {'geometries': [{'type': 'Polygon', 'arcs': [[-2, 0]]},
    {'type': 'Polygon', 'arcs': [[1, 2]]}],
   'type': 'GeometryCollection'}},
 'bbox': (0.0, 0.0, 2.0, 1.0),
 'transform': {'scale': [2.000002000002e-06, 1.000001000001e-06],
  'translate': [0.0, 0.0]},
 'arcs': [[[500000, 0], [-500000, 0], [0, 999999], [500000, 0]],
  [[500000, 0], [0, 999999]],
  [[500000, 999999], [499999, 0], [0, -999999], [-499999, 0]]],
 'options': {'topology': True,
  'prequantize': True,
  'topoquantize': False,
  'presimplify': False,
  'toposimplify': False,
  'shared_coords': True,
  'prevent_oversimplify': True,
  'simplify_with': 'shapely',
  'simplify_algorithm': 'dp',
  'winding_order': 'CW_CCW'}}
</pre>  
</div>
</div>

* * * 

## .to_svg()

Serialize the Topology object into a visual Support Vector Graphic (SVG) mesh.

<div class="code-example mx-1 bg-example">
<div class="example-label" markdown="1">
Example 🔧
{: .label .label-blue-000 }
</div>
<div class="example-text" markdown="1">

We use the data as is prepared in the [.to_json()](output-types.html#to_json) section.
```python
topo.to_svg()
```
<img src="../images/two_polygon.svg">

The output is a mesh and information of polygons are not included. To draw each captured linestring separate use `separate=True`.

```python
topo.to_svg(separate=True)
```
<pre class="code_no_highlight">
0 LINESTRING (1.000001000001 0, 0 0, 0 0.9999999999999999, 1.000001000001 0.9999999999999999)
<img src="../images/to_svg_0.svg">
1 LINESTRING (1.000001000001 0, 1.000001000001 0.9999999999999999)
<img src="../images/to_svg_1.svg">
2 LINESTRING (1.000001000001 0.9999999999999999, 2 0.9999999999999999, 2 0, 1.000001000001 0)
<img src="../images/to_svg_2.svg">
</pre>
</div>
</div>

* * * 

## .to_geojson()

Serialize the Topology object into GeoJSON. This destroys the Topology. 

<div class="code-example mx-1 bg-example">
<div class="example-label" markdown="1">
Example 🔧
{: .label .label-blue-000 }
</div>
<div class="example-text" markdown="1">

We use the data as is prepared in the [.to_json()](output-types.html#to_json) section.

Serialze and save into a JSON (GeoJSON) file
```python
topo.to_geojson('my_file.geo.json')
```

To inspect the JSON object first, leave out the filepath (`fp`) argument.
```
print(topo.to_geojson())
```
<pre class="code_no_highlight">
{"type":"FeatureCollection","features":[{"id":0,"type":"Feature","geometry":{"type":"Polygon","coordinates":[[[1.000001000001,0.9999999999999999],[0.0,0.9999999999999999],[0.0,0.0],[1.000001000001,0.0],[1.000001000001,0.9999999999999999]]]}},{"id":1,"type":"Feature","geometry":{"type":"Polygon","coordinates":[[[1.000001000001,0.0],[1.9999999999999998,0.0],[1.9999999999999998,0.9999999999999999],[1.000001000001,0.9999999999999999],[1.000001000001,0.0]]]}}]}
</pre>
Default is a compact form of JSON. If you like a more readable format, set `pretty=True`.
```python
print(topo.to_json(pretty=True))
```
<pre class="code_no_highlight">
{
    "type": "FeatureCollection",
    "features": [
        {
            "id": 0,
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [1.000001000001, 0.9999999999999999], [0.0, 0.9999999999999999], [0.0, 0.0],
                        [1.000001000001, 0.0], [1.000001000001, 0.9999999999999999]
                    ]
                ]
            }
        },
        {
            "id": 1,
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [1.000001000001, 0.0], [1.9999999999999998, 0.0],
                        [1.9999999999999998, 0.9999999999999999], [1.000001000001, 0.9999999999999999],
                        [1.000001000001, 0.0]
                    ]
                ]
            }
        }
    ]
}
</pre>
The `pretty` option depends on the setting `indent` and `maxlinelength`, these default to `4` and `88` respectively.

More options in generating the GeoJSON from the computed Topololgy are `validate` (`True` or `False`) and `winding_order`. Where the TopoJSON standard defines a winding order of clock-wise orientation for outer polygons and counter-clockwise orientation for innner polygons is the winding order in the GeoJSON standard the opposite (`CCW_CW`).
</pre>
</div>
</div>

* * * 

## .to_alt()

Serialize the Topology object into an Altair visualization.

<div class="code-example mx-1 bg-example">
<div class="example-label" markdown="1">
Example 🔧
{: .label .label-blue-000 }
</div>
<div class="example-text" markdown="1">

Here we load continental Afria as data file and apply the toposimplify on the arcs.
```python
import topojson as tp

import topojson as tp
data = tp.utils.example_data_africa()

topo = tp.Topology(data, toposimplify=4)
```
<img src="../images/two_polygon.svg">

<pre class="code_no_highlight">
Text output
</pre>
</div>
</div>

* * * 

## .to_gdf()

Serialize the Topology object into a GeoPandas GeoDataFrame.

<div class="code-example mx-1 bg-example">
<div class="example-label" markdown="1">
Example 🔧
{: .label .label-blue-000 }
</div>
<div class="example-text" markdown="1">

Given the following two polygons:
```python
import topojson as tp

data = [
    {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
    {"type": "Polygon", "coordinates": [[[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]]}
]
geometry.GeometryCollection([geometry.shape(g) for g in data])
```
<img src="../images/two_polygon.svg">

<pre class="code_no_highlight">
Text output
</pre>
</div>
</div>

* * * 

## .to_widget()

Serialize the Topology object into an interactive IPython Widget.

<div class="code-example mx-1 bg-example">
<div class="example-label" markdown="1">
Example 🔧
{: .label .label-blue-000 }
</div>
<div class="example-text" markdown="1">

Given the following two polygons:
```python
import topojson as tp

data = [
    {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
    {"type": "Polygon", "coordinates": [[[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]]}
]
geometry.GeometryCollection([geometry.shape(g) for g in data])
```
<img src="../images/two_polygon.svg">

<pre class="code_no_highlight">
Text output
</pre>
</div>
</div>

