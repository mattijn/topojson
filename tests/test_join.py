from shapely import geometry
import unittest
import topojson
import geopandas


class TestJoin(unittest.TestCase):
    # the returned hashmap has true for junction points
    def test_true_for_junction_points(self):
        data = {
            "cba": {"type": "LineString", "coordinates": [[2, 0], [1, 0], [0, 0]]},
            "ab": {"type": "LineString", "coordinates": [[0, 0], [1, 0]]},
        }
        topo = topojson.join(topojson.extract(data))
        self.assertTrue(geometry.MultiPoint([
            (0.0, 0.0),(1.0, 0.0),(2.0, 0.0)
            ]).equals(geometry.MultiPoint(topo["junctions"])))

    # the returned hashmap has undefined for non-junction points
    def test_undefined_for_non_junction_points(self):
        data = {
            "cba": {"type": "LineString", "coordinates": [[2, 0], [1, 0], [0, 0]]},
            "ab": {"type": "LineString", "coordinates": [[0, 0], [2, 0]]},
        }
        topo = topojson.join(topojson.extract(data))
        # print(topo)
        self.assertFalse(
            geometry.Point(1.0, 0.0) in geometry.MultiPoint(topo["junctions"])
        )

        # forward backward lines

    def test_forward_backward_lines(self):
        data = {
            "foo": {
                "type": "LineString",
                "coordinates": [(0, 0), (10, 0), (10, 5), (20, 5)],
            },
            "bar": {
                "type": "LineString",
                "coordinates": [(5, 0), (30, 0), (30, 5), (0, 5)],
            },
        }
        topo = topojson.join(topojson.extract(data))
        # print(topo)
        self.assertTrue(len(topo["junctions"]), 4)

    # more than two lines
    def test_more_than_two_lines(self):
        data = {
            "foo": {"type": "LineString", "coordinates": [(0, 0), (15, 2.5), (30, 5)]},
            "bar": {"type": "LineString", "coordinates": [(0, 0), (15, 2.5), (30, 5)]},
            "baz": {
                "type": "LineString",
                "coordinates": [(0, 0), (10, 0), (10, 5), (20, 5)],
            },
            "qux": {
                "type": "LineString",
                "coordinates": [(5, 0), (30, 0), (30, 5), (0, 5)],
            },
        }
        topo = topojson.join(topojson.extract(data))
        # print(topo)
        self.assertTrue(len(topo["junctions"]), 6)

    # exact duplicate lines ABC & ABC have no junctions
    def test_duplicate_lines_junction_endpoints(self):
        data = {
            "abc1": {"type": "LineString", "coordinates": [[0, 0], [1, 0], [2, 0]]},
            "abc2": {"type": "LineString", "coordinates": [[0, 0], [1, 0], [2, 0]]},
        }
        topo = topojson.join(topojson.extract(data))
        # print(topo)
        self.assertListEqual(topo["junctions"], [])

    # reversed duplicate lines ABC & CBA have no junctions
    def test_reversed_duplicate_lines_junction_endpoints(self):
        data = {
            "abc": {"type": "LineString", "coordinates": [[0, 0], [1, 0], [2, 0]]},
            "cba": {"type": "LineString", "coordinates": [[2, 0], [1, 0], [0, 0]]},
        }
        topo = topojson.join(topojson.extract(data))
        # print(topo)
        self.assertListEqual(topo["junctions"], [])

    # exact duplicate rings ABCA & ABCA have no junctions
    def test_exact_duplicate_rings(self):
        data = {
            "abca1": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [1, 1], [2, 0], [0, 0]]],
            },
            "abca2": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [1, 1], [2, 0], [0, 0]]],
            },
        }
        topo = topojson.join(topojson.extract(data))
        # print(topo)
        self.assertListEqual(topo["junctions"], [])

    # reversed duplicate rings ABCA & ACBA have no junctions
    def test_reversed_duplicate_rings(self):
        data = {
            "abca": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [1, 1], [2, 0], [0, 0]]],
            },
            "acba": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [2, 0], [1, 1], [0, 0]]],
            },
        }
        topo = topojson.join(topojson.extract(data))
        self.assertListEqual(topo["junctions"], [])

    # rotated duplicate rings BCAB & ABCA have no junctions
    def test_rotated_duplicate_rings(self):
        data = {
            "abca": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [1, 1], [2, 0], [0, 0]]],
            },
            "bcab": {
                "type": "Polygon",
                "coordinates": [[[1, 1], [2, 0], [0, 0], [1, 1]]],
            },
        }
        topo = topojson.join(topojson.extract(data))
        self.assertListEqual(topo["junctions"], [])

    # ring ABCA & line ABCA have no junction at A
    def test_equal_ring_and_line_no_junctions(self):
        data = {
            "abcaLine": {
                "type": "LineString",
                "coordinates": [[0, 0], [1, 1], [2, 0], [0, 0]],
            },
            "abcaPolygon": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [1, 1], [2, 0], [0, 0]]],
            },
        }
        topo = topojson.join(topojson.extract(data))
        self.assertListEqual(topo["junctions"], [])

    # ring ABCA & line ABCA have no junctions
    def test_rotated_ring_and_line_no_junctions(self):
        data = {
            "abcaLine": {
                "type": "LineString",
                "coordinates": [[0, 0], [1, 1], [2, 0], [0, 0]],
            },
            "bcabPolygon": {
                "type": "Polygon",
                "coordinates": [[[1, 1], [2, 0], [0, 0], [1, 1]]],
            },
        }
        topo = topojson.join(topojson.extract(data))
        self.assertListEqual(topo["junctions"], [])

    # when an old arc ABC extends a new arc AB, there is a junction at B
    def test_line_ABC_extends_new_line_AB(self):
        data = {
            "abc": {"type": "LineString", "coordinates": [[0, 0], [1, 0], [2, 0]]},
            "ab": {"type": "LineString", "coordinates": [[0, 0], [1, 0]]},
        }
        topo = topojson.join(topojson.extract(data))
        self.assertTrue(
            geometry.MultiPoint(topo["junctions"]).equals(
                geometry.MultiPoint([(0.0, 0.0), (1.0, 0.0)])
            )
        )

    # when a reversed old arc CBA extends a new arc AB, there is a junction at B
    def test_reversed_line_CBA_extends_new_line_AB(self):
        data = {
            "cba": {"type": "LineString", "coordinates": [[2, 0], [1, 0], [0, 0]]},
            "ab": {"type": "LineString", "coordinates": [[0, 0], [1, 0]]},
        }
        topo = topojson.join(topojson.extract(data))
        self.assertTrue(
            geometry.Point(1.0, 0.0).within(geometry.MultiPoint(topo["junctions"]))
        )

    # when a new arc ADE shares its start with an old arc ABC, there is no junction at A
    def test_line_ADE_share_starts_with_ABC(self):
        data = {
            "ade": {"type": "LineString", "coordinates": [[0, 0], [1, 0], [2, 0]]},
            "abc": {"type": "LineString", "coordinates": [[0, 0], [1, 1], [2, 1]]},
        }
        topo = topojson.join(topojson.extract(data))
        self.assertListEqual(topo["junctions"], [])

    # ring ABA has no junctions
    def test_single_ring_ABCA(self):
        data = {
            "abca": {
                "type": "LineString",
                "coordinates": [[0, 0], [1, 0], [1, 1], [0, 0]],
            }
        }
        topo = topojson.join(topojson.extract(data))
        self.assertListEqual(topo["junctions"], [])

    # ring AA is not a proper polygon geometry.
    def test_single_ring_AA(self):
        data = {"aa": {"type": "Polygon", "coordinates": [[0, 0], [0, 0]]}}
        topo = topojson.join(topojson.extract(data))
        self.assertListEqual(topo["junctions"], [])

    # when a new line DEC shares its end with an old line ABC, there is no junction at C
    def test_line_DEC_share_line_ABC(self):
        data = {
            "abc": {"type": "LineString", "coordinates": [[0, 0], [1, 0], [2, 0]]},
            "dec": {"type": "LineString", "coordinates": [[0, 1], [1, 1], [2, 0]]},
        }
        topo = topojson.join(topojson.extract(data))
        self.assertListEqual(topo["junctions"], [])

    # when a new line ABC extends an old line AB, there is a junction at B
    def test_line_ABC_extends_line_AB(self):
        data = {
            "ab": {"type": "LineString", "coordinates": [[0, 0], [1, 0]]},
            "abc": {"type": "LineString", "coordinates": [[0, 0], [1, 0], [2, 0]]},
        }
        topo = topojson.join(topojson.extract(data))
        self.assertTrue(
            geometry.MultiPoint(topo["junctions"]).equals(
            geometry.MultiPoint([(0.0, 0.0), (1.0, 0.0)])),
        )

    # when a new line ABC extends a reversed old line BA, there is a junction at B
    def test_line_ABC_extends_line_BA(self):
        data = {
            "ba": {"type": "LineString", "coordinates": [[1, 0], [0, 0]]},
            "abc": {"type": "LineString", "coordinates": [[0, 0], [1, 0], [2, 0]]},
        }
        topo = topojson.join(topojson.extract(data))
        self.assertTrue(
            geometry.MultiPoint(topo["junctions"]).equals(
            geometry.MultiPoint([(1.0, 0.0), (0.0, 0.0)])))

    # when a new line starts BC in the middle of an old line ABC, there is a 
    # junction at B
    def test_line_ABC_extends_line_BC(self):
        data = {
            "abc": {"type": "LineString", "coordinates": [[0, 0], [1, 0], [2, 0]]},
            "bc": {"type": "LineString", "coordinates": [[1, 0], [2, 0]]},
        }
        topo = topojson.join(topojson.extract(data))
        self.assertTrue(
            geometry.MultiPoint(topo["junctions"]).equals(
                geometry.MultiPoint([(1.0, 0.0), (0.0, 0.0), (2.0, 0.0)])
            )
        )

    # when a new line BC starts in the middle of a reversed old line CBA, there is a 
    # junction at B
    def test_line_BC_start_middle_reversed_line_CBA(self):
        data = {
            "cba": {"type": "LineString", "coordinates": [[2, 0], [1, 0], [0, 0]]},
            "bc": {"type": "LineString", "coordinates": [[1, 0], [2, 0]]},
        }
        topo = topojson.join(topojson.extract(data))
        self.assertTrue(
            geometry.MultiPoint(topo["junctions"]).equals(
                geometry.MultiPoint([(2.0, 0.0), (1.0, 0.0)])
            )
        )

    # when a new line ABD deviates from an old line ABC, there is a junction at B
    def test_line_ABD_deviates_line_ABC(self):
        data = {
            "abc": {"type": "LineString", "coordinates": [[0, 0], [1, 0], [2, 0]]},
            "abd": {"type": "LineString", "coordinates": [[0, 0], [1, 0], [3, 0]]},
        }
        topo = topojson.join(topojson.extract(data))
        self.assertTrue(
            geometry.MultiPoint(topo["junctions"]).equals(
                geometry.MultiPoint([(0.0, 0.0), (2.0, 0.0)])
            )
        )

    # when a new line ABD deviates from a reversed old line CBA, there is a 
    # junction at B
    def test_line_ABD_deviates_line_CBA(self):
        data = {
            "cba": {"type": "LineString", "coordinates": [[2, 0], [1, 0], [0, 0]]},
            "abd": {"type": "LineString", "coordinates": [[0, 0], [1, 0], [3, 0]]},
        }
        topo = topojson.join(topojson.extract(data))
        self.assertTrue(
            geometry.MultiPoint(topo["junctions"]).equals(
                geometry.MultiPoint([(2.0, 0.0), (0.0, 0.0)])
            )
        )

    # when a new line DBC merges into an old line ABC, there is a junction at B
    def test_line_DBC_merge_line_ABC(self):
        data = {
            "abc": {"type": "LineString", "coordinates": [[0, 0], [1, 0], [2, 0]]},
            "dbc": {"type": "LineString", "coordinates": [[3, 0], [1, 0], [2, 0]]},
        }
        topo = topojson.join(topojson.extract(data))
        self.assertTrue(
            geometry.MultiPoint(topo["junctions"]).equals(
                geometry.MultiPoint([(1.0, 0.0), (2.0, 0.0), (3.0, 0.0), (0.0, 0.0)])
            )
        )

    # when a new line DBC merges into a reversed old line CBA, there is a junction at B
    def test_line_DBC_merge_reversed_line_CBA(self):
        data = {
            "cba": {"type": "LineString", "coordinates": [[2, 0], [1, 0], [0, 0]]},
            "dbc": {"type": "LineString", "coordinates": [[3, 0], [1, 0], [2, 0]]},
        }
        topo = topojson.join(topojson.extract(data))
        self.assertTrue(
            geometry.MultiPoint(topo["junctions"]).equals(
                geometry.MultiPoint([(2.0, 0.0), (1.0, 0.0), (3.0, 0.0)])
            )
        )

    # when a new line DBE shares a single midpoint with an old line ABC, there is 
    # no junction at B
    def test_line_DBE_share_singe_midpoint_line_ABC(self):
        data = {
            "abc": {"type": "LineString", "coordinates": [[0, 0], [1, 0], [2, 0]]},
            "dbe": {"type": "LineString", "coordinates": [[0, 1], [1, 0], [2, 1]]},
        }
        topo = topojson.join(topojson.extract(data))
        self.assertListEqual(topo["junctions"], [])

    # when a new line ABDE skips a point with an old line ABCDE, there is a no junction
    def test_line_ABDE_skips_point_line_ABCDE(self):
        data = {
            "abcde": {
                "type": "LineString",
                "coordinates": [[0, 0], [1, 0], [2, 0], [3, 0], [4, 0]],
            },
            "abde": {
                "type": "LineString",
                "coordinates": [[0, 0], [1, 0], [3, 0], [4, 0]],
            },
        }
        topo = topojson.join(topojson.extract(data))
        self.assertListEqual(topo["junctions"], [])

    # when a new line ABDE skips a point with a reversed old line EDCBA, there is 
    # no junction
    def test_line_ABDE_skips_point_reversed_line_EDCBA(self):
        data = {
            "edcba": {
                "type": "LineString",
                "coordinates": [[4, 0], [3, 0], [2, 0], [1, 0], [0, 0]],
            },
            "abde": {
                "type": "LineString",
                "coordinates": [[0, 0], [1, 0], [3, 0], [4, 0]],
            },
        }
        topo = topojson.join(topojson.extract(data))
        self.assertListEqual(topo["junctions"], [])

    # when a line ABCDBE self-intersects with its middle, there are no junctions
    def test_line_ABCDBE_self_intersects_with_middle(self):
        data = {
            "abcdbe": {
                "type": "LineString",
                "coordinates": [[0, 0], [1, 0], [2, 0], [3, 0], [1, 0], [4, 0]],
            }
        }
        topo = topojson.join(topojson.extract(data))
        self.assertListEqual(topo["junctions"], [])

    # when a line ABACD self-intersects with its start, there are no junctions
    def test_line_ABACD_self_intersects_with_middle(self):
        data = {
            "abacd": {
                "type": "LineString",
                "coordinates": [[0, 0], [1, 0], [0, 0], [3, 0], [4, 0]],
            }
        }
        topo = topojson.join(topojson.extract(data))
        self.assertListEqual(topo["junctions"], [])

    # when a line ABCDBD self-intersects with its end, there are no junctions
    def test_line_ABCDBD_self_intersects_with_end(self):
        data = {
            "abcdbd": {
                "type": "LineString",
                "coordinates": [[0, 0], [1, 0], [4, 0], [3, 0], [4, 0]],
            }
        }
        topo = topojson.join(topojson.extract(data))
        self.assertListEqual(topo["junctions"], [])

    # when an old line ABCDBE self-intersects and shares a point B, there is 
    # no junction at B
    def test_line_ABCDB_self_intersects(self):
        data = {
            "abcdbe": {
                "type": "LineString",
                "coordinates": [[0, 0], [1, 0], [2, 0], [3, 0], [1, 0], [4, 0]],
            },
            "fbg": {"type": "LineString", "coordinates": [[0, 1], [1, 0], [2, 1]]},
        }
        topo = topojson.join(topojson.extract(data))
        self.assertListEqual(topo["junctions"], [])

    # when a line ABCA is closed, there is no junction at A
    def test_line_ABCA_is_closed(self):
        data = {
            "abca": {
                "type": "LineString",
                "coordinates": [[0, 0], [1, 0], [0, 1], [0, 0]],
            }
        }
        topo = topojson.join(topojson.extract(data))
        self.assertListEqual(topo["junctions"], [])

    # when a ring ABCA is closed, there are no junctions
    def test_ring_ABCA_is_closed(self):
        data = {
            "abca": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [1, 0], [0, 1], [0, 0]]],
            }
        }
        topo = topojson.join(topojson.extract(data))
        self.assertListEqual(topo["junctions"], [])

    # exact duplicate rings ABCA & ABCA share the arc ABCA, but contain no junctions
    def test_exact_duplicate_rings_ABCA_ABCA_share_ABCA(self):
        data = {
            "abca": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [1, 0], [0, 1], [0, 0]]],
            },
            "abca2": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [1, 0], [0, 1], [0, 0]]],
            },
        }
        topo = topojson.join(topojson.extract(data))
        self.assertListEqual(topo["junctions"], [])

    # reversed duplicate rings ABCA & ACBA share the arc ABCA, but contain no juctions
    def test_exact_duplicate_rings_ABCA_ACBA_share_ABCA(self):
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
        topo = topojson.join(topojson.extract(data))
        self.assertListEqual(topo["junctions"], [])

    # coincident rings ABCA & BCAB share the arc BCAB, but contain no junctinos
    # this is a problem though as they are considered equal in a MultiPolygon geometry.
    # test will pass, but coincident rings should be rotated before dedup
    def test_coincident_rings_ABCA_BCAB_share_BCAB(self):
        data = {
            "abca": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [1, 0], [0, 1], [0, 0]]],
            },
            "bcab": {
                "type": "Polygon",
                "coordinates": [[[1, 0], [0, 1], [0, 0], [1, 0]]],
            },
        }
        topo = topojson.join(topojson.extract(data))
        self.assertListEqual(topo["junctions"], [])

    # coincident rings ABCA & BACB share the arc BCAB, but contain no junctions
    def test_coincident_rings_ABCA_BACB_share_BCAB(self):
        data = {
            "abca": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [1, 0], [0, 1], [0, 0]]],
            },
            "bacb": {
                "type": "Polygon",
                "coordinates": [[[1, 0], [0, 0], [0, 1], [1, 0]]],
            },
        }
        topo = topojson.join(topojson.extract(data))
        self.assertListEqual(topo["junctions"], [])

    # coincident rings ABCA & DBED share the point B, but is no junction
    def test_coincident_rings_ABCA_DBED_share_B(self):
        data = {
            "abca": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [1, 0], [0, 1], [0, 0]]],
            },
            "dbed": {
                "type": "Polygon",
                "coordinates": [[[2, 1], [1, 0], [2, 2], [2, 1]]],
            },
        }
        topo = topojson.join(topojson.extract(data))
        self.assertListEqual(topo["junctions"], [])

    # coincident ring ABCA & line DBE share the point B
    def test_coincident_ring_ABCA_and_line_DBE_share_B(self):
        data = {
            "abca": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [1, 0], [0, 1], [0, 0]]],
            },
            "dbe": {"type": "LineString", "coordinates": [[2, 1], [1, 0], [2, 2]]},
        }
        topo = topojson.join(topojson.extract(data))
        self.assertListEqual(topo["junctions"], [])

    # should keep junctions from partly shared paths
    # this test was added since the a shared path of ABC and another shared path of ABD
    # only kept the junctions at A, C and D, but not at B.
    def test_shared_junctions_in_shared_paths(self):
        data = geopandas.read_file(geopandas.datasets.get_path('naturalearth_lowres'))
        data = data[(data.name == 'Togo') | (data.name == 'Benin') | 
            (data.name == 'Burkina Faso')]
        topo = topojson.join(topojson.extract(data))
        self.assertEqual(len(topo["junctions"]), 6)

    # this test was added since a shared path can be detected of two linestrings where 
    # the shared path is partly from the start and partly of the end part of the 
    # linestring. If any shared path are detected also add the first coordinates of both
    # linestrings to be considerd as junction. Not sure what happened if this introduces
    # another problem since this coordinates may not be unique anymore, and this can be 
    # skipped as a junction..
    def test_shared_segment_partly_start_partly_end_segment(self):
        data = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
        data = data[
            (data.name == "Eritrea")
            | (data.name == "Ethiopia")
            | (data.name == "Sudan")
        ]
        topo = topojson.join(topojson.extract(data))
        self.assertEqual(len(topo['junctions']), 11)  

    def test_non_noded_interesection(self):
        data = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
        topo = topojson.join(topojson.extract(data), quant_factor=1e6)
        self.assertEqual(len(topo['junctions']), 377)               