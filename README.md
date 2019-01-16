# TopoJSON

[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)

[Work in Progress]

*TopoJSON* encodes geographic data structures into a shared topology in Python. This repository describes the development of the Python implementation of this TopoJSON format. A TopoJSON topology represents one or more geometries that share sequences of positions called arcs. 


## Installation

The package is not yet released on PyPi and can currently be installed through git:

`python -m pip install git+https://github.com/mattijn/topojson.git`

The required dependencies are:

- `numpy`
- `shapely`

The optional packages are:

- `rdtree`
- `geopandas`
- `geojson`

Inclusion of `rdtree` is highly recommened though, as it will improve speed substantially. 
The packages `geopandas` and `geojson` ware solely used in the tests and recognized as types with the extractor.

Download dependencies from https://www.lfd.uci.edu/~gohlke/pythonlibs/ for Windows and use `pip` for Linux and Mac.

Installation of the Python module `rtree` depends on the C++ library `libspatialindex`. For a installation on Mac you will have to install this using brew, as follow:

```bash
brew install spatialindex
```


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

The following geometry types are registered as correct geometric input data:
- geojson.Feature
- geojson.FeatureCollection
- geopandas.GeoDataFrame
- geopandas.GeoSeries
- dict of geometries (LineString, MultiLineString, Polygon, MultiPolygon, Point, MultiPoint, GeometryCollection)

## Example and tutorial notebooks

The notebooks folder of this Github repository contains Jupyter Notebooks with a tutorial. The many tests within this package also can be used as example material.

## Development Notes

Development of this packages started by reading https://bost.ocks.org/mike/topology/ and https://github.com/topojson by Mike Bostocks.

Initially a translation of the JavaScript implementation was considered, but quickly was decided to use a combination of Shapely (since it is based on the GEOS library) and NumPy. 

Nonetheless, some subtile differences are existing between the JavaScript implementation of the TopoJSON format and the current Python implementation. Some of these deviation are briefly mentioned here:

1. The extraction class stores all the different geometrical objects as Shapely LineStrings in `'linestrings'` and keeps a record of these linestrings available under the key `'bookkeeping_geoms'`. In the JavaScript implementation there is a differentiation of the geometries between `'lines'`, `'rings'` and a seperate object containing all `'coordinates'`. Since the current approach adopts `shapely` for much of the heavy lifting this extraction is working against us (in the cut-process).

2. In the join class only the geometries that have shared paths are considered to have junctions. This means that the intersection of two crossing lines at a single coordinate is not considered as a junction. This also means that the two ends of a LineString are not automatically considered as being a junction. So if a segment starts or finish on another segment with that coordinate being the only coordinate in common it is not considered as a junction.

3. In the computation of a shared path, a junction can be created on an existing coordinate in one of the geometries. Where in the JavaScript implementation this only can be considered when both geometries contain the coordinate. 

4. In the process of cutting lines the rings are rotated in the JavaScript implementation to make sure they start at a junction. This reduces the number of cuts. This rotation is done before cutting. In the current Python implementation this is (will be) done differently. First the linestrings are cut using the junction coordinates and afterwards there is tried to apply a linemerge on the non-duplicate arcs of a geometry containing at least one shared arc.