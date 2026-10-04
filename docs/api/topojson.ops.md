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
> + ###### `arr` : numpy.array
    2-dimensional numpy array

> #### Returns
> + ###### numpy.void
1-dimensional numpy void object

## np_array_bbox_points_line
```python
np_array_bbox_points_line(line, tree_splitter)
```

Get junctions within bbox of line and return both as numpy array

> #### Parameters
> + ###### `line` : numpy.array
    numpy array with coordinates representing a line segment
> + ###### `tree_splitter` : STRtree
    a STRtree splitter object

> #### Returns
> + ###### numpy.array
`ls_xy`, numpy array from coordinates, if any, representing a line segment
> + ###### numpy.array
`pts_xy_bbox`, numpy array with coordinates that near or on the line

## insert_coords_in_line
```python
insert_coords_in_line(line, tree_splitter)
```

Insert coordinates that are on the line, but where no vertices exists

> #### Parameters
> + ###### `line` : numpy.array
    numpy array with coordinates representing a line segment
> + ###### `tree_splitter` : STRtree
    a STRtree splitter object

> #### Returns
> + ###### (numpy.array)
`new_ls_xy` is an array with inserted coordinates, if any, representing a line
> + ###### segment
(numpy.array)

## shared_path_ends
```python
shared_path_ends(pairs)
```

Start and end points of the paths that each pair of lines shares. These are the
junctions of the topology. Lines that only touch or cross share no path, and equal
lines are skipped.

> #### Parameters
> + ###### `pairs` : iterable of (LineString, LineString)
    Pairs of lines whose envelopes intersect

> #### Returns
> + ###### set of tuple
Junction coordinates

## shared_path_ends_on_grid
```python
shared_path_ends_on_grid(linestrings)
```

Junctions of quantized lines: the start and end points of the paths that each
pair of lines shares, as `shared_path_ends` returns them for all pairs, but
computed for all lines at once on the integer grid.

On the grid, a shared path is a run of segments that both lines contain. A
vertex that lies inside a collinear segment of another line is first inserted
in that line. A vertex is then a junction when the other lines on its incoming
segment differ from those on its outgoing segment. Equal lines count once, as
equal pairs share no path. Lines that pass a vertex twice, or that are closed
and lie wholly on another line, are left to `shared_path_ends` together with
the lines they share segments with. Segments and sets of lines are compared by
64-bit hashes.

> #### Parameters
> + ###### `linestrings` : list of LineString
    Lines with integer coordinates; a closed line continues from its end into
    its start

> #### Returns
> + ###### set of tuple
Junction coordinates

## cut_line
```python
cut_line(line, tree_splitter, is_ring, shared_coords=False)
```

Cut a line at the junctions it passes through. A ring is first rotated to start
at a junction. Collinear points are removed from each part.

> #### Parameters
> + ###### `line` : shapely.geometry.LineString
    Line to cut
> + ###### `tree_splitter` : STRtree or None
    Spatial index on the junction points; None if there are no junctions
> + ###### `is_ring` : bool
    True if the line is the ring of a polygon
> + ###### `shared_coords` : bool
    True to only cut at junctions that are vertices of the line

> #### Returns
> + ###### list of numpy.ndarray
Coordinates of the parts

## cut_lines_on_grid
```python
cut_lines_on_grid(linestrings, junctions, is_ring)
```

Cut quantized lines at the junctions they pass through, as `cut_line` does for
one line, for all lines at once. A ring is first rotated to start at its first
junction; collinear points are removed from each part.

> #### Parameters
> + ###### `linestrings` : list of LineString
    Lines with integer coordinates
> + ###### `junctions` : list of Point
    Junctions with integer coordinates
> + ###### `is_ring` : numpy.ndarray of bool
    True for the lines that are the ring of a polygon

> #### Returns
> + ###### list of numpy.ndarray
Coordinates of the parts, line after line
numpy.ndarray
    Number of parts of each line

## fast_split
```python
fast_split(line, splitter, is_ring)
```

Split a LineString (numpy.array) with a Point or MultiPoint.
This function is a replacement for the shapely.ops.split function, but faster.

> #### Parameters
> + ###### `line` : numpy.array
    numpy array with coordinates that you like to be split
> + ###### `splitter` : numpy.array
    numpy array with coordinates on which the line should be tried splitting
