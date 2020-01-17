---
layout: default
title: topojson.utils
parent: API reference
nav_order: 7
---


# topojson.utils

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
## singledispatch_class
```python
singledispatch_class(func)
```

The singledispatch function only applies to functions. This function creates a
wrapper around the singledispatch so it can be used for class instances.

> #### Returns
dispatch
    dispatcher for methods

## serialize_as_geodataframe
```python
serialize_as_geodataframe(topo_object, url=False)
```

Convert a topology dictionary or string into a GeoDataFrame.

> #### Parameters
> + ###### `topo_object` : (dict, str)
    a complete object representing an topojson encoded file as
    dict, str-object or str-url

> #### Returns
> + ###### `gdf` : (geopandas.GeoDataFrame)
    topojson object parsed GeoDataFrame


