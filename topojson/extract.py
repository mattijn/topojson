from functools import singledispatch, update_wrapper
from copy import deepcopy
import json
from shapely.geometry import shape, LineString, MultiLineString, Polygon, MultiPolygon, GeometryCollection

def methdispatch(func):
    """
    create wrapper around singledispatch to be used for 
    class instances
    """
    dispatcher = singledispatch(func)
    def wrapper(*args, **kw):
        return dispatcher.dispatch(args[1].__class__)(*args, **kw)
    wrapper.register = dispatcher.register
    update_wrapper(wrapper, dispatcher)
    return wrapper

class Extract:

    def __init__(self):
        # initatie topology items
        self.lines = []
        self.rings = []
        self.coordinates = []
        self.objects = {}    

    @methdispatch
    def serialize_geom_type(self, geometry, obj, key):
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
    def extract_line(self, geometry, obj, key):
        """
        *geometry* type is LineString instance.
        """
        arc = list(geometry.coords)
        self.coordinates.extend(arc)
        self.lines.append(geometry)

        # get index of last added item and store as arc
        idx_arc = len(self.lines) - 1
        if 'arcs' not in obj:
            obj['arcs'] = [] 
            
        obj['arcs'].append(idx_arc)
        obj.pop('coordinates', None)
        
        self.objects[key] = obj

    @serialize_geom_type.register(MultiLineString)
    def extract_multiline(self, geometry, obj, key):
        """
        *geometry* type is MultiLineString instance. 
        """
        for line in geometry:
            self.extract_line(line, obj, key)

    @serialize_geom_type.register(Polygon)
    def extract_ring(self, geometry, obj, key):
        """
        *geometry* type is Polygon instance.
        """
        arc = list(geometry.exterior.coords)
        self.coordinates.extend(arc)
        self.rings.append(geometry)

        # get index of last added item and store as arcs
        idx_arc = len(self.rings) - 1
        if 'arcs' not in obj:
            obj['arcs'] = []
            
        obj['arcs'].append(idx_arc)
        obj.pop('coordinates', None)
        
        self.objects[key] = obj

    @serialize_geom_type.register(MultiPolygon)
    def extract_multiring(self, geometry, obj, key):
        """
        *geometry* type is MultiPolygon instance. 
        """
        for ring in geometry:
            self.extract_ring(ring, obj, key)

    @serialize_geom_type.register(GeometryCollection)
    def extract_geometry(self, geometry, obj, key):
        """
        *geometry* type is GeometryCollection instance.
        """
        print('obj: {}'.format(obj))
        
#         for key in obj:
#             # based on the geometry type the right function is serialized
#             obj = data[key]
#             geometry = shape(obj)
            
        for idx, geom in enumerate(geometry):
            print(idx, geom)
            if geom.type == 'GeometryCollection':
                obj = obj['geometries'][idx]
            self.serialize_geom_type(geom, obj, key)

    def extract(self, data):
        data = deepcopy(data)

        # iterate over the input dictionary or geojson object
        for key in data:
            # based on the geometry type the right function is serialized
            obj = data[key]
            geometry = shape(obj)

            print(geometry)
            self.serialize_geom_type(geometry, obj, key)
            
#             # get index of last added item and store as arc
#             objects[key] = obj

        json_topology = {
            "type": "Topology",
            "coordinates": self.coordinates,
            "lines": self.lines,
            "rings": self.rings,
            "objects": self.objects
        }
        return json_topology