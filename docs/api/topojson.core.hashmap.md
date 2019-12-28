---
layout: default
title: topojson.core.hashmap
parent: API reference
nav_order: 6
---


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

>#### Parameters
> + 
###### `arc_ids` : (list)
    list containing the index values of the arcs
> + 
###### `shared_bool` : (list)
    boolean list with same length as arc_ids,
    True means the arc is shared, False means it is a non-shared arc

>#### Returns
> + 
###### `order_of_arc` : (numpy array)
    array containg values if first or last arc should be used to order
> + 
###### `split_arc_ids` : (list of numpy arrays)
    array containing splitted arc ids

### backward_arcs
```python
Hashmap.backward_arcs(self, arc_ids)
```

Function to check if the shared arcs in geom should be backward.
If so, are written as -(index+1)

>#### Parameters
> + 
###### `arc_ids` : (list)
    description of input

>#### Returns
> + 
###### `arc_ids` : (list)
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


