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
> + ###### `data` : dict
    object created by the method topojson.extract.
> + ###### `quant_factor` : int, optional (default: None)
    quantization factor, used to constrain float numbers to integer values.
    - Use 1e4 for 5 valued values (00001-99999)
    - Use 1e5 for 6 valued values (000001-999999)
    - Use 1e6 for 7 valued values (0000001-9999999)

> #### Returns
> + ###### dict
object expanded with
> + ###### - new key: junctions
- new key: transform (if quant_factor is not None)

### to_dict
```python
Join.to_dict(self)
```

Convert the Join object to a dictionary.

### to_svg
```python
Join.to_svg(self, separate=False, include_junctions=False)
```

Display the linestrings and junctions as SVG.

> #### Parameters
> + ###### `separate` : boolean
    If `True`, each of the linestrings will be displayed separately.
    Default is `False`
> + ###### `include_junctions` : boolean
    If `True`, the detected junctions will be displayed as well.
    Default is `False`


