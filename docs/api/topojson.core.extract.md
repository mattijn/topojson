---
layout: default
title: topojson.core.extract
parent: API reference
nav_order: 2
---


# topojson.core.extract

## Extract
```python
Extract(self, data, options={})
```

This class targets the following objectives:
1. Detection of geometrical type of the object
2. Extraction of linestrings from the object

The extract function is the first step in the topology computation.
The following sequence is adopted:
1. extract
2. join
3. cut
4. dedup
5. hashmap

For each line or polygon geometry in the input hash, including nested
geometries as in geometry collections, the `coordinates` array is replaced
with an equivalent `"coordinates"` array that points to one of the
linestrings as indexed in `bookkeeping_geoms` and stored in `linestrings`.

For Points geometries count the same, but are stored in `coordinates` and
referenced in `bookkeeping_coords`.

> #### Parameters
> + ###### `data` : _any_ geometric type
    Different types of a geometry object, originating from shapely, geojson,
    geopandas and dictionary or list of objects that contain a `__geo_interface__`.

> #### Returns
> + ###### dict
object created including the keys `type`, `linestrings`, `coordinates` `bookkeeping_geoms`, `bookkeeping_coords`, `objects`

### to_dict
```python
Extract.to_dict(self)
```

Convert the Extract object to a dictionary.

### to_svg
```python
Extract.to_svg(self, separate=False)
```

Display the linestrings as SVG.

> #### Parameters
> + ###### `separate` : boolean
    If `True`, each of the linestrings will be displayed separately.
    Default is `False`


