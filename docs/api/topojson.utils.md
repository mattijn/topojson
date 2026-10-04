---
layout: default
title: topojson.utils
parent: API reference
nav_order: 7
---


# topojson.utils

## coordinates
```python
coordinates(arcs, tp_arcs, geom_type)
```

Return GeoJSON coordinates for the sequence(s) of arcs.

The arcs parameter may be a sequence of ints, each the index of a coordinate
sequence within tp_arcs within the entire topology describing a line string, a
sequence of such sequences, describing a polygon, or a sequence of polygon arcs.

## geometry
```python
geometry(obj, tp_arcs, transform=None)
```

Converts a topology object to a geometry object.

The topology object is a dict with 'type' and 'arcs' items.

## prettyjson
```python
prettyjson(obj, indent=2, maxlinelength=80)
```
Renders JSON content with indentation and line splits/concatenations to fit maxlinelength.
Only dicts, lists and basic types are supported

## indentitems
```python
indentitems(items, indent, level)
```
Recursively traverses the list of json lines, adds indentation based on the current depth

## serialize_as_geodataframe
```python
serialize_as_geodataframe(fc, crs=None)
```

Convert a topology dictionary or string into a GeoDataFrame.

> #### Parameters
> + ###### `fc` : dict, str
    a complete object representing a GeoJSON file
> + ###### `crs` : str, dict
    coordinate reference system to set on the resulting frame.
    Default is `None`.

> #### Returns
> + ###### geopandas.GeoDataFrame
topojson object parsed as GeoDataFrame
