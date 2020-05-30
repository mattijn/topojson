import topojson
import os
import json
import pytest

def test_to_json(tmp_path):
    topo_file = os.path.join(tmp_path, "topo.json")
    data = [
        {"type": "LineString", "coordinates": [[4, 0], [2, 2], [0, 0]]},
        {"type": "LineString", "coordinates": [[0, 2], [1, 1], [2, 2], [3, 1], [4, 2]]},
    ]
    topo = topojson.Topology(data)
    topo.to_json(topo_file)

    with open(topo_file) as f:
        topo_reloaded = json.load(f)


