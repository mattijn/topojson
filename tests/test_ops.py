import numpy as np
import topojson.ops


def test_ops_remove_colinear_points():

    test = np.array([[0, 0], [0, 1], [0, 2]])
    result = topojson.ops.remove_collinear_points(test)
    assert result.tolist() == [[0, 0], [0, 2]]

    test = np.array([[0, 0], [1, 1], [0, 2]])
    result = topojson.ops.remove_collinear_points(test)
    assert result.tolist() == test.tolist()
