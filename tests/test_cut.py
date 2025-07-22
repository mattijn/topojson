import geopandas
import geopandas.datasets
import pytest
from shapely import geometry, wkt

from topojson.core.cut import Cut


# cut exact duplicate lines ABC & ABC have no cuts
def test_cut_exact_duplicate_lines_ABC_ABC_no_cuts():
    data = {
        "abc": {"type": "LineString", "coordinates": [[0, 0], [1, 0], [2, 0]]},
        "abc2": {"type": "LineString", "coordinates": [[0, 0], [1, 0], [2, 0]]},
    }
    topo = Cut(data).to_dict()

    assert len(topo["junctions"]) == 0
    assert topo["bookkeeping_duplicates"].tolist() == [[1, 0]]


# cut reversed duplicate lines ABC & CBA have no cuts
def test_cut_reversed_duplicate_lines_ABC_CBA_no_cuts():
    data = {
        "abc": {"type": "LineString", "coordinates": [[0, 0], [1, 0], [2, 0]]},
        "cba": {"type": "LineString", "coordinates": [[2, 0], [1, 0], [0, 0]]},
    }
    topo = Cut(data).to_dict()

    assert len(topo["junctions"]) == 0
    assert topo["bookkeeping_duplicates"].tolist() == [[1, 0]]


# overlapping rings ABCDA and BEFCB are cut into BC-CDAB and BEFC-CB
def test_cut_overlapping_rings_are_cut():
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

    assert topo["bookkeeping_linestrings"].size == 4
    assert topo["bookkeeping_duplicates"].tolist() == [[3, 0]]


# currently the border between Sudan and Egypt is not recognized as duplicate
# because of floating-precision. Should be solved by a "snap_to_grid" option.
def test_cut_border_egypt_sudan():
    data = geopandas.read_file("tests/files_shapefile/static_natural_earth.gpkg")
    data = data[(data.ADMIN == "Egypt") | (data.ADMIN == "Sudan")]
    topo = Cut(data).to_dict()

    assert len(topo["bookkeeping_duplicates"].tolist()) == 1


def test_cut_nybb_fast_split():
    data = geopandas.read_file("tests/files_shapefile/static_nybb.gpkg")
    data.set_index("BoroCode", inplace=True)
    topo = Cut(data).to_dict()

    assert topo["bookkeeping_linestrings"].size == 4664


# this test was added since the fast_split was really slow on geometries
# when there are many junctions in the geometry. During debugging this test ran
# eventually 8x more quick.
def test_cut_many_junctions():
    data = geopandas.read_file("tests/files_geojson/mesh2d.geojson")
    # previous test ran in 8.798s (best of 3)
    # current test ran in 8.182s (best of 3)
    topo = Cut(data).to_dict()

    assert topo["bookkeeping_linestrings"].size == 11010


def test_cut_super_function_cut():
    data = geometry.GeometryCollection(
        [
            geometry.Polygon([[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]),
            geometry.Polygon([[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]),
        ]
    )
    topo = Cut(data).to_dict()

    assert len(list(topo.keys())) == 11


# this geometry is added on several classes (extract and hashmap). Not yet clear in
# which phase it is going wrong
def test_cut_geomcol_multipolygon_polygon():
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

    assert topo["bookkeeping_linestrings"].size == 8


def test_cut_junctions_coords():
    data = geopandas.read_file("tests/files_geojson/naturalearth_alb_grc.geojson")
    topo = Cut(data, options={"shared_coords": True}).to_dict()

    assert len(topo["linestrings"]) == 3


# this test is added since its seems no extra junctions are placed at lines where other
# linestrings have shared paths but no shared junctions.
def test_cut_linemerge_multilinestring():
    data = [
        {"type": "LineString", "coordinates": [(0, 0), (10, 0), (10, 5), (20, 5)]},
        {
            "type": "LineString",
            "coordinates": [
                (5, 0),
                (25, 0),
                (25, 5),
                (16, 5),
                (16, 10),
                (14, 10),
                (14, 5),
                (0, 5),
            ],
        },
    ]
    topo = Cut(data).to_dict()

    assert len(topo["linestrings"]) == 12
    assert len(topo["junctions"]) == 6


# cut exact duplicate rings ABCA & ABCA have no cuts
def test_cut_exact_duplicate_rings_ABCA_ABCA_no_cuts():
    data = {
        "abca": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [2, 1], [0, 0]]]},
        "abca2": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [2, 1], [0, 0]]]},
    }
    topo = Cut(data).to_dict()

    assert len(topo["junctions"]) == 0
    assert topo["bookkeeping_duplicates"].tolist() == [[1, 0]]


