import unittest
import topojson


class TestHasmap(unittest.TestCase):
    # duplicate rotated geometry bar with hole interior in geometry foo
    def test_hashmap_geomcol_multipolygon_polygon(self):
        data = {
            "foo": {
                "type": "GeometryCollection",
                "geometries": [
                    {
                        "type": "MultiPolygon",
                        "coordinates": [
                            [
                                [[10, 20], [20, 0], [0, 0], [10, 20]],
                                [[3, 2], [10, 16], [17, 2], [3, 2]],
                            ],
                            [[[6, 4], [14, 4], [10, 12], [6, 4]]],
                        ],
                    },
                    {
                        "type": "Polygon",
                        "coordinates": [[[20, 0], [35, 5], [10, 20], [20, 0]]],
                    },
                ],
            }
        }
        topo = topojson.hashmap(
            topojson.dedup(topojson.cut(topojson.join(topojson.extract(data))))
        )
        # print(topo)
        self.assertEqual(topo["objects"]["foo"]["geometries"][0]["arcs"][0], [4, 0])

    def test_hashmap_backward_polygon(self):
        data = {
            "abc": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
            },
            "def": {
                "type": "Polygon",
                "coordinates": [[[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]],
            },
        }
        topo = topojson.hashmap(
            topojson.dedup(topojson.cut(topojson.join(topojson.extract(data))))
        )
        self.assertEqual(topo["objects"]["abc"]["arcs"], [[-3, 0]])
        self.assertEqual(topo["objects"]["def"]["arcs"], [[1, 2]])
