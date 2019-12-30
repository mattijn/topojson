---
layout: default
title: topojson.ops
parent: API reference
nav_order: 8
---


# topojson.ops

## asvoid
```python
asvoid(arr)
```

Utility function to create a 1-dimensional numpy void object (bytes)
of a 2-dimensional array. This is useful for the function numpy.in1d(),
since it only accepts 1-dimensional objects.

> #### Parameters
> + ###### `arr` : (numpy.array)
    2-dimensional numpy array

> #### Returns
numpy.void
    1-dimensional numpy void object

## insert_coords_in_line
```python
insert_coords_in_line(line, tree_splitter)
```

Insert coordinates that are on the line, but where no vertices exists

> #### Parameters
> + ###### `line` : (numpy.array)
    numpy array with coordinates representing a line segment
tree_splitter: STRtree
    a STRtree splitter object

> #### Returns
> + ###### `new_ls_xy` : (numpy.array)
    numpy array with inserted coordinates, if any, representing a line segment
pts_xy_on_> + ###### `line` : (numpy.array)
    numpy array with with coordinates that are on the lin

## fast_split
```python
fast_split(line, splitter)
```

Split a LineString (numpy.array) with a Point or MultiPoint.
This function is a replacement for the shapely.ops.split function, but faster.

> #### Parameters
> + ###### `line` : (numpy.array)
    numpy array with coordinates that you like to be split
> + ###### `splitter` : (numpy.array)
    numpy array with coordiates on wich the line should be tried splitting

> #### Returns
list of numpy.array
    If more than 1 item, the line was split. Each item in the list is a
    array of coordinates.

## signed_area
```python
signed_area(ring)
```

compute the signed area of a ring (polygon)

note: implementation is numpy variant of shapely's version:
https://github.com/Toblerity/Shapely/blob/master/shapely/algorithms/cga.py

> #### Parameters
> + ###### `ring` : (shapely.geometry.LinearRing)
    an exterior or inner ring of a shapely.geometry.Polygon

> #### Returns
float
    the signed area

## is_ccw
```python
is_ccw(ring)
```
provide information if a given ring is clockwise or counterclockwise.

> #### Parameters
> + ###### `ring` : (shapely.geometry.LinearRing)
    an exterior or inner ring of a shapely.geometry.Polygon

> #### Returns
boolean
    True if ring is counterclockwise and False if ring is clockwise

## properties_foreign
```python
properties_foreign(objects)
```

Try to parse the object properties as foreign members. Reserved keys are:
["type", "bbox", "coordinates", "geometries", "geometry", "properties", "features"]

If these keys are detected they will not be set as a foreign member and will remain
nested within properties.

Only if the

> #### Parameters
> + ###### `objects` : ([type])
    [description]

## compare_bounds
```python
compare_bounds(b0, b1)
```

Function that compares two bounds with each other. Returns the max bound.

> #### Parameters
> + ###### `b0` : (tuple)
    tuple of xmin, ymin, xmax, ymax
> + ###### `b1` : (tuple)
    tuple of xmin, ymin, xmax, ymax

> #### Returns
tuple
    min of mins and max of maxs

## np_array_from_lists
```python
np_array_from_lists(nested_lists)
```

Function to create numpy array from nested lists. The shape of the numpy array
are the number of nested lists (rows) x the length of the longest nested list
(columns). Rows that contain less values are filled with np.nan values.

> #### Parameters
> + ###### `nested_lists` : (list of lists)
    list containing nested lists of different sizes.

> #### Returns
numpy.ndarray
    array created from nested lists, np.nan is used to fill the array

## lists_from_np_array
```python
lists_from_np_array(np_array)
```

Function to convert numpy array to list, where elements set as np.nan
are filtered

## get_matches
```python
get_matches(geoms, tree_idx)
```

Function to return the indici of the rtree that intersects with the input geometries

> #### Parameters
> + ###### `geoms` : (list)
    list of geometries to compare against the STRtree
tree_idx: STRtree
    a STRtree indexing object

> #### Returns
list
    list of tuples, where the key of each tuple is the linestring index and the
    value of each key is a list of junctions intersecting bounds of linestring.

## select_unique
```python
select_unique(data)
```

Function to return unique pairs within a numpy array.
Example: input as [[1,2], [2,1]] will return as [[1,2]]

> #### Parameters
> + ###### `data` : (numpy.array)
    2 dimensional array, where each row is a couple

> #### Returns
numpy.array
    2 dimensional array, where each row is unique.

## select_unique_combs
```python
select_unique_combs(linestrings)
```

Given a set of inpit linestrings will create unique couple combinations.
Each combination created contains a couple of two linestrings where the enveloppe
overlaps each other.
Linestrings with non-overlapping enveloppes are not returned as combination.

> #### Parameters
> + ###### `linestrings` : (list of LineString)
    list where each item is a shapely LineString

> #### Returns
numpy.array
    2 dimensional array, with on each row the index combination
    of a unique couple LineString with overlapping enveloppe

## quantize
```python
quantize(linestrings, bbox, quant_factor=1000000.0)
```

Function that applies quantization. Quantization removes information by reducing
the precision of each coordinate, effectively snapping each point to a regular grid.

> #### Parameters
linestrings: list of shapely.geometry.LineStrings
    LineStrings that will be quantized
