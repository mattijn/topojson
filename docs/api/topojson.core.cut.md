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

> #### Returns
> + ###### dict
object updated and expanded with
> + ###### - updated key: linestrings
- new key: bookkeeping_duplicates

### to_dict
```python
Cut.to_dict(self)
```

Convert the Cut object to a dictionary.

### to_svg
```python
Cut.to_svg(self, separate=False, include_junctions=False)
```

Display the linestrings and junctions as SVG.

> #### Parameters
> + ###### `separate` : boolean
    If `True`, each of the linestrings will be displayed separately.
    Default is `False`
> + ###### `include_junctions` : boolean
    If `True`, the detected junctions will be displayed as well.
    Default is `False`