> + ###### `is_ring` : bool
    True if the line represents a ring. In this case, for the first point found, the
    linestring will be rotated rather than split. For consecutive points it will be
    split.

> #### Returns
> + ###### list of numpy.array
If more than 1 item, the line was split. Each item in the list is an

## signed_area
```python
signed_area(ring)
```

Compute the signed area of a ring (polygon)

Note: implementation is numpy variant of shapely's version:
https://github.com/Toblerity/Shapely/blob/master/shapely/algorithms/cga.py

> #### Parameters
> + ###### `ring` : numpy.array
    coordinates representing an exterior or inner ring

> #### Returns
> + ###### float
the signed area

## is_ccw
```python
is_ccw(ring)
```

Provide information if a given ring is clockwise or counterclockwise.

> #### Parameters
> + ###### `ring` : numpy.array
    coordinates representing an exterior or inner ring

> #### Returns
> + ###### boolean
True if ring is counterclockwise and False if ring is clockwise

## properties_foreign
```python
properties_foreign(objects)
```

Try to parse the object properties as foreign members. Reserved keys are:
[`type`, `bbox`, `coordinates`, `geometries`, `geometry`, `properties`, `features`]

If these keys are detected they will not be set as a foreign member and will remain
nested within properties.

Only if the

> #### Parameters
> + ###### `objects` : [type]
    [description]

## bounds
```python
bounds(arr)
```

Returns a (minx, miny, maxx, maxy) tuple (float values) that bounds the object.

> #### Parameters
> + ###### `arr` : np.array
    array to get bounds from

> #### Returns
> + ###### tuple
(minx, miny, maxx, maxy)

## compare_bounds
```python
compare_bounds(b0, b1)
```

Function that compares two bounds with each other. Returns the max bound.

> #### Parameters
> + ###### `b0` : tuple
    tuple of xmin, ymin, xmax, ymax
> + ###### `b1` : tuple
    tuple of xmin, ymin, xmax, ymax

> #### Returns
> + ###### tuple
min of mins and max of maxs

## np_array_from_lists
```python
np_array_from_lists(nested_lists)
```

Function to create numpy array from nested lists. The shape of the numpy array
are the number of nested lists (rows) x the length of the longest nested list
(columns). Rows that contain less values are filled with np.nan values.

> #### Parameters
> + ###### `nested_lists` : list of lists
    list containing nested lists of different sizes.

> #### Returns
> + ###### numpy.ndarray
array created from nested lists, np.nan is used to fill the array

## lists_from_np_array
```python
lists_from_np_array(np_array)
```

Function to convert numpy array to list, where elements set as np.nan
are filtered

## arc_coordinates
```python
arc_coordinates(arcs, transform=None)
```

Coordinates of each arc as an array of its own, so that memory follows the number
of coordinates instead of the number of arcs times the longest arc. With a
transform, the arcs are delta-encoded integers on its grid; they are decoded and
scaled back.

> #### Parameters
> + ###### `arcs` : list of lists
    Arcs of a topology
> + ###### `transform` : dict, optional
    TopoJSON transform (`scale` and `translate`) of the arcs

> #### Returns
> + ###### list of numpy.ndarray
(n, 2) float coordinates of each arc

## get_matches
```python
get_matches(geoms, tree_idx)
```

Function to return the indices of the rtree that intersects with the input geometries

> #### Parameters
> + ###### `geoms` : list
    list of geometries to compare against the STRtree
> + ###### `tree_idx` : STRtree
    a STRtree indexing object

> #### Returns
> + ###### list
list of tuples, where the key of each tuple is the linestring index and the

## select_unique
```python
select_unique(data)
```

Function to return unique pairs within a numpy array.
Example: input as [[1,2], [2,1]] will return as [[1,2]]

> #### Parameters
> + ###### `data` : numpy.array
    2 dimensional array, where each row is a couple

> #### Returns
> + ###### numpy.array
2 dimensional array, where each row is unique.

## select_unique_combs
```python
select_unique_combs(linestrings)
```

Given a set of input linestrings will create unique couple combinations.
Each combination created contains a couple of two linestrings where the envelope
overlaps each other.
Linestrings with non-overlapping envelopes are not returned as combination.

> #### Parameters
> + ###### `linestrings` : list of LineString
    list where each item is a shapely LineString

