from .utils.dispatcher import methdispatch
from copy import deepcopy
import json
from shapely.geometry import shape, LineString, MultiLineString, Polygon, MultiPolygon, GeometryCollection

class Extract:

    def __init__(self):
        # initatie topology items
        self.lines = []
        self.rings = []
        self.coordinates = []
        self.objects = {}  
        self._geomcollection_counter = 0  

    @methdispatch
    def serialize_geom_type(self, geometry):
        """
        This function handles the different types of a geojson object.
        Each type is registerd as its own function and called when found, if 
        none of the types match the input geometry the current function is
        executed. 

        In our case this will return an error as the input geometry did not 
        match any of the required types.
        """
        return print('error: {} cannot be mapped'.format(geometry))

    @serialize_geom_type.register(LineString)
    def extract_line(self, geometry):
        """
        *geometry* type is LineString instance.
        """
        arc = list(geometry.coords)
        self.coordinates.extend(arc)
        self.lines.append(geometry)

        # get index of last added item and store as arc
        obj = self._obj
        idx_arc = len(self.lines) - 1
        if 'arcs' not in obj:
            obj['arcs'] = [] 
            
        obj['arcs'].append(idx_arc)
        obj.pop('coordinates', None)
        
        #self.objects[key] = obj

    @serialize_geom_type.register(MultiLineString)
    def extract_multiline(self, geometry):
        """
        *geometry* type is MultiLineString instance. 
        """
        for line in geometry:
            self.extract_line(line)

    @serialize_geom_type.register(Polygon)
    def extract_ring(self, geometry):
        """
        *geometry* type is Polygon instance.
        """
        arc = list(geometry.exterior.coords)
        self.coordinates.extend(arc)
        self.rings.append(geometry)

        # get index of last added item and store as arcs
        idx_arc = len(self.rings) - 1
        obj = self._obj
        if 'arcs' not in obj:
            obj['arcs'] = []
            
        obj['arcs'].append(idx_arc)
        obj.pop('coordinates', None)
        
        #self.objects[key] = obj

    @serialize_geom_type.register(MultiPolygon)
    def extract_multiring(self, geometry):
        """
        *geometry* type is MultiPolygon instance. 
        """
        for ring in geometry:
            self.extract_ring(ring)

    @serialize_geom_type.register(GeometryCollection)
    def extract_geometry(self, geometry):
        """
        *geometry* type is GeometryCollection instance.
        """
        obj = self._data[self._key]
        self._geomcollection_counter += 1
        print('obj: {}'.format(obj))

        self._records_collection = len(geometry)
        for idx, geom in enumerate(geometry):
            print(idx, geom)
            # catch nested geometry collection
            if geom.type == 'GeometryCollection':
                self._records_collection = len(geom)
                if self._geomcollection_counter == 1:
                    self._obj = obj['geometries']
                    self._geom_level_1 = idx
                if self._geomcollection_counter == 2:
                    self._obj = obj['geometries'][self._geom_level_1]['geometries']  
            # if not parse to right object in data
            else:
                if self._geomcollection_counter == 1:
                    self._obj =  obj['geometries'][idx]
                    # if last record in collection is parsed set collection counter one level up
                    if idx == self._records_collection - 1:
                        self._geomcollection_counter += -1                    
                if self._geomcollection_counter == 2:
                    self._obj =  obj['geometries'][self._geom_level_1]['geometries'][idx]
                    # if last record in collection is parsed set collection counter one level up
                    if idx == self._records_collection - 1:
                        self._geomcollection_counter += -1                    

            # set type for next loop
            self._prev_type = geom.type
            self.serialize_geom_type(geom)
            

    def extract(self, data):
        self._data = deepcopy(data)
        # init geomcol counter
        self._geomcollection_counter = 0
        self._prev_type = ''

        # iterate over the input dictionary or geojson object
        for key in self._data:
            # based on the geometry type the right function is serialized
            self._key = key
            self._obj = self._data[self._key]
            geometry = shape(self._obj)

            print(geometry)
            self.serialize_geom_type(geometry)
            
            # reset geometry collection counter and level
            self._geomcollection_counter = 0
            self._geom_level_1 = 0
            self._prev_type = ''

        json_topology = {
            "type": "Topology",
            "coordinates": self.coordinates,
            "lines": self.lines,
            "rings": self.rings,
            "objects": self._data
        }
        return json_topology