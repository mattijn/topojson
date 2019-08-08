import json
import unittest
from shapely import geometry
import geopandas
import geojson
from topojson.utils import TopoOptions
import topojson


class TestOptions(unittest.TestCase):
    # test winding order using TopoOptions object
    def test_winding_order_TopoOptions(self):
        from topojson.utils import TopoOptions

        data = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
        data = data[(data.name == "South Africa")]

        topo_options = TopoOptions(winding_order="CW_CCW")
        topo = topojson.Topology(data, options=topo_options).to_dict()
        self.assertEqual(len(topo["objects"]), 1)
        self.assertEqual(isinstance(topo["options"], TopoOptions), True)

    # test winding order using kwarg variables
    def test_winding_order_kwarg_vars(self):

        data = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
        data = data[(data.name == "South Africa")]

        topo = topojson.Topology(data, options={"winding_order": "CW_CCW"}).to_dict()
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

        no_topo = topojson.Topology(data, options={"topology": False}).to_dict()
        topo = topojson.Topology(data, options={"topology": True}).to_dict()

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

        topo = topojson.Topology(
            data, options={"topology": False, "prequantize": 1e4}
        ).to_dict()
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

        topo = topojson.Topology(
            data, options={"topology": False, "prequantize": 1e4, "delta_encode": True}
        ).to_dict()
        self.assertEqual("transform" in topo.keys(), True)

    # test toposimplify
    def test_toposimplify_including_prequantization(self):
        data = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
        data = data[(data.name == "Antarctica")]
        topo = topojson.Topology(
            data, options={"prequantize": True, "simplifypackage": "simplification"}
        )
        topos = topo.toposimplify(2)