> #### Returns
> + ###### numpy.array
2 dimensional array, with on each row the index combination

## validate_transform
```python
validate_transform(transform)
```

Validate a TopoJSON transform and return it as a new dict with float values. A
transform that is not valid raises a `ValueError`.

> #### Parameters
> + ###### `transform` : dict
    TopoJSON transform with keys `scale` (`[kx, ky]`, both positive) and
    `translate` (`[x0, y0]`).

> #### Returns
> + ###### dict
The transform with float values for `scale` and `translate`

## remove_spikes
```python
remove_spikes(line)
```

Remove spikes from a quantized line: vertices where the line turns back over the
same segment. End points of open lines are kept and closed rings stay closed. A
line that would collapse is returned unchanged.

> #### Parameters
> + ###### `line` : numpy.ndarray
    (n, 2) integer coordinates without consecutive duplicates

> #### Returns
> + ###### numpy.ndarray
coordinates without spikes

## quantize
```python
quantize(linestrings, bbox, quant_factor=100000.0, transform=None)
```

Function that applies quantization. Quantization removes information by reducing
the precision of each coordinate, effectively snapping each point to a regular grid.

> #### Parameters
> + ###### `linestrings` : list of shapely.geometry.LineStrings
    LineStrings that will be quantized
> + ###### `bbox` : tuple
    Bounding box (`x0`, `y0`, `x1`, `y1`) used to derive the grid. Ignored when
    `transform` is given.
> + ###### `quant_factor` : int
    Quantization factor. Normally this varies between 1e4, 1e5, 1e6. Where a
    higher number means a bigger grid where the coordinates can snap to. Ignored
    when `transform` is given.
> + ###### `transform` : dict, optional
    Fixed TopoJSON transform (`{"scale": [kx, ky], "translate": [x0, y0]}`) that
    defines the grid. When given, the grid does not depend on `bbox`.

> #### Returns
> + ###### list
quantized linestrings
> + ###### dict
`transform`, scale (`kx`, `ky`) and translation (`x0`, `y0`) values

## simplify
```python
simplify(linestrings,
         epsilon,
         algorithm='dp',
         package='simplification',
         input_as='linestring',
         prevent_oversimplify=True)
```

Function that simplifies linestrings. The goal of line simplification is to reduce
the number of points by deleting some trivial points, but without destroying the
essential shape of the lines in the process.

One can choose between the Douglas-Peucker ["dp"] algorithm (which simplifies
a line based upon vertical interval) and Visvalingam-Whyatt ["vw"] (which
progressively removes points with the least-perceptible change).

Docs
* https://observablehq.com/@lemonnish/minify-topojson-in-the-browser
* https://github.com/topojson/topojson-simplify#planarTriangleArea
* https://www.jasondavies.com/simplify/
* https://bost.ocks.org/mike/simplify/
* https://pdfs.semanticscholar.org/9877/cdf50a15367bcb86649b67df8724425c5451.pdf

> #### Parameters
> + ###### `linestrings` : list of shapely.geometry.LineStrings
    LineStrings that will be simplified
> + ###### `epsilon` : int
    Simplification factor. Normally this varies 1.0, 0.1 or 0.001 for "dp" and
    30-100 for "vw".
> + ###### `algorithm` : str, optional
    Choose between `dp` for Douglas-Peucker and `vw` for Visvalingam-Whyatt.
    Defaults to `dp`, as its evaluation maintains to be good (Shi, W. &
    Cheung, C., 2006).
> + ###### `package` : str, optional
    Choose between `simplification` or `shapely`. Both packages contains
    simplification algorithms (`shapely` only `dp`, and `simplification` both `dp`
    and `vw`).
> + ###### `input_as` : str, optional
    Choose between `linestring` or `array`. This function is being called from
    different locations with different input types. Choose `linestring` if the input
    type are shapely.geometry.LineString or `array` if the input is a list of
    coordinate arrays

> #### Returns
> + ###### list of shapely.geometry.LineStrings or ndarrays, depending on the type of the input
LineStrings that are simplified

## dp_weights
```python
dp_weights(xy, starts, ends)
```

Weight of each vertex of lines for Douglas-Peucker: simplifying with a tolerance
`epsilon` keeps exactly the vertices with a weight larger than `epsilon`, as
`shapely.simplify` with `preserve_topology=False` does.

