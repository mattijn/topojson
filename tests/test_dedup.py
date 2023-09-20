import geopandas
import geopandas.datasets
import geojson
from shapely import geometry
from shapely import wkt

from topojson.core.dedup import Dedup


# duplicate rotated geometry bar with hole interior in geometry foo
def test_dedup_duplicate_rotated_hole_interior():
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

    assert len(topo["bookkeeping_duplicates"]) == 0
    assert topo["bookkeeping_geoms"] == [[0, 1], [2], [3]]


def test_dedup_two_polygon_reversed_shared_arc():
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

    assert len(topo["bookkeeping_duplicates"]) == 0
    assert topo["bookkeeping_shared_arcs"] == [2]
    assert topo["bookkeeping_arcs"] == [[2, 0], [1, 2]]


def test_dedup_duplicate_polygon_no_junctions():
    data = {
        "abca": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [0, 1], [0, 0]]]},
        "acba": {"type": "Polygon", "coordinates": [[[0, 0], [0, 1], [1, 0], [0, 0]]]},
    }
    topo = Dedup(data).to_dict()

    assert len(topo["bookkeeping_duplicates"]) == 0
    assert topo["bookkeeping_shared_arcs"] == [0]
    assert topo["bookkeeping_arcs"] == [[0], [0]]
    assert topo["bookkeeping_geoms"] == [[0], [1]]


def test_dedup_shared_line_ABCDBE_and_FBCG():
    # This is a weird test case. The first linestring doubles back on itself, so
    # self-intersects?
    data = {
        "abcdbe": {
            "type": "LineString",
            "coordinates": [[0, 0], [1, 0], [2, 0], [3, 0], [1, 0], [4, 0]],
        },
        "fbcg": {"type": "LineString", "coordinates": [[0, 1], [1, 0], [2, 0], [3, 1]]},
    }
    topo = Dedup(data).to_dict()

    assert len(topo["bookkeeping_duplicates"]) == 0
    assert len(topo["bookkeeping_shared_arcs"]) == 1
    assert len(topo["bookkeeping_arcs"]) == 2
    assert topo["bookkeeping_geoms"] == [[0], [1]]


# this test was added since the shared_arcs bookkeeping is not doing well. Next runs
# can affect previous runs where dup_pair_list should update properly.
def test_dedup_shared_junctions_in_shared_paths():
    data = geopandas.read_file("tests/files_shapefile/static_natural_earth.gpkg")
    data = data[
        (data.ADMIN == "Togo")
        | (data.ADMIN == "Benin")
        | (data.ADMIN == "Burkina Faso")
    ]
    topo = Dedup(data).to_dict()

    assert len(topo["bookkeeping_shared_arcs"]) == 3
    assert len(topo["bookkeeping_duplicates"]) == 0


# this test was added since the shared_arcs bookkeeping is doing well, but the
# wrong arc got deleted. How come?
# the problem arose in wrongly line-merging of contiguous line-elements
# merged linestring is not always placed upfront.
def test_dedup_arc_not_shared_arcs_got_deleted():
    data = geopandas.read_file("tests/files_shapefile/static_natural_earth.gpkg")
    data = data[
        (data.ADMIN == "Botswana")
        | (data.ADMIN == "South Africa")
        | (data.ADMIN == "Zimbabwe")
        | (data.ADMIN == "Mozambique")
        | (data.ADMIN == "Zambia")
    ]
    topo = Dedup(data).to_dict()

    assert len(topo["bookkeeping_shared_arcs"]) == 9
    assert len(topo["bookkeeping_duplicates"]) == 0


# this test was added since there is no test for non-intersecting geometries.
# as was raised in https://github.com/mattijn/topojson/issues/1
def test_dedup_no_shared_paths_in_geoms():
    data = geopandas.read_file("tests/files_shapefile/static_natural_earth.gpkg")
    data = data[(data.ADMIN == "Togo") | (data.ADMIN == "Liberia")]
    topo = Dedup(data).to_dict()

    assert len(topo["bookkeeping_shared_arcs"]) == 0
    assert len(topo["bookkeeping_duplicates"]) == 0