> + ###### `quant_factor` : (int)
    Quantization factor. Normally this varies between 1e4, 1e5, 1e6. Where a
    higher number means a bigger grid where the coordinates can snap to.

> #### Returns
> + ###### `transform` : (dict)
    scale (kx, ky) and translation (x0, y0) values
> + ###### `bbox` : (array)
    bbox of all linestrings

## simplify
```python
simplify(linestrings, epsilon, algorithm='dp', package='simplification', input_as='linestring')
```

Function that simplifies linestrings. The goal of line simplification is to reduce
the number of points by deleting some trivial points, but without destroying the
essential shape of the lines in the process.

One can choose between the Douglas-Peucker ["dp"] algorithm (which simplifies
a line based upon vertical interval) and Visvalingam–Whyatt ["vw"] (which
progressively removes points with the least-perceptible change).

https://pdfs.semanticscholar.org/9877/cdf50a15367bcb86649b67df8724425c5451.pdf

> #### Parameters
linestrings: list of shapely.geometry.LineStrings
    LineStrings that will be simplified
> + ###### `epsilon` : (int)
    Simplification factor. Normally this varies 1.0, 0.1 or 0.001 for "rdp" and
    30-100 for "vw".
> + ###### `algorithm` : (str, optional)
    Choose between `dp` for Douglas-Peucker and `vw` for Visvalingam–Whyatt.
    Defaults to `dp`, as its evaluation maintains to be good (Song & Miao, 2016).
> + ###### `package` : (str, optional)
    Choose between `simplification` or `shapely`. Both pachakges contains
    simplification algorithms (`shapely` only `dp`, and `simplification` both `dp`
    and `vw`).
> + ###### `input_as` : (str, optional)
    Choose between `linestring` or `array`. This function is being called from
    different locations with different input types. Choose `linestring` if the input
    type are shapely.geometry.LineString or `array` if the input are numpy.array
    coordinates

> #### Returns
simp_linestrings: list of shapely.geometry.LineStrings
    LineStrings that are simplified

Docs
* https://observablehq.com/@lemonnish/minify-topojson-in-the-browser
* https://github.com/topojson/topojson-simplify#planarTriangleArea
* https://www.jasondavies.com/simplify/
* https://bost.ocks.org/mike/simplify/

## winding_order
```python
winding_order(geom, order='CW_CCW')
```

Function that force a certain winding order on the resulting output geometries. One
can choose between "CCW_CW" and "CW_CCW".

"CW_CCW" implies clockwise for exterior polygons and counterclockwise for interior
polygons (aka the geographical right-hand-rule where the right hand is in the area
of interest as you walk the line).

"CCW_CW" implies counterclockwise for exterior polygons and clockwise for interior
polygons (aka the mathematical right-hand-rule where the right hand curls around
the polygon's exterior with your thumb pointing "up" (toward space), signing a
positive area for the polygon in the signed area sense).

TopoJSON, and so this package, defaults to "CW_CCW"*, but depending on the
application you might decide differently.

* https://bl.ocks.org/mbostock/a7bdfeb041e850799a8d3dce4d8c50c8

Only applies to Polygons and MultiPolygons.

> #### Parameters
> + ###### `geom` : (geometry or shapely.geometry.GeometryCollection)
    Geometry objects where the winding order will be forced upon.
> + ###### `order` : (str, optional)
    Choose "CW_CCW" for clockwise for exterior- and counterclockwise for
    interior polygons or "CCW_CW" for counterclockwise for exterior- and clockwise
    for interior polygons, by default "CW_CCW".

> #### Returns
> + ###### `geom` : (geometry or shapely.geometry.GeometryCollection)
    Geometry objects where the chosen winding order is forced upon.

## round_coordinates
```python
round_coordinates(linestrings, rounding_precision)
```

Round all coordinates to a specified precision, e.g. rounding_precision=3 will round
to 3 decimals on the resulting output geometries (after the topology is computed).

> #### Parameters
linestrings: list of shapely.geometry.LineStrings
    LineStrings of which the coordinates will be rounded
> + ###### `rounding_precision` : (int)
    Precision value. Up till how many decimales the coordinates should be rounded.

> #### Returns
linestrings: list of shapely.geometry.LineStrings
    LineStrings of which the coordinates will be rounded

## prettify
```python
prettify(topojson_object)
```

prettify TopoJSON Format output for readability.

> #### Parameters
> + ###### `topojson_object` : (topojson.Topojson)
    [description]

> #### Returns
> + ###### `topojson_object` : (topojson.Topojson)
    pretty printed JSON variant of the topoloy object

## properties_level
```python
properties_level(topojson_object, position='nested')
```

Define where the attributes of the geometry object should be placed. Choose between
"nested" or "foreign. Default is "nested" where the attribute information is placed
within the "properties" ditctionary, part of the geometry.
"foreign", tries to place the attributes on the same level as the geometry.

> #### Parameters
> + ###### `topojson_object` : (topojson.Topojson)
    [description]
> + ###### `position` : (str, optional)
    [description], by default "nested"

## delta_encoding
```python
delta_encoding(linestrings)
```

Function to apply delta-encoding to linestrings. Delta-encoding is a technique ..

Replace in Hashmapper class.

> #### Parameters
> + ###### `linestrings` : (list of shapely.geometry.LineStrings)
    LineStrings that will be delta-encoded

> #### Returns
> + ###### `linestrings` : (list of shapely.geometry.LineStrings)
    LineStrings that are delta-encoded


