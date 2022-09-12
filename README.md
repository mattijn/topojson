# topojson

[![PyPI version](https://img.shields.io/pypi/v/topojson.svg)](https://pypi.org/project/topojson)
[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![github actions](https://github.com/mattijn/topojson/workflows/test/badge.svg)](https://github.com/mattijn/topojson/actions?query=workflow%3Atest)
[![Conda version](https://anaconda.org/conda-forge/topojson/badges/installer/conda.svg)](https://anaconda.org/conda-forge/topojson)
![shapely 2.0 compliant](https://img.shields.io/badge/shapely%201%20%26%202-compliant-brightgreen)


# Encode spatial data as topology in Python!

Topojson is a library that is capable of creating a topojson encoded format of merely any spatial object in Python.

With topojson it is possible to reduce the size of your spatial data. Mostly by orders of magnitude. It is able to do so through:

- Eliminating redundancy through computation of a topology
- Fixed-precision integer encoding of coordinates and
- Simplification and quantization of arcs

See [Topojson Documentation Site](https://mattijn.github.io/topojson) for all info how to use this package.

## Usage

The package can be used in multiple different ways, with the main purpose to create a TopoJSON topology. 

See the Python [Topojson Documentation Site](https://mattijn.github.io/topojson) for all info or [this Notebook](https://nbviewer.jupyter.org/github/mattijn/topojson/blob/master/notebooks/topojson.ipynb) with some examples, such as the following:

<p align="center">
<a href="https://nbviewer.jupyter.org/github/mattijn/topojson/blob/master/notebooks/topojson.ipynb" target="_blank" rel="noopener noreferrer"><img src="docs/images/africa_simplify.png" alt="click to open notebook" width="600px"></a>
</p>

_Click on the image to go the Notebook Viewer with code-snippets how these images are created or visit the [Topojson Documentation Site](https://mattijn.github.io/topojson)._ 

## Installation

Installation can be done through PyPI by the following command:

```
python -m pip install topojson
```

And through conda using the following command:

```
conda install topojson -c conda-forge
```

This package `topojson` has the following hard dependencies:

- `numpy`
- `shapely`

Further, optional soft dependencies are:

- `altair` - enlarge the experience by visualizing your TopoJSON output
- `simplification` - more and quicker simplification options
- `geojson` - parse string input with GeoJSON data
- `geopandas` - parse your TopoJSON output directly into a GeoDataFrame
- `ipywidgets` + (lab)extension - make your life complete with the interactive experience

## Get in touch

For now, just use the Github issues. That can be:

- usage questions
- bug reports
- feature suggestions
- or anything related

Finally, see the Python [Topojson Documentation Site](https://mattijn.github.io/topojson) for all info how to use this package.
