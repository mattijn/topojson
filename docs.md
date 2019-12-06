# topojson

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

# topojson.core.topology

## Topology
```python
Topology(self, data, topology=True, prequantize=True, topoquantize=False, presimplify=False, toposimplify=0.0001, simplify_with='shapely', simplify_algorithm='dp', winding_order='CW_CCW')
```

Returns a TopoJSON topology for the specified geometric object.
TopoJSON is an extension of GeoJSON providing multiple approaches
to compress the geographical input data. These options include
simplifying the linestrings or quantizing the coordinates but
foremost the computation of a topology.

Parameters
----------
data : _any_ geometric type
    Geometric data that should be converted into TopoJSON
topology : boolean
    Specifiy if the topology should be computed for deriving the
    TopoJSON.
    Default is True.
prequantize : boolean or int
    If the prequantization parameter is specified, the input geometry
    is quantized prior to computing the topology, the returned
    topology is quantized, and its arcs are delta-encoded.
    Quantization is recommended to improve the quality of the topology
    if the input geometry is messy (i.e., small floating point error
    means that adjacent boundaries do not have identical values);
    typical values are powers of ten, such as 1e4, 1e5 or 1e6.
    Default is True (which correspond to a quantize factor of 1e6).
topoquantize : boolean or int
    If the topoquantization parameter is specified, the input geometry
    is quantized after the topology is constructed. If the topology is
    already quantized this will be resolved first before the
    topoquantization is applied.
    Default is False.
presimplify : boolean or float
    Apply presimplify to remove unnecessary points from linestrings
    before the topology is constructed. This will simplify the input
    geometries.
    Default is False.
toposimplify : boolean or float
    Apply toposimplify to remove unnecessary points from arcs after
    the topology is constructed. This will simplify the constructed
    arcs without altering the topological relations. Sensible values
    are in the range of 0.0001 to 10.
    Defaults to 0.0001.
simplify_with : str
    Sets the package to use for simplifying (both pre- and
    toposimplify). Choose between `shapely` or `simplification`.
    Shapely adopts solely Douglas-Peucker and simplification both
    Douglas-Peucker and Visvalingam-Whyatt. The pacakge simplification
    is known to be quicker than shapely.
    Default is "shapely".
simplify_algorithm : str
    Choose between 'dp' and 'vw', for Douglas-Peucker or Visvalingam-
    Whyatt respectively. 'vw' will only be selected if `simplify_with`
    is set to `simplification`.
    Default is `dp`, since it still "produces the most accurate
    generalization" (Chi & Cheung, 2006).
winding_order : str
    Determines the winding order of the features in the output
    geometry. Choose between `CW_CCW` for clockwise orientation for
    outer rings and counter-clockwise for interior rings. Or `CCW_CW`
    for counter-clockwise for outer rings and clockwise for interior
    rings.
    Default is `CW_CCW`.

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

Parameters
----------
data : Union[shapely.geometry.LineString, shapely.geometry.MultiLineString,
shapely.geometry.Polygon, shapely.geometry.MultiPolygon, shapely.geometry.Point,
shapely.geometry.MultiPoint, shapely.geometry.GeometryCollection, geojson.Feature,
geojson.FeatureCollection, geopandas.GeoDataFrame, geopandas.GeoSeries, dict, list]
    Different types of a geometry object, originating from shapely, geojson,
    geopandas and dictionary or list of objects that contain a __geo_interface__.

Returns
-------
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

Parameters
----------
geom : shapely.geometry.LineString
    LineString instance

### extract_multiline
```python
Extract.extract_multiline(self, geom)
```
*geom* type is MultiLineString instance.

Parameters
----------
geom : shapely.geometry.MultiLineString
    MultiLineString instance

### extract_ring
```python
Extract.extract_ring(self, geom)
```
*geom* type is Polygon instance.

Parameters
----------
geom : shapely.geometry.Polygon
    Polygon instance

### extract_multiring
```python
Extract.extract_multiring(self, geom)
```
*geom* type is MultiPolygon instance.

Parameters
----------
geom : shapely.geometry.MultiPolygon
    MultiPolygon instance

### extract_point
```python
Extract.extract_point(self, geom)
```
*geom* type is Point instance.
coordinates are directly passed to "coordinates"

Parameters
----------
geom : shapely.geometry.Point
    Point instance

