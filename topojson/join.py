from .utils.dispatcher import methdispatch
from .extract import Extract
import json
from shapely import geometry 
import geojson

class Join:
    """
    identify junctions (intersection points).
    """

    def __init__(self):
        # initatie topology items
        self.junctions = []

    def join(self, data):
        """
        start join function
        
        to find shared paths:
        https://shapely.readthedocs.io/en/stable/manual.html#shared-paths
        
        to set up a R-tree:
        and https://shapely.readthedocs.io/en/stable/manual.html#str-packed-r-tree
        """
        print(data)
        data['junctions'] = data['coordinates']
        return data        