
# Settings and tuning

```python exec="on" session="examplesettings-tuning"
import threading
from concurrent.futures import ThreadPoolExecutor

import markdown_exec._internal.formatters.python as _python

# Zensical renders pages in parallel threads; GDAL and PROJ (geopandas) crash when
# they are used from more than one thread, so every example runs on one thread
with _python.__dict__.setdefault("_one_thread_lock", threading.Lock()):
    if not hasattr(_python, "_one_thread"):
        _python._one_thread = ThreadPoolExecutor(max_workers=1)
        _run = _python.exec_python

        def _exec_python(*args, **kwargs):
            return _python._one_thread.submit(_run, *args, **kwargs).result()

        _python.exec_python = _exec_python

import numpy as np
import topojson as tp


class _Drawing:
    def __getattr__(self, name):
        return lambda *args, **kwargs: self

    __or__ = __and__ = __add__ = lambda self, other: self


for _name in ["to_alt", "to_svg", "to_widget"]:
    setattr(tp.Topology, _name, lambda self, *args, **kwargs: _Drawing())
try:
    import geopandas

    geopandas.GeoDataFrame.plot = property(lambda self: lambda *a, **k: _Drawing())
except ImportError:
    pass
```

By adopting the TopoJSON format is possible to store geographical data as topology. Adopting this approach makes smaller files than its GeoJSON counterpart. This process allows varies options, which are described below:

