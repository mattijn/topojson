# topojson

[![PyPI version](https://img.shields.io/pypi/v/topojson.svg)](https://pypi.org/project/topojson)
[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![build status](http://img.shields.io/travis/mattijn/topojson/master.svg?style=flat)](https://travis-ci.org/mattijn/topojson)


_[Its not yet version 1.0, but that's merely because of missing documentation. With other words: you should be safe to use it!]_


#

_Topojson_ encodes geographic data structures into a shared topology. This repository describes the development of a **Python** implementation of the TopoJSON format.

## Usage

The package can be used in multiple different ways, with the main purpose to create a TopoJSON topology:

```python
import topojson

data = [
    {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
    {"type": "Polygon", "coordinates": [[[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]]}
]

tj = topojson.Topology(data, prequantize=False, topology=True)
tj.to_json()
```

What results in the following TopoJSON object:

```python
'{"type": "Topology", "objects": {"data": {"geometries": [{"type": "Polygon", "arcs": [[-2, 0]]}, {"type": "Polygon", "arcs": [[1, 2]]}], "type": "GeometryCollection"}}, "bbox": [0.0, 0.0, 2.0, 1.0], "arcs": [[[1.0, 0.0], [0.0, 0.0], [0.0, 1.0], [1.0, 1.0]], [[1.0, 0.0], [1.0, 1.0]], [[1.0, 1.0], [2.0, 1.0], [2.0, 0.0], [1.0, 0.0]]]}'
```

More or less all Python objects containing geographical data are supported through the `__geo_interface__` attribute. This includes at least the Python packages `geojson`, `shapely`, `geopandas`, `pyshp`.

Moreover a `dict` of objects that provide a valid `__geo_interface__`, a `list` of objects that provide a valid `__geo_interface__` and `str` objects with TopoJSON or GeoJSON geographic structures are supported too.

In the example above the output is parsed to a JSON string (`.to_json()`), but this is not the only thing we can do. Multiple functions are available to serialize the Topology object.

| Functions                       | Required Packages                                                       |
| ------------------------------- | ----------------------------------------------------------------------- |
| topojson.Topology().to_json()   | Shapely, NumPy                                                          |
| topojson.Topology().to_dict()   | Shapely, NumPy                                                          |
| topojson.Topology().to_svg()    | Shapely, NumPy                                                          |
| topojson.Topology().to_alt()    | Shapely, NumPy, Altair\*                                                |
| topojson.Topology().to_gdf()    | Shapely, NumPy, GeoPandas\*                                             |
| topojson.Topology().to_widget() | Shapely, NumPy, Altair*, Simplification*, ipywidgets\* (+ labextension) |

\* optional dependencies

The TopoJSON format is merely designed to create smaller files than its GeoJSON counterpart. It is capable of doing so through a few options of which the following are currently available: compute topology, quantize the input and/or output, simplify the input and/or output.

The following parameters can be used to control these options for generating the `Topology()` object. Detailed information can be found in the docstring of the [`topojson.Topology()`](https://github.com/mattijn/topojson/blob/master/topojson/core/topology.py#L18:L79) class.

- topology
- prequantize
- topoquantize
- presimplify
- toposimplify
- simplify_with
- simplify_algorithm
- winding_order

Where the `toposimplify` and `topoquantize` are supported by chaining as well. Meaning you could first compute the Topology (which can be cost-intensive) and afterwards apply the simplify and quantize settings on the computed Topology and visualize till pleased.

```python
tj = topojson.Topology(data, prequantize=False, topology=True)
tj.toposimplify(1).topoquantize(1e6).to_svg()
```

Or use the ipywidget approach described more below for an interactive approach.

## Installation

Installation can be done by:

```
python3 -m pip install topojson
```

Topojson depends on the following packages:

- numpy
- shapely

Windows users: download the dependencies from https://www.lfd.uci.edu/~gohlke/pythonlibs/.
OS X or Linux users: use `pip` as usual

Further, optional dependencies are:

- altair (enlarge the experience by visualizing your TopoJSON output)
- simplification (more and quicker simplification options)
- geojson (parse string input with GeoJSON data)
- geopandas (with `fiona` version >=1.8.6!, parse your TopoJSON output directly into a GeoDataFrame - converting it to GeoJSON)
- ipywidgets + (lab)extension (make your life complete with the interactive experience)

## Get in touch

For now, just use the Github issues. That can be:

- usage questions
- bug reports
- feature suggestions
- or anything related

## Examples and tutorial notebooks

The followig examples present different input types parsed to different output types. The input types are not dependent on the used output type and vice versa, they are just possible examples.

### Input Type: `list`

The list should contain items that supports the `__geo_interface__`

```python
import topojson

list_geoms = [
    {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
    {"type": "Polygon", "coordinates": [[[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]]}
]
```

#

#### apply Topology and present the output as dict

```python
tj = topojson.Topology(data, prequantize=False, topology=True)
tj.to_dict()
```

```python
{'type': 'Topology',
  [[1.0, 0.0], [1.0, 1.0]],
  [[1.0, 1.0], [2.0, 1.0], [2.0, 0.0], [1.0, 0.0]]],
 'objects': {'data': {'geometries': [{'type': 'Polygon', 'arcs': [[-2, 0]]},
    {'type': 'Polygon', 'arcs': [[1, 2]]}],
   'type': 'GeometryCollection'}},
 'options': TopoOptions(
   {'prequantize': False,
  'presimplify': False,
  'simplify_with': 'shapely',
  'topology': True,
  'topoquantize': False,
  'toposimplify': 0.0001,
  'winding_order': 'CW_CCW'}
 ),
 'bbox': (0.0, 0.0, 2.0, 1.0),
 'arcs': [[[1.0, 0.0], [0.0, 0.0], [0.0, 1.0], [1.0, 1.0]],
  [[1.0, 0.0], [1.0, 1.0]],
  [[1.0, 1.0], [2.0, 1.0], [2.0, 0.0], [1.0, 0.0]]]}
```

#

### Input Type: `dict`

The dictionary should be structured like {`key1`: `obj1`, `key2`: `obj2`}.

```python
import topojson

dictionary = {
    0: {
        "type": "Polygon",
        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
    },
    1: {
        "type": "Polygon",
        "coordinates": [[[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]],
    }
}
```

#

#### apply Topology and present the output as scalable vector graphic

```python
tj = topojson.Topology(dictionary, prequantize=False, topology=True)
tj.to_svg()
```

<img src="images/svg_repr.png" alt="svg">

#

### Input Type: `GeoDataFrame` from package `geopandas` (if installed)

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

<img src="images/geodataframe_plot.png" alt="geodataframe">

#

#### apply Topology and present output as `altair` chart (if installed)

```python
tj = topojson.Topology(gdf, prequantize=False, topology=True)
tj.to_alt(color='properties.name:N')
```

<img src="images/altair_chart.png" alt="altair">

#

### Input Type: `FeatureCollection` from package `geojson` (if installed)

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

#### apply Topology and present output as `geodataframe` (if `geopandas` is installed)

```python
tj = topojson.Topology(feature_collection, prequantize=False, topology=True)
tj.to_gdf()
```

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>geometry</th>
      <th>id</th>
      <th>name</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>POLYGON ((1 1, 1 0, 0 0, 0 1, 1 1))</td>
      <td>None</td>
      <td>abc</td>
    </tr>
    <tr>
      <th>1</th>
      <td>POLYGON ((1 0, 1 1, 2 1, 2 0, 1 0))</td>
      <td>None</td>
      <td>def</td>
    </tr>
  </tbody>
</table>
</div>

#

Currently parsing TopoJSON as string input requires `geopandas` (`fiona` version >=1.8.6) and parsing GeoJSON as string requires the package `geojson`.

The package `simplification` can be used if you want to adopt the Visvalingam-Whyatt algorithm for simplifying or for having a speedup on the Douglas-Peucker algorithm (compared to the `shapely`-integrated version).

The `.to_widget()` function depends on `ipywidgets` and can be a bit tricky to get it installed and properly working. But if you do, something like the following will show up:

<img src="images/ipywidgets.gif" alt="ipywidgets">

To install, use the ipywidgets website for installation.  
Initially I ran very often in errors like the following after I thought I'd install everything correctly:

```
[IPKernelApp] WARNING | No such comm: xxxyyyzzz123etc.
```

To solve this error I found out that I'd first had to pip uninstall JupyterLab, then install the lab extension of ipywidgets and then install JupyterLab again. Then when starting JupyterLab for the first time it asks to rebuild to include the ipywidgets lab extension. Click Yes or OK and wait till JupyterLab refresh, afterwards these errors did not appear for me anymore (both Windows and macOS). If you got all installed I suggest starting from `In [5]` in the following [notebook](https://nbviewer.jupyter.org/github/mattijn/topojson/blob/master/notebooks/ipywidgets_interaction.ipynb) to test if all works.

Futher, the many [tests][l1] as part of this package also can be used as example material.

[l1]: https://github.com/mattijn/topojson/tree/master/tests

## Changelog

Version `1.0rc6`:

- fix linemerging of non-duplicate arcs #50
- include `__geo_interface__` attributed as input #53
- include travis testing on GitHub (thanks @Casyfill!)
- migrate from unittests to pytest (thanks @Casyfill!)

Version `1.0rc5`:

- change `TopoOptions` in `to_dict` to be serializable #46
- changed all `int` to `np.int64`, since it is platform specific #49, #45

Version `1.0rc4`:

- no `linestring` key in topojson
- serialize `str` of TopoJSON or GeoJSON data
- add `vw` as algoritm type and update widget

Version `1.0rc3`:

- changed class object to inherit sequence
- removed the `topojson.topology` function
- introducted the `topojson.Topology` class
- speedups and bug fixes, see PR#15-#36
- introduced multiple options see #8

Version `1.0rc2`:

- apply linemerge on non-duplicate arcs
- fix computing topology without shared boundaries ([#1][i1], [#3][i3])
- use `geopandas` and `geojson` solely for tests, but recognize them as type ([#2][i2], [#4][i4])
- use [`simplification`](https://github.com/urschrei/simplification) as option to simplify linestrings
- include option to snap vertices to grid
- removed `rdtree` as dependency, use `SRTtree` from `shapely` instead

Version `1.0rc1`:

- initial release

[i1]: https://github.com/mattijn/topojson/issues/1
[i2]: https://github.com/mattijn/topojson/issues/2
[i3]: https://github.com/mattijn/topojson/issues/3
[i4]: https://github.com/mattijn/topojson/issues/4

## Tests

There are many tests writen to make sure all type of corner-cases are covered. To make sure all tests will pass, you must have version >=0.5.0 of `geopandas` in combination with `fiona` version >=1.8.6.
Shapely version 1.7a2 is recommended (because of https://github.com/Toblerity/Shapely/pull/733), but all tests pass from version >=1.6.3.

## Development Notes

Development of this packages started by reading:

- https://bost.ocks.org/mike/topology/ and https://github.com/topojson by Mike Bostocks and
- https://github.com/calvinmetcalf/topojson.py by Calvin Metcalf.

The reason for development of this package was the willingness:

- To adopt `shapely` (GEOS) and `numpy` for the core-functionalities in deriving the Topology.
- To provide integration with other geographical packages within the Python ecosystem (eg. `geopandas` and `altair`).
- Also the possibility of including the many tests available in the JavaScript implementation was hoped-for.

To create a certain synergy between the JavaScript and Python implementation the same naming conventions was adopted for the processing steps (`extract`, `join`, `cut`, `dedup`, `hashmap`). Even though the actual code differs significant.

Some subtile differences are existing between the JavaScript implementation and the current Python implementation for deriving the Topology. Some of these deviations are briefly mentioned here:

1. The extraction class stores all the different geometrical objects as Shapely LineStrings in `linestrings` and keeps a record of these linestrings available under the key `bookkeeping_geoms`. In the JavaScript implementation there is a differentiation of the geometries between `lines`, `rings` and a seperate object containing all `coordinates`. Since the current approach adopts `shapely` for much of the heavy lifting this extraction is working against us (in the cut-process).

2. In the join class only the geometries that have shared paths are considered to have junctions. This means that the intersection of two crossing lines at a single coordinate is not considered as a junction. This also means that the two ends of a LineString are not automatically considered as being a junction. So if a segment starts or finish on another segment, with that coordinate being the only coordinate in common, it is not considered as a junction.

3. In the computation of a shared path, a junction can be created on an existing coordinate in one of the geometries. Where in the JavaScript implementation this only can be considered when both geometries contain the coordinate.

4. In the process of cutting lines; the rings are rotated in the JavaScript implementation to make sure they start at a junction. This reduces the number of cuts. This rotation is done before cutting. In the current Python implementation this is done differently. First the linestrings are cut using the junction coordinates and afterwards there is tried to apply a linemerge on the non-duplicate arcs of a geometry containing at least one shared arc.
