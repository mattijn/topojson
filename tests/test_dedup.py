import unittest
import topojson
import geopandas
from shapely import geometry
from topojson.core.dedup import Dedup


class TestDedup(unittest.TestCase):
    # duplicate rotated geometry bar with hole interior in geometry foo
    def test_duplicate_rotated_hole_interior(self):
        data = {
            "foo": {
                "type": "MultiPolygon",
                "coordinates": [
                    [
                        [[0, 0], [20, 0], [10, 20], [0, 0]],  # CCW
                        [[3, 2], [10, 16], [17, 2], [3, 2]],  # CW
                    ],
                    [[[6, 4], [14, 4], [10, 12], [6, 4]]],  # CCW
                ],
            },
            "bar": {
                "type": "Polygon",
                "coordinates": [[[17, 2], [3, 2], [10, 16], [17, 2]]],
            },
        }
        topo = Dedup(data).to_dict()
        # print(topo)
        self.assertEqual(len(topo["bookkeeping_duplicates"]), 0)
        self.assertEqual(topo["bookkeeping_geoms"], [[0, 1], [2], [3]])

    def test_two_polygon_reversed_shared_arc(self):
        data = {
            "abcda": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
            },  # rotated to BCDAB, cut BC-CDAB
            "befcb": {
                "type": "Polygon",
                "coordinates": [[[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]],
            },
        }
        topo = Dedup(data).to_dict()
        self.assertEqual(len(topo["bookkeeping_duplicates"]), 0)
        self.assertEqual(topo["bookkeeping_shared_arcs"], [2])
        self.assertEqual(topo["bookkeeping_arcs"], [[2, 0], [1, 2]])

    def test_duplicate_polygon_no_junctions(self):
        data = {
            "abca": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [1, 0], [0, 1], [0, 0]]],
            },
            "acba": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [0, 1], [1, 0], [0, 0]]],
            },
        }
        topo = Dedup(data).to_dict()
        self.assertEqual(len(topo["bookkeeping_duplicates"]), 0)
        self.assertEqual(topo["bookkeeping_shared_arcs"], [0])
        self.assertEqual(topo["bookkeeping_arcs"], [[0], [0]])
        self.assertEqual(topo["bookkeeping_geoms"], [[0], [1]])

    def test_shared_line_ABCDBE_and_FBCG(self):
        data = {
            "abcdbe": {
                "type": "LineString",
                "coordinates": [[0, 0], [1, 0], [2, 0], [3, 0], [1, 0], [4, 0]],
            },
            "fbcg": {
                "type": "LineString",
                "coordinates": [[0, 1], [1, 0], [2, 0], [3, 1]],
            },
        }
        topo = Dedup(data).to_dict()
        self.assertEqual(len(topo["bookkeeping_duplicates"]), 0)
        self.assertEqual(topo["bookkeeping_shared_arcs"], [4])
        self.assertEqual(topo["bookkeeping_arcs"], [[0, 4, 1, 2], [3, 4, 5]])

    # this test was added since the shared_arcs bookkeeping is not doing well. Next runs
    # can affect previous runs where dup_pair_list should update properly.
    def test_shared_junctions_in_shared_paths(self):
        data = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
        data = data[
            (data.name == "Togo")
            | (data.name == "Benin")
            | (data.name == "Burkina Faso")
        ]
        topo = Dedup(data).to_dict()
        self.assertEqual(len(topo["bookkeeping_shared_arcs"]), 3)
        self.assertEqual(len(topo["bookkeeping_duplicates"]), 0)

    # this test was added since the shared_arcs bookkeeping is doing well, but the
    # wrong arc gots deleted. How come?
    # the problem arose in wrongly linemerging of contigiuous line-elements
    # merged linestring is not always placed upfront.
    def test_arc_not_shared_arcs_got_deleted(self):
        data = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
        data = data[
            (data.name == "Botswana")
            | (data.name == "South Africa")
            | (data.name == "Zimbabwe")
            | (data.name == "Mozambique")
            | (data.name == "Zambia")
        ]
        topo = Dedup(data).to_dict()
        self.assertEqual(len(topo["bookkeeping_shared_arcs"]), 9)
        self.assertEqual(len(topo["bookkeeping_duplicates"]), 0)

    # this test was added since there is no test for non-intersecting geometries.
    # as was raised in https://github.com/mattijn/topojson/issues/1
    def test_no_shared_paths_in_geoms(self):
        data = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
        data = data[(data.name == "Togo") | (data.name == "Liberia")]
        topo = Dedup(data).to_dict()
        self.assertEqual(len(topo["bookkeeping_shared_arcs"]), 0)
        self.assertEqual(len(topo["bookkeeping_duplicates"]), 0)

    # this test was added since the local variable "array_bk_sarcs" was
    # referenced before assignment. As was raised in:
    # https://github.com/mattijn/topojson/issues/3
    def test_array_bk_sarcs_reference(self):
        data = {
            "foo": {"type": "LineString", "coordinates": [[4, 0], [2, 2], [0, 0]]},
            "bar": {
                "type": "LineString",
                "coordinates": [[0, 2], [1, 1], [2, 2], [3, 1], [4, 2]],
            },
        }
        topo = Dedup(data).to_dict()
        self.assertEqual(len(topo["bookkeeping_shared_arcs"]), 1)
        self.assertEqual(len(topo["junctions"]), 4)

    def test_super_function_dedup(self):
        data = geometry.GeometryCollection(
            [
                geometry.Polygon([[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]),
                geometry.Polygon([[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]),
            ]
        )
        topo = Dedup(data).to_dict()
        self.assertEqual(
            list(topo.keys()),
            [
                "type",
                "linestrings",
                "bookkeeping_geoms",
                "objects",
                "options",
                "bbox",
                "junctions",
                "bookkeeping_duplicates",
                "bookkeeping_arcs",
                "bookkeeping_shared_arcs",
            ],
        )
