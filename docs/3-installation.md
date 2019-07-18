---
layout: default
title: Installation
nav_order: 3
---

<h1>Installation</h1>

Topojson can be installed through PyPI by the following command:

```
python3 -m pip install topojson
```

The library is installed succesfully if the following code will not give you any errors.

```python
import topojson
import shapely



```

<h2>Depdencies</h2>
Topojson has the following minimal dependencies, all of which are installed automatically with the above installation commands:

- numpy
- shapely

If speed is any issue for you than the following optional packages might give you another boost in the topology computation:

- simplification
- numba (not yet included)

To run the full test suite and for buidling the documentation a few additional dependencies are required:

- unittest
- geojson
- geopandas

<h2>Development Install</h2>

The topojson source repository is available on GitHub. Once you have cloned the repository and installed all the above dependencies, run the following command from the root of the repository to install the master version:

```python3 -m pip install -e .
To install development dependencies as well, run

\$ pip install -e .[dev]
If you do not wish to clone the source repository, you can install the development version directly from GitHub using:

\$ pip install git+https://github.com/mattijn/topojson
```