1. [topology](#topology)
2. [prequantize](#prequantize)
3. [topoquantize](#topoquantize)
4. [presimplify](#presimplify)
5. [toposimplify](#toposimplify)
6. [shared_coords](#shared_coords)
7. [prevent_oversimplify](#prevent_oversimplify)
8. [simplify_with](#simplify_with)
9. [simplify_algorithm](#simplify_algorithm)
10. [winding_order](#winding_order)
11. [object_name](#object_name)
12. [ignore_index](#ignore_index)

* * * 

## topology

boolean
Specify if the topology should be computed for deriving the TopoJSON.
Default is `True`.

!!! example


    Given the following two linestrings with one side sharing:
    ```python
    import topojson as tp
    from shapely import geometry

    data = geometry.MultiLineString([
        [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]], 
        [[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]
    ])
    data
    ```

    ```python exec="on" session="examplesettings-tuning"
    import topojson as tp
    from shapely import geometry

    data = geometry.MultiLineString([
        [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]], 
        [[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]
    ])
    data
    ```
    <figure class="parts" data-src="../json/fig_settings_topology_input.json" data-label="Two squares that share a side"><svg></svg></figure>

    By setting `topology=False` a TopoJSON structured file format is created without considering shared segments (the setting `prequantize=False` avoids computing the delta-encoding):
    ```python
    tp.Topology(data, topology=False, prequantize=False)
    ```

    ```python exec="on" session="examplesettings-tuning" result="text"
    _ = tp.Topology(data, topology=False, prequantize=False)
    if isinstance(_, dict):
        print(__import__('pprint').pformat(_, sort_dicts=False, width=88))
    else:
        print(_)
    ```
    As can be seen, the geometries are referenced by two segments (`'arcs': [[0], [1]]`), where each segment is a single linestring (see: `arcs`).

    When doing the same with `topology=True`, there are three `arcs`. Where one arc is referenced two times, namely arc `2` (arc `-3` is arc `2` reversed).
    ```python
    tp.Topology(data, topology=True, prequantize=False)
    ```

    ```python exec="on" session="examplesettings-tuning" result="text"
    _ = tp.Topology(data, topology=True, prequantize=False)
    if isinstance(_, dict):
        print(__import__('pprint').pformat(_, sort_dicts=False, width=88))
    else:
        print(_)
    ```



<!-- **Note:** The following figure is here to test if interactivity is possible

<div id="embed_tuning_topology"></div> -->


* * *         

## prequantize

boolean, int, dict

If the prequantization parameter is specified, the input geometry is 
quantized prior to computing the topology. The returned topology is 
quantized, and its arcs are delta-encoded. 

Quantization is recommended to 
improve the quality of the topology if the input geometry is messy (i.e., 
small floating point error means that adjacent boundaries do not have 
identical values); typical values are powers of ten, such as `1e4`, `1e5` or 
`1e6`. Default is `True` (which correspond to a quantize factor of `1e5`).

Instead of a factor, a TopoJSON transform can be given as a dict,
`{"scale": [kx, ky], "translate": [x0, y0]}`. The grid is then fixed and does not
depend on the bounding box of the input, so topologies of different inputs (or of
different runs) share the same grid. This is what
[incremental updates](incremental-updates.md) build on.
See [quantization](quantization.md) for how the grid follows the bounding box
and how to choose it yourself.

!!! example


    Quantization is a two-step process, namely normalization and delta-encoding. Given the following two polygon with no sides shared, since the left-polygon has a x-max coordinate at `0.97` and the right-polygon has a x-min coordinate at `1.03`:
    ```python
    import topojson as tp
    from shapely import geometry

    data = geometry.MultiLineString([
        [[0, 0], [0.97, 0], [0.97, 1], [0, 1], [0, 0]], 
        [[1.03, 0], [2, 0], [2, 1], [1.03, 1], [1.03, 0]]
    ])
    data
    ```

    ```python exec="on" session="examplesettings-tuning"
    import topojson as tp
    from shapely import geometry

    data = geometry.MultiLineString([
        [[0, 0], [0.97, 0], [0.97, 1], [0, 1], [0, 0]], 
        [[1.03, 0], [2, 0], [2, 1], [1.03, 1], [1.03, 0]]
    ])
    data
    ```
    <figure class="parts" data-src="../json/fig_settings_prequantize_input.json" data-label="Two squares with a gap between them"><svg></svg></figure>

    The `prequantize` option is defined as an integer number. It can be best understand as a value that defines the size of a rectangular grid, with the bottom left coordinate at `(0,0)`. Next, the `x`-numbers and `y`-numbers of all coordinates are independency scaled and shifted on this rectangular grid (normalization on range). Here it is shown for the `x`-numbers only:
    ```python
    import numpy as np

    # get the x-numbers of all coordinates
    x = np.array([ls.xy[0] for ls in data.geoms])
    print(f'x:\n{x}')
    ```

    ```python exec="on" session="examplesettings-tuning" result="text"
    import numpy as np

    # get the x-numbers of all coordinates
    x = np.array([ls.xy[0] for ls in data.geoms])
    print(f'x:\n{x}')
    ```
    ```python
    # compute the scaling factor (kx) given the quantize factor (qf)
    qf = 33
    kx = (x.max() - x.min()) / (qf - 1)
    print(f'kx: {kx}')
    ```

    ```python exec="on" session="examplesettings-tuning" result="text"
    # compute the scaling factor (kx) given the quantize factor (qf)
    qf = 33
    kx = (x.max() - x.min()) / (qf - 1)
    print(f'kx: {kx}')
    ```
    ```python
    # shift and apply the scaling factor to map the x-numbers on the integer range
    xnorm = np.round((x - x.min()) / kx).astype(int)
    print(f'x-normalized:\n{xnorm}')
    ```

    ```python exec="on" session="examplesettings-tuning" result="text"
    # shift and apply the scaling factor to map the x-numbers on the integer range
    xnorm = np.round((x - x.min()) / kx).astype(int)
    print(f'x-normalized:\n{xnorm}')
    ```
    ```python
    # denormalize happens as follow
    print(f'x-denormalized:\n{xnorm * kx + x.min()}')
    ```

    ```python exec="on" session="examplesettings-tuning" result="text"
    # denormalize happens as follow
    print(f'x-denormalized:\n{xnorm * kx + x.min()}')
    ```

    The delta-encoding is applied on the normalized coordinates and starting from the first coordinate, only the delta towards the following coordinate is stored. It is a character-reducing process, since the delta between two points is normally smaller than storing both coordinates. Here an example is shown for the `x`-numbers only (1D), where in real it is a 2D process:
    ```python
    # delta encoding of normalized x-numbers
    x_quant = np.insert(np.diff(xnorm), 0, xnorm[:,0], axis=1)
    print(f'x-quantized (normalized-delta-encoded):\n{x_quant}')
    ```

    ```python exec="on" session="examplesettings-tuning" result="text"
    # delta encoding of normalized x-numbers
    x_quant = np.insert(np.diff(xnorm), 0, xnorm[:,0], axis=1)
    print(f'x-quantized (normalized-delta-encoded):\n{x_quant}')
    ```
    ```python
    # dequantization of quantized x-numbers
    x_dequant = x_quant.cumsum(axis=1) * kx + x.min()
    print(f'x-dequantized:\n{x_dequant}')
    ```

    ```python exec="on" session="examplesettings-tuning" result="text"
    # dequantization of quantized x-numbers
    x_dequant = x_quant.cumsum(axis=1) * kx + x.min()
    print(f'x-dequantized:\n{x_dequant}')
    ```

    So, to apply this `prequantize` value on the two no touching polygons, the polygons are touching as a result of it:
    ```python
    topo = tp.Topology(data, prequantize=33)
    topo.to_svg()
    ```

    ```python exec="on" session="examplesettings-tuning"
    topo = tp.Topology(data, prequantize=33)
    topo.to_svg()
    ```
    <figure class="parts" data-src="../json/fig_settings_prequantize_33.json" data-label="The arcs after prequantize=33: the squares share a side"><svg></svg></figure>

    Two polygons of a different size, quantized on the same fixed grid of `0.01`:
    ```python
    grid = {"scale": [0.01, 0.01], "translate": [0, 0]}
    small = tp.Topology(geometry.Polygon([[0, 0], [1, 0], [1, 1], [0, 1]]), prequantize=grid)
    large = tp.Topology(geometry.Polygon([[0, 0], [2, 0], [2, 2], [0, 2]]), prequantize=grid)
    small.to_dict()["arcs"], large.to_dict()["arcs"]
    ```

    ```python exec="on" session="examplesettings-tuning" result="text"
    grid = {"scale": [0.01, 0.01], "translate": [0, 0]}
    small = tp.Topology(geometry.Polygon([[0, 0], [1, 0], [1, 1], [0, 1]]), prequantize=grid)
    large = tp.Topology(geometry.Polygon([[0, 0], [2, 0], [2, 2], [0, 2]]), prequantize=grid)
    _ = small.to_dict()["arcs"], large.to_dict()["arcs"]
    if isinstance(_, dict):
        print(__import__('pprint').pformat(_, sort_dicts=False, width=88))
    else:
        print(_)
    ```
    Both keep the transform `{'scale': [0.01, 0.01], 'translate': [0.0, 0.0]}`; with a
    quantize factor each would get a grid of its own bounding box.


* * * 

## topoquantize

boolean or int

If the topoquantization parameter is specified, the input geometry is quantized 
after the topology is constructed. If the topology is already quantized this 
will be resolved first before the topoquantization is applied. See for more 
details the `prequantize` parameter. Default is `False`.

See [prequantize](settings-tuning.md#prequantize) for an explained example.

**Note:** This is also supported by chaining. Meaning you could first compute the Topology (which can be cost-intensive) and afterwards apply the `topoquantize` on the computed Topology.



!!! example


    ```python
    import topojson as tp
    data = tp.utils.example_data_africa()

    topo = tp.Topology(data)
    topo_tq = topo.topoquantize(75)

    print(f'length with topoquantization:    {len(topo_tq.to_json())}')
    print(f'length without topoquantization: {len(topo.to_json())}')
    ```

    ```python exec="on" session="examplesettings-tuning" result="text"
    import topojson as tp
    data = tp.utils.example_data_africa()

    topo = tp.Topology(data)
    topo_tq = topo.topoquantize(75)

    print(f'length with topoquantization:    {len(topo_tq.to_json())}')
    print(f'length without topoquantization: {len(topo.to_json())}')
    ```



* * * 

## presimplify

boolean, float

Apply presimplify to remove unnecessary points from linestrings before the 
topology is constructed. This will simplify the input geometries. `True` uses a
tolerance of `2`. Default is `False`.

The lines are simplified one by one, so the two sides of a shared border can be
simplified apart. For polygons, `simplify_with="geos"` simplifies them together as
a coverage instead, see [simplify_with](#simplify_with).

!!! example

    Here we load continental Africa as data file and apply the `presimplify` on the input-space.
    The plot shows the borders including linestring simplification, derived _before_ the `Topology` is computed.

    ```python
    import topojson as tp
    data = tp.utils.example_data_africa()

    topo = tp.Topology(data, presimplify=4)

    # since SVG rendering is too small for this example,
    # we use the (optional!) package Altair for visualization.
    topo.to_alt().properties(title='presimplify')
    ```

    ```python exec="on" session="examplesettings-tuning"
    import topojson as tp
    data = tp.utils.example_data_africa()

    topo = tp.Topology(data, presimplify=4)

    # since SVG rendering is too small for this example,
    # we use the (optional!) package Altair for visualization.
    topo.to_alt().properties(title='presimplify')
    ```
    <div id="embed_tuning_presimplify">
</div>

* * * 

## toposimplify

boolean, float 

Apply toposimplify to remove unnecessary points from arcs after the topology 
is constructed. This will simplify the constructed arcs without altering the 
topological relations. Sensible values for coordinates stored in degrees are 
in the range of `0.0001` to `10`. Defaults to `False`.


**Note 1:** The units of `toposimplify` are corresponding to the input space. The provided _sensible_ values are for degrees (eg. `epsg:4326`). When the projection of your data is in `meters` you might need to test which value should be adopted.

**Note 2:** This is also supported by chaining. Meaning you could first compute the Topology (which can be cost-intensive) and afterwards apply the `toposimplify` on the computed Topology.

**Note 3:** With `prevent_oversimplify` (the default), a ring that would be reduced to fewer than three points keeps the vertices to stay a triangle, so small islands do not collapse.

!!! example

    Here we load continental Africa as data file and apply the `toposimplify` on the arcs.
    The plot shows the borders including linestring simplification, derived _after_ the `Topology` is computed.

    ```python
    import topojson as tp
    data = tp.utils.example_data_africa()

    topo = tp.Topology(data, toposimplify=4)

    # since SVG rendering is too small for this example,
    # we use the (optional!) package Altair for visualization.
    topo.to_alt().properties(title='toposimplify')
    ```

    ```python exec="on" session="examplesettings-tuning"
    import topojson as tp
    data = tp.utils.example_data_africa()

    topo = tp.Topology(data, toposimplify=4)

    # since SVG rendering is too small for this example,
    # we use the (optional!) package Altair for visualization.
    topo.to_alt().properties(title='toposimplify')
    ```
    <div id="embed_tuning_toposimplify">
</div>

Instead of a tolerance, `keep` gives the share of the vertices to keep, between `0` and
`1`. Each inner vertex of an arc gets a weight: the largest `epsilon` at which
Douglas-Peucker still keeps it. `keep` keeps the vertices with the largest weights,
and the ends of the arcs always, so the result is the same as with the matching
`epsilon`. As the arcs are shared, shared borders stay matched.

With `simplify_algorithm="vw"`, `keep` searches the tolerance of Visvalingam-Whyatt
(package simplification) that leaves the share asked for. VW is nested, so each step
of the search continues from the result of the step before, and the result is again
that of the matching `epsilon`.

!!! example

    A line of 9 inner vertices (blue) with the weight of each vertex, simplified to a
    quarter and to half of its inner vertices (dashed); the kept vertices are filled.

    ```python
    topo = tp.Topology(data)
    topo.toposimplify(keep=0.1)  # keep 10% of the vertices
    ```

    ```python exec="on" session="examplesettings-tuning"
    topo = tp.Topology(data)
    topo.toposimplify(keep=0.1)  # keep 10% of the vertices
    ```
    <div id="embed_tuning_toposimplify_keep">
</div>


* * * 

## shared_coords

boolean
Sets the strategy to detect junctions. When set to `False` a path is considered
shared when coordinates are the same path (`path-connected`). The path-connected
strategy is more 'correct', but slightly slower. When set to `True` a path is 
considered shared when all coordinates appear in both paths 
(`coords-connected`). Default is `False`.

!!! example

    The example shows two LineStrings, the are partially overlapping with one shared coordinate.

    ```python
    import topojson as tp
    from shapely import geometry

    data = geometry.MultiLineString([
        [(0, 0), (10, 0), (10, 5), (20, 5)], 
        [(5, 0), (20, 0), (20, 5), (10, 5), (0, 5)]
    ])
    data
    ```

    ```python exec="on" session="examplesettings-tuning"
    import topojson as tp
    from shapely import geometry

    data = geometry.MultiLineString([
        [(0, 0), (10, 0), (10, 5), (20, 5)], 
        [(5, 0), (20, 0), (20, 5), (10, 5), (0, 5)]
    ])
    data
    ```
    <figure class="parts" data-src="../json/fig_settings_shared_coords_input.json" data-label="Two lines that partly overlap"><svg></svg></figure>

    The setting `shared_coords=True` adopts a strategy of `coords-connected`, meaning it will split only when coordinates are detected in both linestrings. Here we show it as SVG, with each derived segment/arc plotted separately.

    ```python
    tp.Topology(
        data, 
        shared_coords=True, 
        prequantize=False
    ).to_svg(separate=True)
    ```

    ```python exec="on" session="examplesettings-tuning"
    tp.Topology(
        data, 
        shared_coords=True, 
        prequantize=False
    ).to_svg(separate=True)
    ```
    <figure class="parts" data-src="../json/fig_settings_shared_coords_true.json" data-label="The arcs with shared_coords=True"><svg></svg></figure>
    Arc 2 (20 5, 10 5) is the shared segment. 

    When using the setting `shared_coords=False` a `path-connected` strategy is adopted, meaning it will split also when paths are overlapping without having common coordinates.

    ```python
    tp.Topology(
        data, 
        shared_coords=False, 
        prequantize=False
    ).to_svg(separate=True)
    ```

    ```python exec="on" session="examplesettings-tuning"
    tp.Topology(
        data, 
        shared_coords=False, 
        prequantize=False
    ).to_svg(separate=True)
    ```
    <figure class="parts" data-src="../json/fig_settings_shared_coords_false.json" data-label="The arcs with shared_coords=False"><svg></svg></figure>
    Arcs 2 (5 0, 10 0) and 4 (20 5, 10 5) are shared segments. 


* * * 

## prevent_oversimplify

boolean

If this setting is set to `True`, the simplification is slower, but the 
likelihood of producing valid geometries is higher as it prevents 
oversimplification. Simplification happens on paths separately, so this 
setting is especially relevant for rings with no partial shared paths. This 
is also known as a topology-preserving variant of simplification. 
Default is `True`. 

!!! example

    The example shows a circle that is two times simplified. The first time with `prevent_oversimplify=False`, where the circle collapses to a single point, and the second time with `prevent_oversimplify=True`, where it keeps four points.

    ```python
    import topojson as tp
    from shapely import geometry

    circle = geometry.Point(0, 0).buffer(1)
    circle
    ```

    ```python exec="on" session="examplesettings-tuning"
    import topojson as tp
    from shapely import geometry

    circle = geometry.Point(0, 0).buffer(1)
    circle
    ```
    <figure class="parts" data-src="../json/fig_settings_prevent_oversimplify_input.json" data-label="A circle"><svg></svg></figure>

    ```python
    # force simplification
    tp.Topology(
        circle, 
        toposimplify=2,
        prevent_oversimplify=False
    ).to_svg()
    ```

    ```python exec="on" session="examplesettings-tuning"
    # force simplification
    tp.Topology(
        circle, 
        toposimplify=2,
        prevent_oversimplify=False
    ).to_svg()
    ```

    ```python
    # avoid oversimplification
    tp.Topology(
        circle, 
        toposimplify=2,
        prevent_oversimplify=True
    ).to_svg()
    ```

    ```python exec="on" session="examplesettings-tuning"
    # avoid oversimplification
    tp.Topology(
        circle, 
        toposimplify=2,
        prevent_oversimplify=True
    ).to_svg()
    ```
    <figure class="parts" data-src="../json/fig_settings_prevent_oversimplify.json" data-label="The circle simplified without and with prevent_oversimplify"><svg></svg></figure>



* * * 

## simplify_with

str
Sets the package to use for simplifying (both pre- and toposimplify). Choose 
between `shapely`, `simplification` or `geos`. Shapely adopts solely Douglas-Peucker 
and simplification both Douglas-Peucker and Visvalingam-Whyatt. The package 
simplification is known to be quicker than shapely. 
Default is `shapely`.

`geos` applies to presimplify only. It simplifies the polygons together as a
coverage (`shapely.coverage_simplify`, Visvalingam-Whyatt): a shared border is
simplified once, so the neighbours stay matched, and each ring stays at least a
triangle. Other lines are simplified with shapely. The polygons should form a valid
coverage: no overlaps, and the vertices of shared borders equal
(`shapely.coverage_is_valid`). Toposimplify simplifies arcs, to which this does not
apply.

!!! example


    ```python
    import topojson as tp
    data = tp.utils.example_data_africa()

    topo = tp.Topology(data, prequantize=200)

    # we visualize with the (optional!) package Altair,
    # since SVG rendering is too small for this example
    topo.toposimplify(
        epsilon=1,
        simplify_algorithm='dp', 
        simplify_with='simplification', 
        prevent_oversimplify=False
    ).to_alt().properties(title='Douglas-Peucker (package simplification)')
    ```

    ```python exec="on" session="examplesettings-tuning"
    import topojson as tp
    data = tp.utils.example_data_africa()

    topo = tp.Topology(data, prequantize=200)

    # we visualize with the (optional!) package Altair,
    # since SVG rendering is too small for this example
    topo.toposimplify(
        epsilon=1,
        simplify_algorithm='dp', 
        simplify_with='simplification', 
        prevent_oversimplify=False
    ).to_alt().properties(title='Douglas-Peucker (package simplification)')
    ```
    <div id="embed_tuning_simplify_with"></div>

    With `presimplify`, shapely simplifies each line on its own, so neighbours drift
    apart (the double lines on the left); with `geos` the polygons are simplified as a
    coverage:
    ```python
    presimplified = tp.Topology(data, presimplify=1).to_alt()
    coverage = tp.Topology(data, presimplify=1, simplify_with="geos").to_alt()
    presimplified | coverage
    ```

    ```python exec="on" session="examplesettings-tuning"
    presimplified = tp.Topology(data, presimplify=1).to_alt()
    coverage = tp.Topology(data, presimplify=1, simplify_with="geos").to_alt()
    presimplified | coverage
    ```
    <div id="embed_tuning_simplify_with_geos">
</div>

* * * 

## simplify_algorithm

str

Choose between `dp` and `vw`, for Douglas-Peucker or Visvalingam-Whyatt 
respectively. `vw` will only be selected if `simplify_with` is set to 
`simplification`. Default is `dp`, since it still "produces the most accurate 
generalization" (Shi & Cheung, 2006).

!!! example

    Here we use the `vw` algorithm from Visvalingam-Whyatt included in the package 
    `simplification`.

    ```python
    import topojson as tp
    data = tp.utils.example_data_africa()

    topo = tp.Topology(data, prequantize=200)

    # we visualize with the (optional!) package Altair,
    # since SVG rendering is too small for this example
    topo.toposimplify(
        epsilon=1,
        simplify_algorithm='vw', 
        simplify_with='simplification', 
        prevent_oversimplify=True
    ).to_alt().properties(title='Visvalingam-Whyatt (package simplification)')
    ```

    ```python exec="on" session="examplesettings-tuning"
    import topojson as tp
    data = tp.utils.example_data_africa()

    topo = tp.Topology(data, prequantize=200)

    # we visualize with the (optional!) package Altair,
    # since SVG rendering is too small for this example
    topo.toposimplify(
        epsilon=1,
        simplify_algorithm='vw', 
        simplify_with='simplification', 
        prevent_oversimplify=True
    ).to_alt().properties(title='Visvalingam-Whyatt (package simplification)')
    ```
    <div id="embed_tuning_simplify_alg">
</div>

* * * 

## winding_order

str

Determines the winding order of the features in the output geometry. Choose 
between `CW_CCW` for clockwise orientation for outer rings and counter-
clockwise for interior rings. Or `CCW_CW` for counter-clockwise for outer 
rings and clockwise for interior rings. Default is `CW_CCW`.

!!! example

    Start with creating a `Polygon` geometry

    ```python
    import topojson as tp
    from shapely import geometry

    data = geometry.shape({
        "type": "Polygon",
        "coordinates": [[[0,0],[10,0],[10,10],[0,10],[0,0]]]
    })
    data
    ```

    ```python exec="on" session="examplesettings-tuning"
    import topojson as tp
    from shapely import geometry

    data = geometry.shape({
        "type": "Polygon",
        "coordinates": [[[0,0],[10,0],[10,10],[0,10],[0,0]]]
    })
    data
    ```
    <figure class="parts" data-src="../json/fig_settings_winding_order_input.json" data-label="A square"><svg></svg></figure>

    Continue with defining two Topology objects, one with the outer rings clock wise and the inner rings counter clockwise (`CW_CCW`) and one with the outer rings counter clock wise and the inner rings clock wise (`CCW_CW`).

    ```python
    CW_CCW = tp.Topology(data, winding_order='CW_CCW', prequantize=False)
    CCW_CW = tp.Topology(data, winding_order='CCW_CW', prequantize=False)

    print(CW_CCW)
    print(CCW_CW)
    ```

    ```python exec="on" session="examplesettings-tuning" result="text"
    CW_CCW = tp.Topology(data, winding_order='CW_CCW', prequantize=False)
    CCW_CW = tp.Topology(data, winding_order='CCW_CW', prequantize=False)

    print(CW_CCW)
    print(CCW_CW)
    ```
    As you can see the `arcs` for type `Polygon` are reversed. The effect seems to be negligible, but the effect should be taken into account when using geographic projections, as it defines which part is 'inside' and 'outside' the `Polygon`:

    ```python
    alt_top = CW_CCW.to_alt(projection='equalEarth', color='type:N').properties(title='CW_CCW')
    alt_bottom = CCW_CW.to_alt(projection='equalEarth', color='type:N').properties(title='CCW_CW')

    alt_top & alt_bottom
    ```

    ```python exec="on" session="examplesettings-tuning"
    alt_top = CW_CCW.to_alt(projection='equalEarth', color='type:N').properties(title='CW_CCW')
    alt_bottom = CCW_CW.to_alt(projection='equalEarth', color='type:N').properties(title='CCW_CW')

    alt_top & alt_bottom
    ```
    <div id="embed_tuning_winding_order">
</div>

* * * 

## object_name

str or list of str

Name of the object in the TopoJSON. A list of GeoDataFrames can be given as data,
with a list of names of the same length: each GeoDataFrame then becomes an object
of its own, with the topology computed across all of them.
Default is `data`.

!!! example


    ```python
    import geopandas
    import topojson as tp
    from shapely import geometry

    left = geopandas.GeoDataFrame({"name": ["a"]}, geometry=[geometry.box(0, 0, 1, 1)])
    right = geopandas.GeoDataFrame({"name": ["b"]}, geometry=[geometry.box(1, 0, 2, 1)])

    topo = tp.Topology([left, right], object_name=["left", "right"])
    list(topo.to_dict()["objects"])
    ```

    ```python exec="on" session="examplesettings-tuning" result="text"
    import geopandas
    import topojson as tp
    from shapely import geometry

    left = geopandas.GeoDataFrame({"name": ["a"]}, geometry=[geometry.box(0, 0, 1, 1)])
    right = geopandas.GeoDataFrame({"name": ["b"]}, geometry=[geometry.box(1, 0, 2, 1)])

    topo = tp.Topology([left, right], object_name=["left", "right"])
    _ = list(topo.to_dict()["objects"])
    if isinstance(_, dict):
        print(__import__('pprint').pformat(_, sort_dicts=False, width=88))
    else:
        print(_)
    ```
    The shared border is one arc, used by a feature of each object.


* * * 

## ignore_index

boolean

If `True`, the ids of the features of a GeoJSON FeatureCollection are ignored and
replaced by new ones. Otherwise features keep their id, and a duplicate id raises
an error.
Default is `False`.


<script>
window.addEventListener("DOMContentLoaded", event => {
    var opt = {
        mode: "vega-lite",
        renderer: "svg",
        actions: false
    };

    var spec_presimplify = "../../json/example_presimplify.vl.json";
    vegaEmbed("#embed_tuning_presimplify", spec_presimplify, opt).catch(console.err);

    var spec_toposimplify = "../../json/example_toposimplify.vl.json";
    vegaEmbed("#embed_tuning_toposimplify", spec_toposimplify, opt).catch(console.err);

    var spec_toposimplify_keep = "../../json/example_toposimplify_keep.vl.json";
    vegaEmbed("#embed_tuning_toposimplify_keep", spec_toposimplify_keep, opt).catch(console.err);

    var spec_simplify_with = "../../json/example_simplify_with.vl.json";
    vegaEmbed("#embed_tuning_simplify_with", spec_simplify_with, opt).catch(console.err);   

    var spec_simplify_with_geos = "../../json/example_simplify_with_geos.vl.json";
    vegaEmbed("#embed_tuning_simplify_with_geos", spec_simplify_with_geos, opt).catch(console.err);

    var spec_simplify_alg = "../../json/example_simplify_alg.vl.json";
    vegaEmbed("#embed_tuning_simplify_alg", spec_simplify_alg, opt).catch(console.err);   

    var spec_winding_order = "../../json/example_winding_order.vl.json";
    vegaEmbed("#embed_tuning_winding_order", spec_winding_order, opt).catch(console.err);     
});
</script>
<script type="text/javascript" src="https://cdn.jsdelivr.net/npm/vega@6"></script>
<script type="text/javascript" src="https://cdn.jsdelivr.net/npm/vega-lite@6"></script>
<script type="text/javascript" src="https://cdn.jsdelivr.net/npm/vega-embed@7"></script>
<script src="../js/steps.js" defer></script>