# cut reversed rings ABCA & ACBA have no cuts
def test_cut_reversed_rings_ABCA_ACBA_no_cuts():
    data = {
        "abca": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [2, 1], [0, 0]]]},
        "acba": {"type": "Polygon", "coordinates": [[[0, 0], [2, 1], [1, 0], [0, 0]]]},
    }
    topo = Cut(data).to_dict()

    assert len(topo["junctions"]) == 0
    assert topo["bookkeeping_duplicates"].tolist() == [[1, 0]]


# cut rotated duplicate rings BCAB & ABCA have no cuts
def test_cut_rotated_duplicates_rings_BCAB_ABCA_no_cuts():
    data = {
        "abca": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [2, 1], [0, 0]]]},
        "bcab": {"type": "Polygon", "coordinates": [[[1, 0], [2, 1], [0, 0], [1, 0]]]},
    }
    topo = Cut(data).to_dict()

    assert len(topo["junctions"]) == 0
    assert len(topo["bookkeeping_duplicates"]) == 1


# cut ring ABCA & line ABCA have no cuts
def test_cut_ring_ABCA_line_ABCA_no_cuts():
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

    assert len(topo["junctions"]) == 0
    assert topo["bookkeeping_duplicates"].tolist() == [[1, 0]]


# cut ring BCAB & line ABCA have no cuts
def test_cut_ring_BCAB_line_ABCA_no_cuts():
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

    assert len(topo["junctions"]) == 0
    assert len(topo["bookkeeping_duplicates"]) == 1


# cut ring ABCA & line BCAB have no cuts
def test_cut_ring_ABCA_line_BCAB_no_cuts():
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

    assert len(topo["junctions"]) == 0
    assert len(topo["bookkeeping_duplicates"]) == 1


# this test is added since its seems no extra junctions are placed at lines where other
# linestrings have shared paths but no shared junctions.
def test_cut_shared_paths_linemerge_multilinestring():
    data = [
        {"type": "LineString", "coordinates": [(0, 0), (10, 0), (10, 5), (20, 5)]},
        {
            "type": "LineString",
            "coordinates": [
                (5, 0),
                (25, 0),
                (25, 5),
                (16, 5),
                (16, 10),
                (14, 10),
                (14, 5),
                (0, 5),
            ],
        },
    ]
    topo = Cut(data, options={"shared_coords": False}).to_dict()

    assert len(topo["linestrings"]) == 12
    assert len(topo["junctions"]) == 6


# cut exact duplicate rings ABCA & ABCA have no cuts
def test_cut_shared_paths_exact_duplicate_rings_ABCA_ABCA_no_cuts():
    data = {
        "abca": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [2, 1], [0, 0]]]},
        "abca2": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [2, 1], [0, 0]]]},
    }
    topo = Cut(data, options={"shared_coords": False}).to_dict()

    assert len(topo["junctions"]) == 0
    assert topo["bookkeeping_duplicates"].tolist() == [[1, 0]]


# cut reversed rings ABCA & ACBA have no cuts
def test_cut_shared_paths_reversed_rings_ABCA_ACBA_no_cuts():
    data = {
        "abca": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [2, 1], [0, 0]]]},
        "acba": {"type": "Polygon", "coordinates": [[[0, 0], [2, 1], [1, 0], [0, 0]]]},
    }
    topo = Cut(data, options={"shared_coords": False}).to_dict()

    assert len(topo["junctions"]) == 0
    assert topo["bookkeeping_duplicates"].tolist() == [[1, 0]]


# cut rotated duplicate rings BCAB & ABCA have no cuts
def test_cut_shared_paths_rotated_duplicates_rings_BCAB_ABCA_no_cuts():
    data = {
        "abca": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [2, 1], [0, 0]]]},
        "bcab": {"type": "Polygon", "coordinates": [[[1, 0], [2, 1], [0, 0], [1, 0]]]},
    }
    topo = Cut(data, options={"shared_coords": False}).to_dict()

    assert len(topo["junctions"]) == 0
    assert len(topo["bookkeeping_duplicates"]) == 1


