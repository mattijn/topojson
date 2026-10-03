import numpy as np
import pytest
from shapely import geometry

import topojson.ops
import topojson.utils
from topojson.core.extract import Extract


def test_ops_remove_colinear_points():

    test = np.array([[0, 0], [0, 1], [0, 2]])
    result = topojson.ops.remove_collinear_points(test)
    assert result.tolist() == [[0, 0], [0, 2]]

    test = np.array([[0, 0], [1, 1], [0, 2]])
    result = topojson.ops.remove_collinear_points(test)
    assert result.tolist() == test.tolist()



def test_ops_remove_spikes():
    # ring that turns back at (0, 0)
    ring = np.array([[3, 0], [0, 0], [2, 0], [2, 2], [3, 2], [3, 0]])
    result = topojson.ops.remove_spikes(ring)
    assert result.tolist() == [[3, 0], [2, 0], [2, 2], [3, 2], [3, 0]]

    # ring with the spike at the closing vertex
    ring = np.array([[0, 0], [2, 0], [2, 2], [1, 0], [0, 0]])
    result = topojson.ops.remove_spikes(ring)
    assert result.tolist() == [[2, 0], [2, 2], [1, 0], [2, 0]]

    # open line: end points are kept
    line = np.array([[0, 0], [5, 0], [3, 0], [3, 3]])
    result = topojson.ops.remove_spikes(line)
    assert result.tolist() == [[0, 0], [3, 0], [3, 3]]

    # a line that would collapse is returned unchanged
    line = np.array([[0, 0], [5, 0], [0, 0]])
    assert topojson.ops.remove_spikes(line).tolist() == line.tolist()


def pairwise_shared_path_ends(lines):
    pairs = [
        (a, b)
        for i, a in enumerate(lines)
        for b in lines[i + 1 :]
        if a.envelope.intersects(b.envelope)
    ]
    return topojson.ops.shared_path_ends(pairs)


@pytest.mark.parametrize(
    "lines",
    [
        # equal lines share no path, also with an extra vertex or reversed
        [[(0, 0), (10, 0)], [(0, 0), (5, 0), (10, 0)]],
        [[(0, 0), (10, 0)], [(10, 0), (0, 0)], [(5, 0), (10, 0), (10, 5)]],
        # vertices of one line inside a segment of the other
        [
            [(0, 0), (4, 0), (4, 4), (0, 4), (0, 0)],
            [(4, 1), (8, 1), (8, 3), (4, 3), (4, 1)],
        ],
        [[(0, 0), (6, 0)], [(3, 0), (9, 0)]],
        [[(0, 0), (6, 6)], [(2, 2), (4, 4), (4, 8)]],
        # collinear without overlap, crossing, and the end of a line on a path
        [[(0, 0), (2, 0)], [(3, 0), (5, 0)]],
        [[(0, 0), (4, 4)], [(0, 4), (4, 0)]],
        [[(0, 0), (10, 0)], [(2, 0), (6, 0), (6, 6)]],
        # a closed line continues into its start, also when it is not a ring
        [[(0, 0), (4, 0), (4, 4), (0, 0)], [(4, 0), (4, 4), (0, 0), (4, 0)]],
        [[(0, 0), (4, 0), (4, 4), (0, 0)], [(0, 0), (4, 0)]],
        # a line that passes a vertex twice, and a ring that lies on it
        [
            [(0, 0), (2, 0), (2, 2), (0, 2), (0, 0)],
            [(-2, -2), (2, -2), (2, 0), (0, 0), (0, 2), (2, 2), (2, 0), (4, 0)],
        ],
    ],
)
def test_ops_shared_path_ends_on_grid_cases(lines):
    lines = [geometry.LineString(line) for line in lines]
    expected = pairwise_shared_path_ends(lines)
    assert topojson.ops.shared_path_ends_on_grid(lines) == expected


@pytest.mark.parametrize("quant_factor", [50, 75, 100, 1e5])
def test_ops_shared_path_ends_on_grid_equals_pairwise(quant_factor):
    # coarse grids give rings that touch themselves and lie on each other
    data = topojson.utils.example_data_africa()
    extracted = Extract(data).output
    linestrings = extracted["linestrings"]
    bbox = topojson.ops.bounds(linestrings)
    lines, _ = topojson.ops.quantize(linestrings, bbox, quant_factor)
    expected = pairwise_shared_path_ends(lines)
    assert topojson.ops.shared_path_ends_on_grid(lines) == expected


@pytest.mark.parametrize("quant_factor", [50, 100, 1e5])
def test_ops_cut_lines_on_grid_equals_cut_line(quant_factor):
    data = topojson.utils.example_data_africa()
    extracted = Extract(data).output
    linestrings = extracted["linestrings"]
    bbox = topojson.ops.bounds(linestrings)
    lines, _ = topojson.ops.quantize(linestrings, bbox, quant_factor)
    ends = sorted(topojson.ops.shared_path_ends_on_grid(lines))
    junctions = [geometry.Point(p) for p in ends]
    # a line through a junction that is not one of its vertices
    (x, y) = ends[0]
    lines.append(geometry.LineString([(x - 1, y - 1), (x + 1, y + 1)]))
    is_ring = np.array([line.is_closed for line in lines])

    parts, n_parts = topojson.ops.cut_lines_on_grid(lines, junctions, is_ring)
    tree = topojson.ops.STRtree(junctions)
    expected = [
        topojson.ops.cut_line(line, tree, ring) for line, ring in zip(lines, is_ring)
    ]
    assert n_parts.tolist() == [len(p) for p in expected]
    assert [p.tolist() for p in parts] == [p.tolist() for e in expected for p in e]
