---
layout: default
title: topojson.core.dedup
parent: API reference
nav_order: 5
---


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

> #### Parameters
> + ###### `data` : (dict)
    object that contains the 'linestrings'
> + ###### `no_ndp_arcs` : (int)
    number of non-duplicate arcs
ndp_arcs : array
    array containing index values of the related arcs

> #### Returns
int
    index of LineString that contains merged LineStrings

### deduplicate
```python
Dedup.deduplicate(self, dup_pair_list, linestring_list, array_bk)
```

Function to deduplicate items

> #### Parameters
> + ###### `dup_pair_list` : (numpy.ndarray)
    array containing pair of indexes that refer to duplicate linestrings.
> + ###### `linestring_list` : (list of shapely.geometry.LineStrings)
    list of linestrings from which items will be removed.
> + ###### `array_bk` : (numpy.ndarray)
    array used for bookkeeping of linestrings.

> #### Returns
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

> #### Parameters
> + ###### `data` : (dict)
    object that contains the 'linestrings'.
> + ###### `sliced_array_bk_ndp` : (numpy.ndarray)
    bookkeeping array where shared linestrings are set to np.nan.

### _pop_merged_arcs
```python
Dedup._pop_merged_arcs(self, data, array_bk, array_bk_sarcs)
```

The collected indici that can be popped, since they have been merged