# cut ring ABCA & line ABCA have no cuts
def test_cut_shared_paths_ring_ABCA_line_ABCA_no_cuts():
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
    topo = Cut(data, options={"shared_coords": False}).to_dict()

    assert len(topo["junctions"]) == 0
    assert topo["bookkeeping_duplicates"].tolist() == [[1, 0]]


# cut ring BCAB & line ABCA have no cuts
def test_cut_shared_paths_ring_BCAB_line_ABCA_no_cuts():
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
    topo = Cut(data, options={"shared_coords": False}).to_dict()

    assert len(topo["junctions"]) == 0
    assert len(topo["bookkeeping_duplicates"]) == 1


# cut ring ABCA & line BCAB have no cuts
def test_cut_shared_paths_ring_ABCA_line_BCAB_no_cuts():
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
    topo = Cut(data, options={"shared_coords": False}).to_dict()

    assert len(topo["junctions"]) == 0
    assert len(topo["bookkeeping_duplicates"]) == 1


# topoquantize can have low values, but prequantize cannot. this smells as a bug
# fixed issue in find_duplicates()
def test_cut_low_prequantize():
    import topojson.utils

    data = topojson.utils.example_data_africa()
    topo = Cut(data, options={"prequantize": 75}).to_dict()

    assert len(topo["bookkeeping_duplicates"]) == 163


# test added for issue regarding dedup of +- equal linestrings not happening
@pytest.mark.parametrize("shared_coords, junctions", [(True, 2), (False, 0)])
def test_cut_extra_points_no_cuts(shared_coords, junctions):
    """
    Tests if 2 linestrings are correctly treated as duplicate if they follow the same
    path, but one of them has extra point(s) that disappear with simplify(0).
    No junctions for shared_coords=False, 2 for shared_coords=True.
    """
    g0 = wkt.loads("LineString (0 0, 1 0, 2 0)")
    g1 = wkt.loads("LineString (0 0, 2 0)")
    data = geopandas.GeoDataFrame({"name": ["a", "b"], "geometry": [g0, g1]})
    topo = Cut(
        data, options={"prequantize": False, "shared_coords": shared_coords}
    ).to_dict()

    assert len(topo["junctions"]) == junctions
    assert len(topo["bookkeeping_duplicates"]) == 1


# test added for issue regarding dedup of +- equal linestrings not happening
@pytest.mark.parametrize("shared_coords", [(True), (False)])
def test_cut_extra_points_cut(shared_coords):
    """
    Tests if 2 linestrings are correctly treated as duplicate if they follow the same
    path, but one of them has extra point(s) that disappear with simplify(0).
    """
    g0 = wkt.loads("LineString (0 0, 1 0, 2 0, 3 0)")
    g1 = wkt.loads("LineString (0 0, 2 0)")
    data = geopandas.GeoDataFrame({"name": ["a", "b"], "geometry": [g0, g1]})
    topo = Cut(
        data, options={"prequantize": False, "shared_coords": shared_coords}
    ).to_dict()

    assert len(topo["junctions"]) == 2
    assert len(topo["bookkeeping_duplicates"]) == 1


@pytest.mark.parametrize("shared_coords, junctions", [(True, 4), (False, 2)])
def test_cut_extra_points_other_line_cut(shared_coords, junctions):
    """
    Tests if 2 linestrings are correctly treated as duplicate if they follow the same
    path, but:
      - one of them has extra point(s) that disappear with simplify(0).
      - there is another line combination in the dataset that creates junctions for
        shared_coords=False.
    """
    l1 = wkt.loads("LineString (0 0, 2 0)")
    l2_l1_extra_colinear = wkt.loads("LineString (0 0, 1 0, 2 0)")
    l3 = wkt.loads("LineString (0 1, 2 1, 3 1)")
    l4_cuts_l3 = wkt.loads("LineString (0 1, 2 1)")
    data = geopandas.GeoDataFrame(
        {
            "name": ["l1", "l2", "l3", "l4"],
            "geometry": [l1, l2_l1_extra_colinear, l3, l4_cuts_l3],
        }
    )
    topo = Cut(
        data, options={"prequantize": False, "shared_coords": shared_coords}
    ).to_dict()

    assert len(topo["junctions"]) == junctions
    assert len(topo["bookkeeping_duplicates"]) == 2
