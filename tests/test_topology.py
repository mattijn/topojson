import json
import unittest
from shapely import geometry
import geopandas
import geojson
import topojson
from topojson.utils import TopoOptions


class TestTopology(unittest.TestCase):

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
        topo = topojson.Topology(data).to_gdf()
        self.assertNotEqual(topo["geometry"][0].wkt, "GEOMETRYCOLLECTION EMPTY")
        self.assertEqual(topo["geometry"][0].type, "LineString")

    # test winding order using TopoOptions object
    def test_winding_order_TopoOptions(self):
        from topojson.utils import TopoOptions

        data = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
        data = data[(data.name == "South Africa")]

        topo = topojson.Topology(data, winding_order="CW_CCW").to_dict()
        self.assertEqual(len(topo["objects"]), 1)
        self.assertEqual(isinstance(topo["options"], TopoOptions), True)

    # test winding order using kwarg variables
    def test_winding_order_kwarg_vars(self):

        data = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
        data = data[(data.name == "South Africa")]

        topo = topojson.Topology(data, winding_order="CW_CCW").to_dict()
        self.assertEqual(len(topo["objects"]), 1)
        self.assertEqual(isinstance(topo["options"], TopoOptions), True)

    def test_computing_topology(self):
        data = [
            {"type": "LineString", "coordinates": [[4, 0], [2, 2], [0, 0]]},
            {
                "type": "LineString",
                "coordinates": [[0, 2], [1, 1], [2, 2], [3, 1], [4, 2]],
            },
        ]

        no_topo = topojson.Topology(data, topology=False, prequantize=False).to_dict()
        topo = topojson.Topology(data, topology=True, prequantize=False).to_dict()

        self.assertEqual(len(topo["arcs"]), 5)
        self.assertEqual(len(no_topo["arcs"]), 2)

    # test prequantization without computing topology
    def test_prequantization(self):

        data = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
        data = data[
            (data.name == "Botswana")
            | (data.name == "South Africa")
            | (data.name == "Zimbabwe")
            | (data.name == "Mozambique")
            | (data.name == "Zambia")
        ]

        topo = topojson.Topology(data, topology=False, prequantize=1e4).to_dict()
        self.assertEqual("transform" in topo.keys(), True)

    # test prequantization without computing topology
    def test_prequantization_including_delta_encoding(self):

        data = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
        data = data[
            (data.name == "Botswana")
            | (data.name == "South Africa")
            | (data.name == "Zimbabwe")
            | (data.name == "Mozambique")
            | (data.name == "Zambia")
        ]

        topo = topojson.Topology(data, topology=False, prequantize=1e4).to_dict()
        self.assertEqual("transform" in topo.keys(), True)

    def test_toposimplify_set_in_options(self):
        data = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
        data = data[(data.name == "Antarctica")]
        topo = topojson.Topology(
            data, prequantize=True, simplify_with="shapely", toposimplify=4
        ).to_dict()
        self.assertEqual("transform" in topo.keys(), True)

    def test_toposimplify_as_chaining(self):
        data = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
        data = data[(data.name == "Antarctica")]
        topo = topojson.Topology(data, prequantize=True, simplify_with="shapely")
        topos = topo.toposimplify(2).to_dict()
        self.assertEqual("transform" in topos.keys(), True)

    def test_topoquantize_as_chaining(self):
        data = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
        data = data[(data.name == "Antarctica")]
        topo = topojson.Topology(data, prequantize=False, simplify_with="shapely")
        topos = topo.topoquantize(1e2).to_dict()
        self.assertEqual("transform" in topos.keys(), True)

    def test_prequantize_topoquantize_as_chaining(self):
        data = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
        data = data[(data.name == "Antarctica")]
        topo = topojson.Topology(data, prequantize=1e6, topology=True)
        topos = topo.topoquantize(1e5).to_dict()
        self.assertEqual("transform" in topos.keys(), True)

    def test_topology_to_svg(self):
        data = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
        data = data[(data.name == "Antarctica")]
        topo = topojson.Topology(data, prequantize=1e6, topology=True)
        topo.to_svg()
        self.assertEqual("transform" in topos.keys(), True)
