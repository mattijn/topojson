# TopoJSON

[![PyPI version](https://img.shields.io/pypi/v/topojson.svg)](https://pypi.org/project/topojson)
[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)

[Work in Progress]

_TopoJSON_ encodes geographic data structures into a shared topology. This repository describes the development of a **Python** implementation of this TopoJSON format. A TopoJSON topology represents one or more geometries that share sequences of positions called arcs.

## Usage

The package can be used as follow:

```python
import topojson

data = {
    "abc": {
        "type": "Polygon",
        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
    },
    "def": {
        "type": "Polygon",
        "coordinates": [[[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]],
    },
}

topojson.topology(data)
```

    {'type': 'Topology',
     'objects': {'data': {'geometries': [{'type': 'Polygon', 'arcs': [[0, -4, 1]]},
        {'type': 'Polygon', 'arcs': [[2, 3]]}],
       'type': 'GeometryCollection'}},
     'arcs': [[[0.0, 0.0], [1.0, 0.0]],
      [[1.0, 1.0], [0.0, 1.0], [0.0, 0.0]],
      [[1.0, 0.0], [2.0, 0.0], [2.0, 1.0], [1.0, 1.0]],
      [[1.0, 1.0], [1.0, 0.0]]]}

The result is TopoJSON.

The following geometry types are registered as correct geographical input data:

- `geojson.Feature`
- `geojson.FeatureCollection`
- `geopandas.GeoDataFrame`
- `geopandas.GeoSeries`
- `dict` of geometries (`LineString`, `MultiLineString`, `Polygon`, `MultiPolygon`, `Point`, `MultiPoint`, `GeometryCollection`)

## Installation

The package is released on PyPi as version `1.0rc1`. Installation can be done by:

```
python3 -m pip install topojson
```

The required dependencies are:

- `numpy`
- `shapely`

Download dependencies from https://www.lfd.uci.edu/~gohlke/pythonlibs/ for Windows and use `pip` for Linux and Mac.

The packages `geopandas` and `geojson` are solely used in the tests and recognized as types with the extractor.

## Example and tutorial notebooks

The notebooks folder of this GitHub repository contains a Jupyter Notebook with a tutorial. The many tests within this package also can be used as example material.

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

4. In the process of cutting lines the rings are rotated in the JavaScript implementation to make sure they start at a junction. This reduces the number of cuts. This rotation is done before cutting. In the current Python implementation this is be done differently. First the linestrings are cut using the junction coordinates and afterwards there is tried to apply a linemerge on the non-duplicate arcs of a geometry containing at least one shared arc.
