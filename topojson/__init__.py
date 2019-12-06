"""
topojson - a powerful library to encode geographic data as topology in Python!🌍
===============================================================================
**topojson** is a Python package with the aim of creating TopoJSON topology.

Main Features
-------------
  - Aims to create TopoJSON for _any_ geographic vector data parsed into Python
  - Ability to select the winding order of the geometric input.
  - Options to prequantize and presimplify the geometric features preparatory
    computing the topology.
  - Options to topoquantize and toposimplify after the topology is computed
  - Choose between the package `shapely` or `simplification` to simplify the
    linestrings or arcs.
  - Direct support to analyze the arcs as svg
  - Optional support to parse the TopoJSON into a GeoDataFrame if geopandas is
    installed.
  - Optional support to parse the TopoJSON directly into a mesh or geoshape in
    Altair if the package is installed.
  - Optional support for UI controls to exploring the results of topoquantize
    and toposimplify interactively if ipywidgets is installed.
"""
__version__ = "1.0rc8"
__all__ = ["Topology "]

from .core.topology import Topology  # noqa