Douglas-Peucker is nested: a vertex is kept when its distance to the segment of
its section is larger than `epsilon` and the vertex that split off its section is
kept as well. Its weight is therefore the smallest distance along its chain of
splits. The splits are found level by level, for all sections of all lines at
once.

> #### Parameters
> + ###### `xy` : numpy.ndarray
    Coordinates of all lines after each other
starts, ends : numpy.ndarray
    Index in `xy` of the first and the last vertex of each line

> #### Returns
> + ###### numpy.ndarray
Weight of each vertex; `inf` for the first and the last vertex of each line

## simplify_keep
```python
simplify_keep(linestrings, keep, algorithm='dp')
```

Simplify lines to a share of their vertices: the share `keep` of the inner
vertices that the algorithm removes last is kept, and the first and the last
vertex of each line. The result is that of `simplify` with the tolerance that is
returned. Vertices with an equal weight are kept or removed together, so the share
can be a little off.

Douglas-Peucker uses the weight of each vertex (`dp_weights`). Visvalingam-Whyatt
searches the tolerance of the package simplification (`_vw_tolerance`).

> #### Parameters
> + ###### `linestrings` : list of numpy.ndarray
    Coordinates of the lines
> + ###### `keep` : float
    Share of the inner vertices to keep, between 0 and 1
> + ###### `algorithm` : str
    `dp` for Douglas-Peucker or `vw` for Visvalingam-Whyatt

> #### Returns
> + ###### list of list
Coordinates of the simplified lines
> + ###### float
The tolerance that gives the same result with `simplify`

## simplify_coverage
```python
simplify_coverage(linestrings, polygons, epsilon, exterior_cw=None)
```

Simplify the rings of polygons together as a coverage, with GEOS
(`shapely.coverage_simplify`, Visvalingam-Whyatt): an edge shared by two polygons
is simplified once, so that they stay matched, and each ring keeps at least three
points. The polygons should form a valid coverage: no overlaps, and the vertices
of shared edges equal.

> #### Parameters
> + ###### `linestrings` : list of LineString
    Rings and lines; the rings of the polygons are replaced in place
> + ###### `polygons` : list of list of int
    Index into `linestrings` of the rings of each polygon, exterior first
> + ###### `epsilon` : float
    Tolerance of `shapely.coverage_simplify`
> + ###### `exterior_cw` : bool, optional
    Orientation of the exterior rings in the result; `None` keeps it as is

> #### Returns
> + ###### list of LineString
The linestrings, with the rings simplified

## restore_collapsed_rings
```python
restore_collapsed_rings(arcs, original, rings)
```

Put back vertices of the original arcs in rings that simplification reduced to
fewer than three distinct points, so that each ring stays at least a triangle. Each
time the original vertex farthest from the ring is put back in its arc; as arcs are
shared, the rings next to it stay matched.

> #### Parameters
> + ###### `arcs` : list of list
    Coordinates of the simplified arcs
> + ###### `original` : list of numpy.ndarray
    Coordinates of the arcs before simplification
> + ###### `rings` : list of list of int
    Arc references (~index for an arc used backward) of each ring

> #### Returns
> + ###### list of list
The arcs, with vertices put back where needed

## winding_order
```python
winding_order(geom, order='CW_CCW')
```

Function that force a certain winding order on the resulting output geometries. One
can choose between `CCW_CW` and `CW_CCW`.

`CW_CCW` implies clockwise for exterior polygons and counterclockwise for interior
polygons (aka the geographical right-hand-rule where the right hand is in the area
of interest as you walk the line).

`CCW_CW` implies counterclockwise for exterior polygons and clockwise for interior
polygons (aka the mathematical right-hand-rule where the right hand curls around
the polygon's exterior with your thumb pointing "up" (toward space), signing a
positive area for the polygon in the signed area sense).

TopoJSON, and so this package, defaults to `CW_CCW`, but depending on the
application you might decide differently.

* https://bl.ocks.org/mbostock/a7bdfeb041e850799a8d3dce4d8c50c8

Only applies to Polygons and MultiPolygons.

> #### Parameters
> + ###### `geom` : geometry or shapely.geometry.GeometryCollection
    Geometry objects where the winding order will be forced upon.
