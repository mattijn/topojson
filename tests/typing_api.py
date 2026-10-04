"""
The types of the public API as a user sees them, checked by mypy in CI (not run by
pytest). A `# type: ignore` marks a call that must be an error: with
`warn_unused_ignores`, mypy fails when such a call is accepted.
"""

from typing import Any, assert_type

from shapely.geometry import box

import topojson as tp

topo = tp.Topology([box(0, 0, 1, 1), box(1, 0, 2, 1)], prequantize=1e4)

assert_type(topo.toposimplify(1), tp.Topology)
assert_type(topo.toposimplify(keep=0.1, simplify_algorithm="vw"), tp.Topology)
assert_type(topo.toposimplify(1, inplace=True), None)
assert_type(topo.topoquantize(1e3), tp.Topology)
assert_type(topo.topoquantize({"scale": [1, 1], "translate": [0, 0]}), tp.Topology)
assert_type(topo.topoquantize(1e3, inplace=True), None)
assert_type(topo.to_dict(), dict[str, Any])
assert_type(topo.to_json(), str | None)
assert_type(topo.to_geojson(), str | None)
assert_type(topo.remove([0]).add([box(2, 0, 3, 1)]), tp.Topology)
assert_type(tp.Topology.read_json("topology.json"), tp.Topology)
assert_type(topo.__geo_interface__, dict[str, Any])

tp.Topology([box(0, 0, 1, 1)], simplify_algorithm="rdp")  # type: ignore[arg-type]
tp.Topology([box(0, 0, 1, 1)], winding_order="CW")  # type: ignore[arg-type]
topo.toposimplify(1, simplify_with="mapshaper")  # type: ignore[call-overload]
topo.to_json(indent="4")  # type: ignore[arg-type]
