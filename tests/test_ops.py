import numpy as np
import topojson.ops


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