### extract_multipoint
```python
Extract.extract_multipoint(self, geom)
```
*geom* type is MultiPoint instance.

Parameters
----------
geom : shapely.geometry.MultiPoint
    MultiPoint instance

### extract_geometrycollection
```python
Extract.extract_geometrycollection(self, geom)
```
*geom* type is GeometryCollection instance.

Parameters
----------
geom : shapely.geometry.GeometryCollection
    GeometryCollection instance

### extract_featurecollection
```python
Extract.extract_featurecollection(self, geom)
```
*geom* type is FeatureCollection instance.

Parameters
----------
geom : geojson.FeatureCollection
    FeatureCollection instance

### extract_feature
```python
Extract.extract_feature(self, geom)
```
*geom* type is Feature instance.

Parameters
----------
geom : geojson.Feature
    Feature instance

### extract_geopandas
```python
Extract.extract_geopandas(self, geom)
```
*geom* type is GeoDataFrame or GeoSeries instance.

Parameters
----------
geom : geopandas.GeoDataFrame or geopandas.GeoSeries
    GeoDataFrame or GeoSeries instance

### extract_list
```python
Extract.extract_list(self, geom)
```
*geom* type is List instance.

Parameters
----------
geom : list
    List instance

### extract_string
```python
Extract.extract_string(self, geom)
```
*geom* type is String instance.

Parameters
----------
geom : str
    String instance

### extract_dictionary
```python
Extract.extract_dictionary(self, geom)
```
*geom* type is Dictionary instance.

Parameters
----------
geom : dict
    Dictionary instance

# topojson.core.join

## Join
```python
Join(self, data, options={})
```

This class targets the following objectives:
1. Quantization of input linestrings if necessary
2. Identifies junctions of shared paths

The join function is the second step in the topology computation.
The following sequence is adopted:
1. extract
2. join
3. cut
4. dedup
5. hashmap

Parameters
----------
data : dict
    object created by the method topojson.extract.
quant_factor : int, optional (default: None)
    quantization factor, used to constrain float numbers to integer values.
    - Use 1e4 for 5 valued values (00001-99999)
    - Use 1e6 for 7 valued values (0000001-9999999)

Returns
-------
dict
    object expanded with
    - new key: junctions
    - new key: transform (if quant_factor is not None)

### joiner
```python
Join.joiner(self, data)
```

Entry point for the class Join. This function identiefs junctions
(intersection points) of shared paths.

The join function is the second step in the topology computation.
The following sequence is adopted:
1. extract
2. join
3. cut
4. dedup
5. hashmap

Detects the junctions of shared paths from the specified hash of linestrings.

After decomposing all geometric objects into linestrings it is necessary to
detect the junctions or start and end-points of shared paths so these paths can
be 'merged' in the next step. Merge is quoted as in fact only one of the
shared path is kept and the other path is removed.

Parameters
----------
data : dict
    object created by the method topojson.extract.
quant_factor : int, optional (default: None)
    quantization factor, used to constrain float numbers to integer values.
    - Use 1e4 for 5 valued values (00001-99999)
    - Use 1e6 for 7 valued values (0000001-9999999)

Returns
-------
dict
    object expanded with
    - new key: junctions
    - new key: transform (if quant_factor is not None)

### validate_linemerge
```python
Join.validate_linemerge(self, merged_line)
```

Return list of linestrings. If the linemerge was a MultiLineString
then returns a list of multiple single linestrings

### shared_segs
```python
Join.shared_segs(self, g1, g2)
```

This function returns the segments that are shared with two input geometries.
The shapely function `shapely.ops.shared_paths()` is adopted and can catch
both the shared paths with the same direction for both inputs as well as the
shared paths with the opposite direction for one the two inputs.

The returned object extents the `segments` property with detected segments.
Where each seperate segment is a linestring between two points.

Parameters
----------
g1 : shapely.geometry.LineString
    first geometry
g2 : shapely.geometry.LineString
    second geometry

# topojson.core.cut

## Cut
```python
Cut(self, data, options={})
```

This class targets the following objectives:
1. Split linestrings given the junctions of shared paths
2. Identifies indexes of linestrings that are duplicates

The cut function is the third step in the topology computation.
The following sequence is adopted:
1. extract
2. join
3. cut
4. dedup
5. hashmap

