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

### to_dict
```python
Hashmap.to_dict()
```

Convert the Hashmap object to a dictionary.

### to_svg
```python
Hashmap.to_svg(separate=False)
```

Display the linestrings and junctions as SVG.

> #### Parameters
> + ###### `separate` : boolean
    If `True`, each of the linestrings will be displayed separately.
    Default is `False`

### to_json
```python
Hashmap.to_json()
```

Convert the Hashmap object to a JSON object.

### to_alt
```python
Hashmap.to_alt(projection='identity')
```

Display as Altair visualization.

> #### Parameters
> + ###### `projection` : str
    Defines the projection of the visualization. Defaults to a non-geographic,
    Cartesian projection (known by Altair as `identity`).


