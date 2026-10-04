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
> + ###### `data` : _any_ geometric type
    Geometric data, as for `Extract`
> + ###### `options` : dict or TopoOptions
    Options of the topology, see `Topology`

> #### Returns
> + ###### dict
Output of `Extract` with the key `junctions`, and `transform` if quantized

### to_dict
```python
Join.to_dict()
```

Convert the Join object to a dictionary.

### to_svg
```python
Join.to_svg(separate=False, include_junctions=False)
```

Display the linestrings and junctions as SVG.

> #### Parameters
> + ###### `separate` : boolean
    If `True`, each of the linestrings will be displayed separately.
    Default is `False`
> + ###### `include_junctions` : boolean
    If `True`, the detected junctions will be displayed as well.
    Default is `False`