Parameters
----------
data : dict
    object created by the method topojson.Join.

Returns
-------
dict
    object updated and expanded with
    - updated key: linestrings
    - new key: bookkeeping_duplicates
    - new key: bookkeeping_linestrings

### cutter
```python
Cut.cutter(self, data)
```

Entry point for the class Cut.

The cut function is the third step in the topology computation.
The following sequence is adopted:
1. extract
2. join
3. cut
4. dedup
5. hashmap

Parameters
----------
data : dict
    object created by the method topojson.join.

Returns
-------
dict
    object updated and expanded with
    - updated key: linestrings
    - new key: bookkeeping_duplicates
    - new key: bookkeeping_linestrings

### flatten_and_index
```python
Cut.flatten_and_index(self, slist)
```

Function to create a flattened list of splitted linestrings and create a
numpy array of the bookkeeping_geoms for tracking purposes.

Parameters
----------
slist : list of LineString
    list of splitted LineStrings

Returns
-------
list
    segmntlist flattens the nested LineString in slist
numpy.array
    array_bk is a bookkeeping array with index values to each LineString

### find_duplicates
```python
Cut.find_duplicates(self, segments_list)
```

Function for solely detecting and recording duplicate LineStrings.
Firstly creates couple-combinations of LineStrings. A couple is defined
as two linestrings where the enveloppe overlaps. Indexes of duplicates are
appended to the list self.duplicates.

Parameters
----------
segments_list : list of LineString
    list of valid LineStrings


# topojson.core.dedup

## Dedup
```python
Dedup(self, data, options={})
```

Dedup duplicates and merge contiguous arcs

### deduper
```python
Dedup.deduper(self, data)
```

Deduplication of linestrings that contain duplicates

The dedup function is the fourth step in the topology computation.
The following sequence is adopted:
1. extract
2. join
3. cut
4. dedup
5. hashmap

### find_merged_linestring
```python
Dedup.find_merged_linestring(self, data, no_ndp_arcs, ndp_arcs, ndp_arcs_bk)
```

Function to find the index of LineString in a MultiLineString object which
contains merged LineStrings.

Parameters
----------
data : dict
    object that contains the 'linestrings'
no_ndp_arcs : int
    number of non-duplicate arcs
ndp_arcs : array
    array containing index values of the related arcs

Returns
-------
int
    index of LineString that contains merged LineStrings

### deduplicate
```python
Dedup.deduplicate(self, dup_pair_list, linestring_list, array_bk)
```

Function to deduplicate items

Parameters
----------
dup_pair_list : numpy.ndarray
    array containing pair of indexes that refer to duplicate linestrings.
linestring_list : list of shapely.geometry.LineStrings
    list of linestrings from which items will be removed.
array_bk : numpy.ndarray
    array used for bookkeeping of linestrings.

Returns
-------
numpy.ndarray
    bookkeeping array of shared arcs
numpy.ndarray
    array where each processed pair is set to -99

### merge_contigious_arcs
```python
Dedup.merge_contigious_arcs(self, data, sliced_array_bk_ndp)
```

Function that iterate over geoms that contain shared arcs and try linemerge
on remaining arcs. The merged contigious arc is placed back in the 'linestrings'
object.
The arcs that can be popped are placed within the merged_arcs_idx list

Parameters
----------
data : dict
    object that contains the 'linestrings'.
sliced_array_bk_ndp : numpy.ndarray
    bookkeeping array where shared linestrings are set to np.nan.

### pop_merged_arcs
```python
Dedup.pop_merged_arcs(self, data, array_bk, array_bk_sarcs)
```

The collected indici that can be popped, since they have been merged

# topojson.core.hashmap

## Hashmap
```python
Hashmap(self, data, options={})
```

hash arcs based on their type

### hashmapper
```python
Hashmap.hashmapper(self, data)
```

Hashmap function resolves bookkeeping results to object arcs.

The hashmap function is the fifth step in the topology computation.
The following sequence is adopted:
1. extract
2. join
3. cut
4. dedup
5. hashmap

Developping Notes:
* PostGIS Tips for Power Users: http://2010.foss4g.org/presentations/3369.pdf

### hash_order
```python
Hashmap.hash_order(self, arc_ids, shared_bool)
```

create a decision list with the following options:
0 - skip the array
1 - follow the order of the first arc
2 - follow the order of the last arc
3 - align first two arcs and continue

