---
layout: default
title: Retrieval data types
parent: Example usage
nav_order: 3
---

# Retrieval data types

Multiple functions are available to serialize the Topology object.

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


