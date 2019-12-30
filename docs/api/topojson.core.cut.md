---
layout: default
title: topojson.core.cut
parent: API reference
nav_order: 4
---


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

__Arguments__

----------
- __data __: dict
    object created by the method topojson.Join.

> #### Returns
dict
    object updated and expanded with
- __- updated key__: linestrings
- __- new key__: bookkeeping_duplicates
- __- new key__: bookkeeping_linestrings

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

> #### Parameters
> + ###### `data` : (dict)
    object created by the method topojson.join.

> #### Returns
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

> #### Parameters
> + ###### `slist` : (list of LineString)
    list of splitted LineStrings

> #### Returns
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

> #### Parameters
> + ###### `segments_list` : (list of LineString)
    list of valid LineStrings