Parameters
----------
arc_ids : list
    list containing the index values of the arcs
shared_bool : list
    boolean list with same length as arc_ids,
    True means the arc is shared, False means it is a non-shared arc

Returns
-------
order_of_arc : numpy array
    array containg values if first or last arc should be used to order
split_arc_ids : list of numpy arrays
    array containing splitted arc ids

### backward_arcs
```python
Hashmap.backward_arcs(self, arc_ids)
```

Function to check if the shared arcs in geom should be backward.
If so, are written as -(index+1)

Parameters
----------
arc_ids : list
    description of input

Returns
-------
arc_ids : list
    description of output

### resolve_bookkeeping
```python
Hashmap.resolve_bookkeeping(self, geoms, key)
```

Function that is activated once the key of interest in the find_arcs function
is detected. It replaces the geom ids with the corresponding arc ids.

### resolve_objects
```python
Hashmap.resolve_objects(self, keys, dictionary)
```

Function that resolves the bookkeeping back to the arcs in the objects.
Support also nested dicts such as GeometryCollections

### resolve_arcs
```python
Hashmap.resolve_arcs(self, feat)
```

Function that resolves the arcs based on the type of the feature

# topojson.utils

## singledispatch_class
```python
singledispatch_class(func)
```

The singledispatch function only applies to functions. This function creates a
wrapper around the singledispatch so it can be used for class instances.

Returns
-------
dispatch
    dispatcher for methods

## serialize_as_geodataframe
```python
serialize_as_geodataframe(topo_object, url=False)
```

Convert a topology dictionary or string into a GeoDataFrame.

Parameters
----------
topo_object : dict, str
    a complete object representing an topojson encoded file as
    dict, str-object or str-url

Returns
-------
gdf : geopandas.GeoDataFrame
    topojson object parsed GeoDataFrame

# topojson.ops

## asvoid
```python
asvoid(arr)
```

Utility function to create a 1-dimensional numpy void object (bytes)
of a 2-dimensional array. This is useful for the function numpy.in1d(),
since it only accepts 1-dimensional objects.

Parameters
----------
arr : numpy.array
    2-dimensional numpy array

Returns
-------
numpy.void
    1-dimensional numpy void object

## insert_coords_in_line
```python
insert_coords_in_line(line, tree_splitter)
```

Insert coordinates that are on the line, but where no vertices exists

Parameters
----------
line : numpy.array
    numpy array with coordinates representing a line segment
tree_splitter: STRtree
    a STRtree splitter object

Returns
-------
new_ls_xy : numpy.array
    numpy array with inserted coordinates, if any, representing a line segment
pts_xy_on_line : numpy.array
    numpy array with with coordinates that are on the lin

## fast_split
```python
fast_split(line, splitter)
```

Split a LineString (numpy.array) with a Point or MultiPoint.
This function is a replacement for the shapely.ops.split function, but faster.

Parameters
----------
line : numpy.array
    numpy array with coordinates that you like to be split
splitter : numpy.array
    numpy array with coordiates on wich the line should be tried splitting

Returns
-------
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

Parameters
----------
ring : shapely.geometry.LinearRing
    an exterior or inner ring of a shapely.geometry.Polygon

Returns
-------
float
    the signed area

## is_ccw
```python
is_ccw(ring)
```
provide information if a given ring is clockwise or counterclockwise.

Parameters
----------
ring : shapely.geometry.LinearRing
    an exterior or inner ring of a shapely.geometry.Polygon

Returns
-------
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

Parameters
----------
objects : [type]
    [description]

## compare_bounds
```python
compare_bounds(b0, b1)
```

Function that compares two bounds with each other. Returns the max bound.

Parameters
----------
b0 : tuple
    tuple of xmin, ymin, xmax, ymax
b1 : tuple
    tuple of xmin, ymin, xmax, ymax

Returns
-------
tuple
    min of mins and max of maxs

## np_array_from_lists
```python
np_array_from_lists(nested_lists)
```

Function to create numpy array from nested lists. The shape of the numpy array
are the number of nested lists (rows) x the length of the longest nested list
(columns). Rows that contain less values are filled with np.nan values.

Parameters
----------
nested_lists : list of lists
    list containing nested lists of different sizes.

Returns
-------
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

Parameters
----------
geoms : list
    list of geometries to compare against the STRtree