> + ###### `order` : str, optional
    Choose `CW_CCW` for clockwise for exterior- and counterclockwise for
    interior polygons or `CCW_CW` for counterclockwise for exterior- and clockwise
    for interior polygons, by default `CW_CCW`.

> #### Returns
> + ###### geometry or shapely.geometry.GeometryCollection
Geometry objects where the chosen winding order is forced upon.

## round_coordinates
```python
round_coordinates(linestrings, rounding_precision)
```

Round all coordinates to a specified precision, e.g. `rounding_precision=3` will round
to 3 decimals on the resulting output geometries (after the topology is computed).

> #### Parameters
> + ###### `linestrings` : list of shapely.geometry.LineStrings
    LineStrings of which the coordinates will be rounded
> + ###### `rounding_precision` : int
    Precision value. Up till how many decimals the coordinates should be rounded.

> #### Returns
> + ###### list of shapely.geometry.LineStrings
LineStrings of which the coordinates are rounded

## prettify
```python
prettify(topojson_object)
```

prettify TopoJSON Format output for readability.

> #### Parameters
> + ###### `topojson_object` : topojson.Topojson
    object to be pretty printed

> #### Returns
> + ###### topojson.Topojson
pretty printed JSON variant of the topology object

## properties_level
```python
properties_level(topojson_object, position='nested')
```

Define where the attributes of the geometry object should be placed. Choose between
`nested` or `foreign`. Default is `nested` where the attribute information is placed
within the "properties" dictionary, part of the geometry.
`foreign`, tries to place the attributes on the same level as the geometry.

> #### Parameters
> + ###### `topojson_object` : topojson.Topojson
    [description]
> + ###### `position` : str, optional
    [description], by default "nested"

## delta_encoding
```python
delta_encoding(linestrings)
```

Delta-encode linestrings: the first coordinate of each linestring is absolute,
every next coordinate is relative to the previous one. All linestrings are
encoded at once.

> #### Parameters
> + ###### `linestrings` : list of shapely.geometry.LineStrings, arrays or lists
    Linestrings with integer coordinates

> #### Returns
> + ###### list of lists
Delta-encoded linestrings

## delta_decoding
```python
delta_decoding(arcs)
```

Decode delta-encoded arcs to absolute coordinates. All arcs are decoded at once.

> #### Parameters
> + ###### `arcs` : list of lists
    Delta-encoded arcs

> #### Returns
> + ###### list of numpy.ndarray
(n, 2) integer coordinates of each arc

## arc_areas
```python
arc_areas(arcs)
```

Twice the signed area that each arc adds to a ring (shoelace formula), exact on
the integer grid. The area of a ring is the sum over its arcs, with the sign
flipped for an arc used backward.

> #### Parameters
> + ###### `arcs` : list of numpy.ndarray
    Integer coordinates of the arcs

> #### Returns
> + ###### numpy.ndarray
Twice the signed area of each arc, as integers

## cart
```python
cart(arr)
```

Function that returns all combinations as a 2D array
[3, 152,  62, 52] is returned as [[152,  62], [152,  52], [152,   3]]

## hash_paths
```python
hash_paths(paths)
```

Hash of each path that is the same for duplicate paths: equal coordinates in any
direction and, for a closed path, from any start. The x and y values of a path are
hashed as multisets (the closing point of a closed path left out), together with
their number and whether the path is closed.

> #### Parameters
> + ###### `paths` : list of numpy.ndarray
    Coordinates of each path

> #### Returns
> + ###### numpy.ndarray
int64 hash of each path

## find_duplicates
```python
find_duplicates(segments_list, type='array')
```

Function for solely detecting and recording duplicate LineStrings. The function
converts and sorts the coordinates of each linestring and gets the hash. Using the
hashes it can quickly detect duplicates and return the indices.

> #### Parameters
> + ###### `segments_list` : list of paths
    list of valid paths
> + ###### `type` : str
    set if paths is `array` or `linestring`

## map_values
```python
map_values(arr, search_vals, replace_vals)
```

This function replace values element-wise in a numpy array.
Its quick and avoids a np.where-loop (which is slow).
The result is a new array, not inplace.

> #### Parameters
> + ###### `arr` : np.array
    input array
> + ###### `search_vals` : list or 1D np.array
    array with 'bad' values
> + ###### `replace_vals` : list or 1D np.array
    array with 'good' values

> #### Returns
> + ###### np.array
new array with replaced values
