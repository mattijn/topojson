# topojson

[![PyPI version](https://img.shields.io/pypi/v/topojson.svg)](https://pypi.org/project/topojson)
[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![build status](http://img.shields.io/travis/mattijn/topojson/master.svg?style=flat)](https://travis-ci.org/mattijn/topojson)

# Encode geographic data as topology in Python!

Topojson is a library that is capable of creating a topojson encoded format of merely any geographical object in Python.

With topojson it is possible to reduce the size of your geographical data. Mostly by orders of magnitude. It is able to do so through:

- Eliminating redundancy through computation of a topology
- Fixed-precision integer encoding of coordinates and
- Simplification and quantization of arcs


## Usage

The package can be used in multiple different ways, with the main purpose to create a TopoJSON topology. 

See the Python [Topojson Documentation Site](https://mattijn.github.io/topojson) for all info or [this Notebook](https://nbviewer.jupyter.org/github/mattijn/topojson/blob/master/notebooks/topojson.ipynb) with some examples, such as the following:

<p align="center">
<img src="docs/images/africa_simplify.jpeg" alt="simplifying with and without topology" width="600px">
</p>

_Top row (right) presents linestring simplification on a computed Topology and (left) on the geographical object directly. Bottom row presents visual impact on file size reduction between (left) Raw GeoJSON and (right) Topological optimized TopoJSON._ 

## Installation

Installation can be done by:

```
python3 -m pip install topojson
```

This package `topojson` has the following hard dependencies:

- `numpy`
- `shapely`

Further, optional soft dependencies are:

- `altair` (enlarge the experience by visualizing your TopoJSON output)
- `simplification` (more and quicker simplification options)
- `geojson` (parse string input with GeoJSON data)
- `geopandas` (with `fiona` version >=1.8.6!, parse your TopoJSON output directly into a GeoDataFrame)
- `ipywidgets` + (lab)extension (make your life complete with the interactive experience)

## Get in touch

For now, just use the Github issues. That can be:

- usage questions
- bug reports
- feature suggestions
- or anything related

Finally, see the Python [Topojson Documentation Site](https://mattijn.github.io/topojson) for more info.

## Changelog
Version `1.0`:
- fix duplicate coordinates in geojson export #112
- add docs [how-it-works](https://mattijn.github.io/topojson/how-it-works.html)
- replace dispatcher with if-else statments #114

Version `1.0rc11`:
- support for `fiona` Collections, using the optional `geojson` module #100
- improvements on popping of merged linestrings #105, #107
- the `to_gdf()` funtion is serialized through GeoJSON features and not through Fiona/OGR #108
- documentation updates #101 and #103

Version `1.0rc10`:
- introduced `shared_coords` as new default strategy to detect junctions #76 (thanks @martinfleis!)
- optimize reading geopandas objects #77
- add `prevent_oversimplify` as parameter #86
- fix `serialize_as_json()` to dump correct json to file #87 (thanks @olenhb!)
- store linestrings internally as numpy arrays instead of shapely geometries #90 - #97
- generate a speedup of ~20X for larger geographical objects

Version `1.0rc9`:
- include `to_geojson()` function to return the Topology as an GeoJSON object #71
- include a `__geo_interface__` for the `Topology()` class #71

Version `1.0rc8`:

- complex shared paths are registered correctly #63
- new insterted junctions are inserted in right order #64

Version `1.0rc7`:

- major refactoring to include quantization of points
- and to hash combinations of polygons/linestrings with points #61

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
- speedups and bug fixes, see #15 - #36
- introduced multiple options see #8

Version `1.0rc2`:

- apply linemerge on non-duplicate arcs
- fix computing topology without shared boundaries #1, #3
- use `geopandas` and `geojson` solely for tests, but recognize them as type #2, #4
- use [`simplification`](https://github.com/urschrei/simplification) as option to simplify linestrings
- include option to snap vertices to grid
- removed `rdtree` as dependency, use `SRTtree` from `shapely` instead

Version `1.0rc1`:

- initial release
