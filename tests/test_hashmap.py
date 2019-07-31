import unittest
import topojson
import geopandas
from shapely import geometry
from topojson.core.hashmap import Hashmap


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
        topo = Hashmap(data).to_dict()
        # print(topo)
        self.assertEqual(
            topo["objects"]["data"]["geometries"][0]["arcs"], [[[4, 0]], [[1]], [[2]]]
        )

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
        topo = Hashmap(data).to_dict()
        self.assertEqual(topo["objects"]["data"]["geometries"][0]["arcs"], [[-3, 0]])
        self.assertEqual(topo["objects"]["data"]["geometries"][1]["arcs"], [[1, 2]])

    # this test should catch a shared boundary and a hashed multipolgon
    # related to https://github.com/Toblerity/Shapely/issues/535
    def test_albania_greece(self):
        data = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
        data = data[(data.name == "Albania") | (data.name == "Greece")]
        topo = Hashmap(data).to_dict()
        self.assertEqual(len(topo["arcs"]), 4)

    # something is wrong with hashmapping in the example of benin
    def test_benin_surrounding_countries(self):
        data = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
        data = data[
            (data.name == "Togo")
            | (data.name == "Benin")
            | (data.name == "Burkina Faso")
        ]
        topo = Hashmap(data).to_dict()
        self.assertEqual(len(topo["arcs"]), 6)

    # something is wrong with hashmapping once a geometry has only shared arcs
    def test_geom_surrounding_many_geometries(self):
        data = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
        data = data[
            (data.name == "Botswana")
            | (data.name == "South Africa")
            | (data.name == "Zimbabwe")
            | (data.name == "Namibia")
            | (data.name == "Zambia")
        ]
        topo = Hashmap(data).to_dict()
        self.assertEqual(len(topo["arcs"]), 13)

    # this test was added since the shared_arcs bookkeeping is doing well, but the
    # wrong arc gots deleted. How come?
    def test_shared_arcs_ordering_issues(self):
        data = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
        data = data[
            (data.name == "Botswana")
            | (data.name == "South Africa")
            | (data.name == "Zimbabwe")
            | (data.name == "Mozambique")
            | (data.name == "Zambia")
        ]
        topo = Hashmap(data).to_dict()
        self.assertEqual(len(topo["arcs"]), 17)

    def test_super_function_hashmap(self):
        data = geometry.GeometryCollection(
            [
                geometry.Polygon([[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]),
                geometry.Polygon([[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]),
            ]
        )
        topo = Hashmap(data).to_dict()
        self.assertEqual(list(topo.keys()), ["type", "objects", "options", "arcs"])

    # this test was added since geometries of only linestrings resulted in a topojson
    # file that returns an empty geodataframe when reading
    def test_linestrings_parsed_to_gdf(self):
        data = [
            {"type": "LineString", "coordinates": [[4, 0], [2, 2], [0, 0]]},
            {
                "type": "LineString",
                "coordinates": [[0, 2], [1, 1], [2, 2], [3, 1], [4, 2]],
            },
        ]
        topo = Hashmap(data).to_gdf()
        self.assertNotEqual(topo["geometry"][0].wkt, "GEOMETRYCOLLECTION EMPTY")
        self.assertEqual(topo["geometry"][0].type, "LineString")

    # this test wass added since objects with nested geometreycollections seems not
    # being parsed in the topojson format
    def test_hashing_of_nested_geometrycollection(self):
        data = {
            "foo": {
                "type": "GeometryCollection",
                "geometries": [
                    {
                        "type": "GeometryCollection",
                        "geometries": [
                            {
                                "type": "LineString",
                                "coordinates": [[0.1, 0.2], [0.3, 0.4]],
                            }
                        ],
                    },
                    {
                        "type": "Polygon",
                        "coordinates": [[[0.5, 0.6], [0.7, 0.8], [0.9, 1.0]]],
                    },
                ],
            }
        }
        topo = Hashmap(data).to_dict()  # .to_gdf()
        self.assertNotEqual(topo["geometry"][0].wkt, "GEOMETRYCOLLECTION EMPTY")

