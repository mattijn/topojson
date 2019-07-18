import json
import unittest
from topojson.core.extract import Extract
from shapely import geometry
import geopandas
import geojson
from topojson.utils import TopoOptions


class TestOptions(unittest.TestCase):
    # test winding order using TopoOptions object
    def test_winding_order_TopoOptions(self):
        from topojson.utils import TopoOptions

        data = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
        data = data[(data.name == "South Africa")]

        topo_options = TopoOptions(winding_order="CW_CCW")
        topo = Extract(data, options=topo_options).to_dict()
        self.assertEqual(len(topo["objects"]), 1)
        self.assertEqual(isinstance(topo["options"], TopoOptions), True)

    # test winding order using kwarg variables
    def test_winding_order_kwarg_vars(self):

        data = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
        data = data[(data.name == "South Africa")]

        topo = Extract(data, options={"winding_order": "CW_CCW"}).to_dict()
        self.assertEqual(len(topo["objects"]), 1)
        self.assertEqual(isinstance(topo["options"], TopoOptions), True)
