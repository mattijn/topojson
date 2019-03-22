import unittest
import topojson
import geopandas


class TestCut(unittest.TestCase):
    # cut exact duplicate lines ABC & ABC have no cuts
    def test_exact_duplicate_lines_ABC_ABC_no_cuts(self):
        data = {
            "abc": {"type": "LineString", "coordinates": [[0, 0], [1, 0], [2, 0]]},
            "abc2": {"type": "LineString", "coordinates": [[0, 0], [1, 0], [2, 0]]},
        }
        topo = topojson.cut(topojson.join(topojson.extract(data)))
        # print(topo)
        self.assertEqual(len(topo["junctions"]), 0)
        self.assertSequenceEqual(topo["bookkeeping_duplicates"].tolist(), [[1, 0]])

    # cut reversed duplicate lines ABC & CBA have no cuts
    def test_reversed_duplicate_lines_ABC_CBA_no_cuts(self):
        data = {
            "abc": {"type": "LineString", "coordinates": [[0, 0], [1, 0], [2, 0]]},
            "cba": {"type": "LineString", "coordinates": [[2, 0], [1, 0], [0, 0]]},
        }
        topo = topojson.cut(topojson.join(topojson.extract(data)))
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
        topo = topojson.cut(topojson.join(topojson.extract(data)))
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
        topo = topojson.cut(topojson.join(topojson.extract(data)))
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
        topo = topojson.cut(topojson.join(topojson.extract(data)))
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
        topo = topojson.cut(topojson.join(topojson.extract(data)))
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
        topo = topojson.cut(topojson.join(topojson.extract(data)))
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
        topo = topojson.cut(topojson.join(topojson.extract(data)))
        # print(topo)
        self.assertEqual(len(topo["junctions"]), 0)
        self.assertSequenceEqual(topo["bookkeeping_duplicates"].tolist(), [[1, 0]])

    # TODO: Continue from
    # https://github.com/topojson/topojson-server/blob/master/test/cut-test.js#L103

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
        topo = topojson.cut(topojson.join(topojson.extract(data)))
        # print(topo)
        self.assertEqual(topo["bookkeeping_linestrings"].size, 6)
        self.assertSequenceEqual(topo["bookkeeping_duplicates"].tolist(), [[4, 1]])

    # currently the border between Sudan and Eqypt is not recognized as duplicate
    # because of floating-precision. Should be solved by a 'snap_to_grid' option.
    def test_to_cut_border_egypt_sudan(self):
        data = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
        data = data[(data.name == "Egypt") | (data.name == "Sudan")]
        topo = topojson.cut(topojson.join(topojson.extract(data)))
        self.assertEqual(len(topo["bookkeeping_duplicates"].tolist()), 0)

    def test_nybb_fast_split(self):
        nybb_path = geopandas.datasets.get_path("nybb")
        data = geopandas.read_file(nybb_path)
        data.set_index("BoroCode", inplace=True)

        topo = topojson.cut(topojson.join(topojson.extract(data)))
        self.assertEqual(topo["bookkeeping_linestrings"].size, 5618)
