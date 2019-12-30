---
layout: default
title: topojson.utils
parent: API reference
nav_order: 7
---


# topojson.utils

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


