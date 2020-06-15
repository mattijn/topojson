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

### to_dict
```python
Dedup.to_dict(self)
```

Convert the Dedup object to a dictionary.

### to_svg
```python
Dedup.to_svg(self, separate=False, include_junctions=False)
```

Display the linestrings and junctions as SVG.

> #### Parameters
> + ###### `separate` : boolean
    If `True`, each of the linestrings will be displayed separately.
    Default is `False`
> + ###### `include_junctions` : boolean
    If `True`, the detected junctions will be displayed as well.
    Default is `False`


