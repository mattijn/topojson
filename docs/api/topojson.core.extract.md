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

> #### Parameters
> + ###### `data` : (_any_ geometric type)
    Different types of a geometry object, originating from shapely, geojson,
    geopandas and dictionary or list of objects that contain a __geo_interface__.

> #### Returns
dict
    object created including
    - new key: type
    - new key: linestrings
    - new key: bookkeeping_geoms
    - new key: objects

### extractor
```python
Extract.extractor(self, data)
```
"
Entry point for the class Extract.

The extract function is the first step in the topology computation.
The following sequence is adopted:
1. extract
2. join
3. cut
4. dedup
5. hashmap

Returns an object including two new properties:

* linestrings - linestrings extracted from the hash, of the form [start, end],
as shapely objects
* bookkeeping_geoms - record array storing index numbers of linestrings
used in each object.

For each line or polygon geometry in the input hash, including nested
geometries as in geometry collections, the `coordinates` array is replaced
with an equivalent `"coordinates"` array that points to one of the
linestrings as indexed in `bookkeeping_geoms`.

Points geometries are not collected within the new properties, but are placed
directly into the `"coordinates"` array within each object.

### serialize_geom_type
```python
Extract.serialize_geom_type(self, geom)
```

This function handles the different types that can occur within known
geographical data. Each type is registerd as its own function and called when
found, if none of the types match the input geom the current function is
executed.

The adoption of the dispatcher approach makes the usage of multiple if-else
statements not needed, since the dispatcher redirects the `geom` input to the
function which handles that partical geometry type.

The following geometry types are registered:
- shapely.geometry.LineString
- shapely.geometry.MultiLineString
- shapely.geometry.Polygon
- shapely.geometry.MultiPolygon
- shapely.geometry.Point
- shapely.geometry.MultiPoint
- shapely.geometry.GeometryCollection
- geojson.Feature
- geojson.FeatureCollection
- geopandas.GeoDataFrame
- geopandas.GeoSeries
- dict of objects that provide a __geo_interface__
- list of objects that provide a __geo_interface__
- object that provide a __geo_interface__
- TopoJSON string
- GeoJSON string

Any non-registered geometry wil return as an error that cannot be mapped.

### extract_line
```python
Extract.extract_line(self, geom)
```
*geom* type is LineString instance.

> #### Parameters
> + ###### `geom` : (shapely.geometry.LineString)
    LineString instance

### extract_multiline
```python
Extract.extract_multiline(self, geom)
```
*geom* type is MultiLineString instance.

> #### Parameters
> + ###### `geom` : (shapely.geometry.MultiLineString)
    MultiLineString instance

### extract_ring
```python
Extract.extract_ring(self, geom)
```
*geom* type is Polygon instance.

> #### Parameters
> + ###### `geom` : (shapely.geometry.Polygon)
    Polygon instance

### extract_multiring
```python
Extract.extract_multiring(self, geom)
```
*geom* type is MultiPolygon instance.

> #### Parameters
> + ###### `geom` : (shapely.geometry.MultiPolygon)
    MultiPolygon instance

### extract_point
```python
Extract.extract_point(self, geom)
```
*geom* type is Point instance.
coordinates are directly passed to "coordinates"

> #### Parameters
> + ###### `geom` : (shapely.geometry.Point)
    Point instance

### extract_multipoint
```python
Extract.extract_multipoint(self, geom)
```
*geom* type is MultiPoint instance.

> #### Parameters
> + ###### `geom` : (shapely.geometry.MultiPoint)
    MultiPoint instance

### extract_geometrycollection
```python
Extract.extract_geometrycollection(self, geom)
```
*geom* type is GeometryCollection instance.

> #### Parameters
> + ###### `geom` : (shapely.geometry.GeometryCollection)
    GeometryCollection instance

### extract_featurecollection
```python
Extract.extract_featurecollection(self, geom)
```
*geom* type is FeatureCollection instance.

> #### Parameters
> + ###### `geom` : (geojson.FeatureCollection)
    FeatureCollection instance

### extract_feature
```python
Extract.extract_feature(self, geom)
```
*geom* type is Feature instance.

> #### Parameters
> + ###### `geom` : (geojson.Feature)
    Feature instance

### extract_geopandas
```python
Extract.extract_geopandas(self, geom)
```
*geom* type is GeoDataFrame or GeoSeries instance.

> #### Parameters
> + ###### `geom` : (geopandas.GeoDataFrame or geopandas.GeoSeries)
    GeoDataFrame or GeoSeries instance

### extract_list
```python
Extract.extract_list(self, geom)
```
*geom* type is List instance.

> #### Parameters
> + ###### `geom` : (list)
    List instance

### extract_string
```python
Extract.extract_string(self, geom)
```
*geom* type is String instance.

> #### Parameters
> + ###### `geom` : (str)
    String instance

### extract_dictionary
```python
Extract.extract_dictionary(self, geom)
```
*geom* type is Dictionary instance.

> #### Parameters
> + ###### `geom` : (dict)
    Dictionary instance