def test_dedup_super_function():
    data = geometry.GeometryCollection(
        [
            geometry.Polygon([[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]),
            geometry.Polygon([[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]),
        ]
    )
    topo = Dedup(data).to_dict()

    assert len(list(topo.keys())) == 12


# this test was added since the local variable "array_bk_sarcs" was
# referenced before assignment. As was raised in:
# https://github.com/mattijn/topojson/issues/3
def test_dedup_array_bk_sarcs_reference():
    data = {
        "foo": {"type": "LineString", "coordinates": [[4, 0], [2, 2], [0, 0]]},
        "bar": {
            "type": "LineString",
            "coordinates": [[0, 2], [1, 1], [2, 2], [3, 1], [4, 2]],
        },
    }
    topo = Dedup(data).to_dict()

    assert len(topo["bookkeeping_shared_arcs"]) == 1
    assert len(topo["junctions"]) == 2


# this test was added since there is an error stating the following during Dedup:
# TypeError: list indices must be integers or slices, not NoneType, see #50
def test_dedup_s2_geometries():
    data = [
        wkt.loads(
            "MULTILINESTRING ((-51.17176115208171 -30.05269620283153, -51.18859500873385 -29.99305326146263, -51.1541142383379 -29.95234110496228, -51.13731737261026 -30.01193511071039, -51.17176115208171 -30.05269620283153), (-51.13731737261026 -30.01193511071039, -51.1541142383379 -29.95234110496228, -51.11963364027719 -29.91170657721793, -51.10287369862932 -29.97125162042611, -51.13731737261026 -30.01193511071039), (-51.13799328025614 -30.17188406207867, -51.17176115208171 -30.05269620283153, -51.10287369862932 -29.97125162042611, -51.06925390117097 -30.09024489967364, -51.13799328025614 -30.17188406207867), (-51.06925390117097 -30.09024489967364, -51.0860804353923 -30.03076444145886, -51.05167386668366 -29.99010960397871, -51.03488427131447 -30.04954147652281, -51.06925390117097 -30.09024489967364), (-51.0860804353923 -30.03076444145886, -51.10287369862932 -29.97125162042611, -51.0684302317277 -29.9306455702365, -51.05167386668366 -29.99010960397871, -51.0860804353923 -30.03076444145886))"
        )
    ]
    topo = Dedup(data).to_dict()

    assert len(topo["junctions"]) == 4
    assert len(topo["bookkeeping_duplicates"]) == 0


def test_dedup_linemerge_multilinestring():
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
    topo = Dedup(data).to_dict()

    assert len(topo["linestrings"]) == 9
    assert len(topo["junctions"]) == 6


# this test was added since the local variable "array_bk_sarcs" was
# referenced before assignment. As was raised in:
# https://github.com/mattijn/topojson/issues/3
def test_dedup_shared_paths_array_bk_sarcs_reference():
    data = {
        "foo": {"type": "LineString", "coordinates": [[4, 0], [2, 2], [0, 0]]},
        "bar": {
            "type": "LineString",
            "coordinates": [[0, 2], [1, 1], [2, 2], [3, 1], [4, 2]],
        },
    }
    topo = Dedup(data, options={"shared_coords": False}).to_dict()

    assert len(topo["bookkeeping_shared_arcs"]) == 1
    junctions = [list(junction.coords) for junction in topo["junctions"]]
    assert sorted(junctions) == sorted([[(1.0, 1.0)], [(3.0, 1.0)]])


# this test was added since there is an error stating the following during Dedup:
# TypeError: list indices must be integers or slices, not NoneType, see #50
def test_dedup_shared_paths_s2_geometries():
    data = [
        wkt.loads(
            "MULTILINESTRING ((-51.17176115208171 -30.05269620283153, -51.18859500873385 -29.99305326146263, -51.1541142383379 -29.95234110496228, -51.13731737261026 -30.01193511071039, -51.17176115208171 -30.05269620283153), (-51.13731737261026 -30.01193511071039, -51.1541142383379 -29.95234110496228, -51.11963364027719 -29.91170657721793, -51.10287369862932 -29.97125162042611, -51.13731737261026 -30.01193511071039), (-51.13799328025614 -30.17188406207867, -51.17176115208171 -30.05269620283153, -51.10287369862932 -29.97125162042611, -51.06925390117097 -30.09024489967364, -51.13799328025614 -30.17188406207867), (-51.06925390117097 -30.09024489967364, -51.0860804353923 -30.03076444145886, -51.05167386668366 -29.99010960397871, -51.03488427131447 -30.04954147652281, -51.06925390117097 -30.09024489967364), (-51.0860804353923 -30.03076444145886, -51.10287369862932 -29.97125162042611, -51.0684302317277 -29.9306455702365, -51.05167386668366 -29.99010960397871, -51.0860804353923 -30.03076444145886))"
        )
    ]
    topo = Dedup(data, options={"shared_coords": False}).to_dict()

    assert len(topo["junctions"]) == 4
    assert len(topo["bookkeeping_duplicates"]) == 0


def test_dedup_shared_paths_linemerge_multilinestring():
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
    topo = Dedup(data, options={"shared_coords": False}).to_dict()

    assert len(topo["linestrings"]) == 9
    assert len(topo["junctions"]) == 6


def test_dedup_topology_false():
    data = geopandas.read_file("tests/files_shapefile/static_natural_earth.gpkg")
    topo = Dedup(data, options={"topology": False}).to_dict()

    assert len(topo["linestrings"]) == 288
    assert len(topo["junctions"]) == 0


# see https://github.com/mattijn/topojson/issues/104 for context
# TypeError: cannot unpack non-iterable NoneType object and
# TypeError: 'NoneType' object is not iterable
def test_dedup_merge_continuous():
    data = [
        {"type": "LineString", "coordinates": [(1, 0), (2, 0), (3, 0), (4, 0), (5, 0)]},
        {
            "type": "LineString",
            "coordinates": [
                (5, 0),
                (4, -1),
                (4, 0),
                (4, 1),
                (3, 1),
                (3, 0),
                (2, 1),
                (2, 0),
                (1, 0),
                (1, 1),
            ],
        },
    ]
    topo = Dedup(data, options={"prequantize": False}).to_dict()

    assert len(topo["linestrings"]) == 4
    assert len(topo["junctions"]) == 2


def test_dedup_merge_continuous_shared_path():
    data = geojson.loads(
        '{"type": "FeatureCollection", "features": [{"id": "0", "type": "Feature", "properties": {"certainty": 4}, "geometry": {"type": "Polygon", "coordinates": [[[380565.0, -3576915.0], [380595.0, -3576915.0], [380595.0, -3576945.0], [380625.0, -3576945.0], [380625.0, -3576975.0], [380595.0, -3576975.0], [380595.0, -3577005.0], [380565.0, -3577005.0], [380565.0, -3577035.0], [380595.0, -3577035.0], [380595.0, -3577065.0], [380625.0, -3577065.0], [380625.0, -3577095.0], [380655.0, -3577095.0], [380655.0, -3577065.0], [380685.0, -3577065.0], [380685.0, -3577035.0], [380745.0, -3577035.0], [380745.0, -3577065.0], [380775.0, -3577065.0], [380775.0, -3577095.0], [380895.0, -3577095.0], [380895.0, -3577125.0], [380865.0, -3577125.0], [380865.0, -3577215.0], [380835.0, -3577215.0], [380835.0, -3577245.0], [380805.0, -3577245.0], [380805.0, -3577215.0], [380745.0, -3577215.0], [380745.0, -3577245.0], [380685.0, -3577245.0], [380685.0, -3577215.0], [380625.0, -3577215.0], [380625.0, -3577245.0], [380595.0, -3577245.0], [380595.0, -3577185.0], [380565.0, -3577185.0], [380565.0, -3577125.0], [380535.0, -3577125.0], [380535.0, -3577005.0], [380505.0, -3577005.0], [380505.0, -3576945.0], [380535.0, -3576945.0], [380565.0, -3576945.0], [380565.0, -3576915.0]]]}}, {"id": "1", "type": "Feature", "properties": {"certainty": 4}, "geometry": {"type": "Polygon", "coordinates": [[[380685.0, -3577335.0], [380715.0, -3577335.0], [380715.0, -3577365.0], [380745.0, -3577365.0], [380745.0, -3577395.0], [380715.0, -3577395.0], [380715.0, -3577425.0], [380685.0, -3577425.0], [380685.0, -3577395.0], [380655.0, -3577395.0], [380655.0, -3577365.0], [380685.0, -3577365.0], [380685.0, -3577335.0]]]}}, {"id": "2", "type": "Feature", "properties": {"certainty": 4}, "geometry": {"type": "Polygon", "coordinates": [[[380865.0, -3577395.0], [380895.0, -3577395.0], [380895.0, -3577425.0], [380925.0, -3577425.0], [380925.0, -3577455.0], [380895.0, -3577455.0], [380895.0, -3577485.0], [380835.0, -3577485.0], [380835.0, -3577425.0], [380865.0, -3577425.0], [380865.0, -3577395.0]]]}}, {"id": "3", "type": "Feature", "properties": {"certainty": 4}, "geometry": {"type": "Polygon", "coordinates": [[[381075.0, -3577965.0], [381195.0, -3577965.0], [381195.0, -3578025.0], [381165.0, -3578025.0], [381165.0, -3578055.0], [381135.0, -3578055.0], [381105.0, -3578055.0], [381105.0, -3578085.0], [381075.0, -3578085.0], [381075.0, -3578115.0], [381045.0, -3578115.0], [381045.0, -3578145.0], [381015.0, -3578145.0], [381015.0, -3578115.0], [380985.0, -3578115.0], [380985.0, -3578145.0], [380955.0, -3578145.0], [380955.0, -3578115.0], [380925.0, -3578115.0], [380925.0, -3578145.0], [380865.0, -3578145.0], [380865.0, -3578115.0], [380835.0, -3578115.0], [380835.0, -3578085.0], [380805.0, -3578085.0], [380805.0, -3577995.0], [380835.0, -3577995.0], [380835.0, -3578025.0], [380865.0, -3578025.0], [380865.0, -3578055.0], [380895.0, -3578055.0], [380895.0, -3578085.0], [380985.0, -3578085.0], [380985.0, -3578055.0], [381015.0, -3578055.0], [381015.0, -3578025.0], [381045.0, -3578025.0], [381045.0, -3577995.0], [381075.0, -3577995.0], [381075.0, -3577965.0]]]}}, {"id": "4", "type": "Feature", "properties": {"certainty": 4}, "geometry": {"type": "Polygon", "coordinates": [[[381255.0, -3578085.0], [381315.0, -3578085.0], [381315.0, -3578115.0], [381345.0, -3578115.0], [381345.0, -3578145.0], [381315.0, -3578145.0], [381285.0, -3578145.0], [381285.0, -3578175.0], [381255.0, -3578175.0], [381255.0, -3578145.0], [381225.0, -3578145.0], [381225.0, -3578115.0], [381255.0, -3578115.0], [381255.0, -3578085.0]]]}}, {"id": "5", "type": "Feature", "properties": {"certainty": 0}, "geometry": {"type": "Polygon", "coordinates": [[[381500.0, -3578500.0], [380400.0, -3578500.0], [380400.0, -3576500.0], [381500.0, -3576500.0], [381500.0, -3578500.0]], [[381285.0, -3578145.0], [381315.0, -3578145.0], [381345.0, -3578145.0], [381345.0, -3578115.0], [381315.0, -3578115.0], [381315.0, -3578085.0], [381255.0, -3578085.0], [381255.0, -3578115.0], [381225.0, -3578115.0], [381225.0, -3578145.0], [381255.0, -3578145.0], [381255.0, -3578175.0], [381285.0, -3578175.0], [381285.0, -3578145.0]], [[380805.0, -3577995.0], [380805.0, -3578085.0], [380835.0, -3578085.0], [380835.0, -3578115.0], [380865.0, -3578115.0], [380865.0, -3578145.0], [380925.0, -3578145.0], [380925.0, -3578115.0], [380955.0, -3578115.0], [380955.0, -3578145.0], [380985.0, -3578145.0], [380985.0, -3578115.0], [381015.0, -3578115.0], [381015.0, -3578145.0], [381045.0, -3578145.0], [381045.0, -3578115.0], [381075.0, -3578115.0], [381075.0, -3578085.0], [381105.0, -3578085.0], [381105.0, -3578055.0], [381135.0, -3578055.0], [381165.0, -3578055.0], [381165.0, -3578025.0], [381195.0, -3578025.0], [381195.0, -3577965.0], [381075.0, -3577965.0], [381075.0, -3577995.0], [381045.0, -3577995.0], [381045.0, -3578025.0], [381015.0, -3578025.0], [381015.0, -3578055.0], [380985.0, -3578055.0], [380985.0, -3578085.0], [380895.0, -3578085.0], [380895.0, -3578055.0], [380865.0, -3578055.0], [380865.0, -3578025.0], [380835.0, -3578025.0], [380835.0, -3577995.0], [380805.0, -3577995.0]], [[380895.0, -3577455.0], [380925.0, -3577455.0], [380925.0, -3577425.0], [380895.0, -3577425.0], [380895.0, -3577395.0], [380865.0, -3577395.0], [380865.0, -3577425.0], [380835.0, -3577425.0], [380835.0, -3577485.0], [380895.0, -3577485.0], [380895.0, -3577455.0]], [[380565.0, -3576915.0], [380565.0, -3576945.0], [380535.0, -3576945.0], [380505.0, -3576945.0], [380505.0, -3577005.0], [380535.0, -3577005.0], [380535.0, -3577125.0], [380565.0, -3577125.0], [380565.0, -3577185.0], [380595.0, -3577185.0], [380595.0, -3577245.0], [380625.0, -3577245.0], [380625.0, -3577215.0], [380685.0, -3577215.0], [380685.0, -3577245.0], [380745.0, -3577245.0], [380745.0, -3577215.0], [380805.0, -3577215.0], [380805.0, -3577245.0], [380835.0, -3577245.0], [380835.0, -3577215.0], [380865.0, -3577215.0], [380865.0, -3577125.0], [380895.0, -3577125.0], [380895.0, -3577095.0], [380775.0, -3577095.0], [380775.0, -3577065.0], [380745.0, -3577065.0], [380745.0, -3577035.0], [380685.0, -3577035.0], [380685.0, -3577065.0], [380655.0, -3577065.0], [380655.0, -3577095.0], [380625.0, -3577095.0], [380625.0, -3577065.0], [380595.0, -3577065.0], [380595.0, -3577035.0], [380565.0, -3577035.0], [380565.0, -3577005.0], [380595.0, -3577005.0], [380595.0, -3576975.0], [380625.0, -3576975.0], [380625.0, -3576945.0], [380595.0, -3576945.0], [380595.0, -3576915.0], [380565.0, -3576915.0]], [[380655.0, -3577365.0], [380655.0, -3577395.0], [380685.0, -3577395.0], [380685.0, -3577425.0], [380715.0, -3577425.0], [380715.0, -3577395.0], [380745.0, -3577395.0], [380745.0, -3577365.0], [380715.0, -3577365.0], [380715.0, -3577335.0], [380685.0, -3577335.0], [380685.0, -3577365.0], [380655.0, -3577365.0]]]}}]}'
    )
    topo = Dedup(data, options={"shared_coords": False}).to_dict()

    assert len(topo["linestrings"]) == 6
    assert len(topo["junctions"]) == 0
