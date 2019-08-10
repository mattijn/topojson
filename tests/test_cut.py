import unittest
import topojson
import geopandas
from shapely import geometry
from topojson.core.cut import Cut


class TestCut(unittest.TestCase):
    # cut exact duplicate lines ABC & ABC have no cuts
    def test_exact_duplicate_lines_ABC_ABC_no_cuts(self):
        data = {
            "abc": {"type": "LineString", "coordinates": [[0, 0], [1, 0], [2, 0]]},
            "abc2": {"type": "LineString", "coordinates": [[0, 0], [1, 0], [2, 0]]},
        }
        topo = Cut(data).to_dict()
        # print(topo)
        self.assertEqual(len(topo["junctions"]), 0)
        self.assertSequenceEqual(topo["bookkeeping_duplicates"].tolist(), [[1, 0]])

    # cut reversed duplicate lines ABC & CBA have no cuts
    def test_reversed_duplicate_lines_ABC_CBA_no_cuts(self):
        data = {
            "abc": {"type": "LineString", "coordinates": [[0, 0], [1, 0], [2, 0]]},
            "cba": {"type": "LineString", "coordinates": [[2, 0], [1, 0], [0, 0]]},
        }
        topo = Cut(data).to_dict()
        # print(topo)
        self.assertEqual(len(topo["junctions"]), 0)
        self.assertSequenceEqual(topo["bookkeeping_duplicates"].tolist(), [[1, 0]])

    # cut exact duplicate rings ABCA & ABCA have no cuts
    def test_exact_duplicate_rings_ABCA_ABCA_no_cuts(self):
        data = {
            "abca": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [1, 0], [2, 1], [0, 0]]],
            },
            "abca2": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [1, 0], [2, 1], [0, 0]]],
            },
        }
        topo = Cut(data).to_dict()
        # print(topo)
        self.assertEqual(len(topo["junctions"]), 0)
        self.assertSequenceEqual(topo["bookkeeping_duplicates"].tolist(), [[1, 0]])

    # cut reversed rings ABCA & ACBA have no cuts
    def test_reversed_rings_ABCA_ACBA_no_cuts(self):
        data = {
            "abca": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [1, 0], [2, 1], [0, 0]]],
            },
            "acba": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [2, 1], [1, 0], [0, 0]]],
            },
        }
        topo = Cut(data).to_dict()
        # print(topo)
        self.assertEqual(len(topo["junctions"]), 0)
        self.assertSequenceEqual(topo["bookkeeping_duplicates"].tolist(), [[1, 0]])

    # cut rotated duplicate rings BCAB & ABCA have no cuts
    def test_rotated_duplicates_rings_BCAB_ABCA_no_cuts(self):
        data = {
            "abca": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [1, 0], [2, 1], [0, 0]]],
            },
            "bcab": {
                "type": "Polygon",
                "coordinates": [[[1, 0], [2, 1], [0, 0], [1, 0]]],
            },
        }
        topo = Cut(data).to_dict()
        # print(topo)
        self.assertEqual(len(topo["junctions"]), 0)
        self.assertSequenceEqual(topo["bookkeeping_duplicates"].tolist(), [[1, 0]])

    # cut ring ABCA & line ABCA have no cuts
    def test_ring_ABCA_line_ABCA_no_cuts(self):
        data = {
            "abcaLine": {
                "type": "Linestring",
                "coordinates": [[0, 0], [1, 0], [2, 1], [0, 0]],
            },
            "abcaPolygon": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [1, 0], [2, 1], [0, 0]]],
            },
        }
        topo = Cut(data).to_dict()
        # print(topo)
        self.assertEqual(len(topo["junctions"]), 0)
        self.assertSequenceEqual(topo["bookkeeping_duplicates"].tolist(), [[1, 0]])

    # cut ring BCAB & line ABCA have no cuts
    def test_ring_BCAB_line_ABCA_no_cuts(self):
        data = {
            "abcaLine": {
                "type": "Linestring",
                "coordinates": [[0, 0], [1, 0], [2, 1], [0, 0]],
            },
            "bcabPolygon": {
                "type": "Polygon",
                "coordinates": [[[1, 0], [2, 1], [0, 0], [1, 0]]],
            },
        }
        topo = Cut(data).to_dict()
        # print(topo)
        self.assertEqual(len(topo["junctions"]), 0)
        self.assertSequenceEqual(topo["bookkeeping_duplicates"].tolist(), [[1, 0]])

    # cut ring ABCA & line BCAB have no cuts
    def test_ring_ABCA_line_BCAB_no_cuts(self):
        data = {
            "bcabLine": {
                "type": "Linestring",
                "coordinates": [[1, 0], [2, 1], [0, 0], [1, 0]],
            },
            "abcaPolygon": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [1, 0], [2, 1], [0, 0]]],
            },
        }
        topo = Cut(data).to_dict()
        # print(topo)
        self.assertEqual(len(topo["junctions"]), 0)
        self.assertSequenceEqual(topo["bookkeeping_duplicates"].tolist(), [[1, 0]])

    # overlapping rings ABCDA and BEFCB are cut into BC-CDAB and BEFC-CB
    def test_overlapping_rings_are_cut(self):
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
        topo = Cut(data).to_dict()
        # print(topo)
        self.assertEqual(topo["bookkeeping_linestrings"].size, 6)
        self.assertSequenceEqual(topo["bookkeeping_duplicates"].tolist(), [[4, 1]])

    # currently the border between Sudan and Eqypt is not recognized as duplicate
    # because of floating-precision. Should be solved by a "snap_to_grid" option.
    def test_to_cut_border_egypt_sudan(self):
        data = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
        data = data[(data.name == "Egypt") | (data.name == "Sudan")]
        topo = Cut(data).to_dict()
        self.assertEqual(len(topo["bookkeeping_duplicates"].tolist()), 1)

    def test_nybb_fast_split(self):
        nybb_path = geopandas.datasets.get_path("nybb")
        data = geopandas.read_file(nybb_path)
        data.set_index("BoroCode", inplace=True)

        topo = Cut(data).to_dict()
        self.assertEqual(topo["bookkeeping_linestrings"].size, 5618)

    # this test was added since the fast_split was really slow on geometries
    # when there are many junctions in the geometry. During debugging this test ran
    # eventually 8x more quick.
    def test_many_junctions(self):
        data = geopandas.read_file(
            "tests/files_geojson/mesh2d.geojson", driver="GeoJSON"
        )
        # previous test ran in 8.798s (best of 3)
        # current test ran in 8.182s (best of 3)
        topo = Cut(data).to_dict()
        self.assertEqual(topo["bookkeeping_linestrings"].size, 11010)

    def test_super_function_cut(self):
        data = geometry.GeometryCollection(
            [
                geometry.Polygon([[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]),
                geometry.Polygon([[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]),
            ]
        )
        topo = Cut(data).to_dict()
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
                "bookkeeping_linestrings",
            ],
        )

    # this geometry is added on several classes (extract and hashmap). Not yet clear in
    # which phase it is going wrong
    def test_cut_geomcol_multipolygon_polygon(self):
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
        topo = Cut(data).to_dict()
        # print(topo)
        self.assertEqual(topo["bookkeeping_linestrings"].size, 8)

