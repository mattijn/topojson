# TOPOJSON

[Work in Progress]. 
This repository describes the development a Python implementation of the TopoJSON format. TopoJSON is a JSON format for encoding geographic data structures into a shared topology. A TopoJSON topology represents one or more geometries that share sequences of positions called arcs. 

## Installing
The package is not yet released on pypi and can currently be installed from git.
`python -m pip install git+https://github.com/mattijn/topojson.git`

The current required dependencies for the package are

```
numpy
shapely
rdtree
geopandas
geojson
```

The package `geopandas` and `geojson` will become optional since they are solely used in the tests and recognized as types with the extractor. For `rdtree`, I'm not sure if it should become optional.

Download dependencies from https://www.lfd.uci.edu/~gohlke/pythonlibs/ for Windows and use `pip` for Linux and Mac.

Installation of the python module `rtree` depends on the C++ library `libspatialindex`. If not installed, install on a Mac by:

```bash
brew install spatialindex
```

## Usage
The package can be used as follow:

```
import topojson
topojson.topology(geometric_data)
```

The result is TopoJSON. The following geometry types are registered as geometric input data:
- geojson.Feature
- geojson.FeatureCollection
- geopandas.GeoDataFrame
- geopandas.GeoSeries
- dict of shapely geometries (LineString, MultiLineString, Polygon, MultiPolygon, Point, MultiPoint, GeometryCollection)

## Development notes
Development of this packages started by reading https://bost.ocks.org/mike/topology/ and https://github.com/topojson by Mike Bostocks.

Initially a translation of the JavaScript implementation was considered, but quickly was decided to use a combination of Shapely (since it is based on the GEOS library) and Numpy. 

Nonetheless, some subtile differences are existing between the JavaScript implementation of the TopoJSON format and this Python implementation. Some of these deviation are briefly mentioned here:
1. The extraction class stores all the different geometrical objects as shapely LineStrings in `'linestrings'` and keeps a record of these linestrings available under the key `'bookkeeping_geoms'`. In the JavaScript implementation there is a differentiation of the geometries between `'lines'`, `'rings'` and a seperate object containing all `'coordinates'`. Since the current approach adopts `shapely` for much of the heavy lifting this extraction is working against us (in the cut-process).
2. In the join class only the geometries that have shared paths are considered to have junctions. This means that the intersection of two crossing lines at a single coordinate is not considered as a junction. This also means that the two ends of a LineString are not automatically considered as being a junction. So if a segment starts or finish on another segment with that coordinate being the only coordinate in common it is not considered as a junction.
3. In the computation of a shared path, a junction can be created on a existing coordinate in one of the geometries. Where in the JavaScript implementation this only can be considered when both geometries contain the coordinate. 
4. In the process of cutting lines the rings are rotated in the JavaScript implementation to make sure they start at a junction. This reduces the number of cuts. This rotation is done before cutting. In the current Python implementation this is done differently. First the linestrings are cut using the junction coordinates and afterwards it is tried to apply a linemerge on the non-duplicate arcs of a geometry containing at least one shared arc.