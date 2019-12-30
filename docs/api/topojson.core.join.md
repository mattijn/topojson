---
layout: default
title: topojson.core.join
parent: API reference
nav_order: 3
---


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

> #### Parameters
> + ###### `data` : (dict)
    object created by the method topojson.extract.
> + ###### `quant_factor` : (int, optional (default: None))
    quantization factor, used to constrain float numbers to integer values.
    - Use 1e4 for 5 valued values (00001-99999)
    - Use 1e6 for 7 valued values (0000001-9999999)

> #### Returns
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

> #### Parameters
> + ###### `data` : (dict)
    object created by the method topojson.extract.
> + ###### `quant_factor` : (int, optional (default: None))
    quantization factor, used to constrain float numbers to integer values.
    - Use 1e4 for 5 valued values (00001-99999)
    - Use 1e6 for 7 valued values (0000001-9999999)

> #### Returns
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

> #### Parameters
> + ###### `g1` : (shapely.geometry.LineString)
    first geometry
> + ###### `g2` : (shapely.geometry.LineString)
    second geometry