tree_idx: STRtree
    a STRtree indexing object

Returns
-------
list
    list of tuples, where the key of each tuple is the linestring index and the
    value of each key is a list of junctions intersecting bounds of linestring.

## select_unique
```python
select_unique(data)
```

Function to return unique pairs within a numpy array.
Example: input as [[1,2], [2,1]] will return as [[1,2]]

Parameters
----------
data : numpy.array
    2 dimensional array, where each row is a couple

Returns
-------
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

Parameters
----------
linestrings : list of LineString
    list where each item is a shapely LineString

Returns
-------
numpy.array
    2 dimensional array, with on each row the index combination
    of a unique couple LineString with overlapping enveloppe

## quantize
```python
quantize(linestrings, bbox, quant_factor=1000000.0)
```

Function that applies quantization. Quantization removes information by reducing
the precision of each coordinate, effectively snapping each point to a regular grid.

Parameters
----------
linestrings: list of shapely.geometry.LineStrings
    LineStrings that will be quantized
quant_factor : int
    Quantization factor. Normally this varies between 1e4, 1e5, 1e6. Where a
    higher number means a bigger grid where the coordinates can snap to.

Returns
-------
transform : dict
    scale (kx, ky) and translation (x0, y0) values
bbox : array
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

Parameters
----------
linestrings: list of shapely.geometry.LineStrings
    LineStrings that will be simplified
epsilon : int
    Simplification factor. Normally this varies 1.0, 0.1 or 0.001 for "rdp" and
    30-100 for "vw".
algorithm : str, optional
    Choose between `dp` for Douglas-Peucker and `vw` for Visvalingam–Whyatt.
    Defaults to `dp`, as its evaluation maintains to be good (Song & Miao, 2016).
package : str, optional
    Choose between `simplification` or `shapely`. Both pachakges contains
    simplification algorithms (`shapely` only `dp`, and `simplification` both `dp`
    and `vw`).
input_as : str, optional
    Choose between `linestring` or `array`. This function is being called from
    different locations with different input types. Choose `linestring` if the input
    type are shapely.geometry.LineString or `array` if the input are numpy.array
    coordinates

Returns
-------
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

Parameters
----------
geom : geometry or shapely.geometry.GeometryCollection
    Geometry objects where the winding order will be forced upon.
order : str, optional
    Choose "CW_CCW" for clockwise for exterior- and counterclockwise for
    interior polygons or "CCW_CW" for counterclockwise for exterior- and clockwise
    for interior polygons, by default "CW_CCW".

Returns
-------
geom : geometry or shapely.geometry.GeometryCollection
    Geometry objects where the chosen winding order is forced upon.

## round_coordinates
```python
round_coordinates(linestrings, rounding_precision)
```

Round all coordinates to a specified precision, e.g. rounding_precision=3 will round
to 3 decimals on the resulting output geometries (after the topology is computed).

Parameters
----------
linestrings: list of shapely.geometry.LineStrings
    LineStrings of which the coordinates will be rounded
rounding_precision : int
    Precision value. Up till how many decimales the coordinates should be rounded.

Returns
-------
linestrings: list of shapely.geometry.LineStrings
    LineStrings of which the coordinates will be rounded

## prettify
```python
prettify(topojson_object)
```

prettify TopoJSON Format output for readability.

Parameters
----------
topojson_object : topojson.Topojson
    [description]

Returns
-------
topojson_object : topojson.Topojson
    pretty printed JSON variant of the topoloy object

## properties_level
```python
properties_level(topojson_object, position='nested')
```

Define where the attributes of the geometry object should be placed. Choose between
"nested" or "foreign. Default is "nested" where the attribute information is placed
within the "properties" ditctionary, part of the geometry.
"foreign", tries to place the attributes on the same level as the geometry.

Parameters
----------
topojson_object : topojson.Topojson
    [description]
position : str, optional
    [description], by default "nested"

## delta_encoding
```python
delta_encoding(linestrings)
```

Function to apply delta-encoding to linestrings. Delta-encoding is a technique ..

Replace in Hashmapper class.

Parameters
----------
linestrings : list of shapely.geometry.LineStrings
    LineStrings that will be delta-encoded

Returns
-------
linestrings : list of shapely.geometry.LineStrings
    LineStrings that are delta-encoded

