from .utils.dispatcher import methdispatch
import json
from shapely import geometry 
from shapely import speedups
import geojson
import copy
import gc
import logging

if speedups.available:
    speedups.enable()


class _Extract:
    """
    decompose shapes into lines and rings.
    """
    def __init__(self):
        # initatie topology items
        self.lines = []
        self.rings = []
        self.coordinates = []
        self.geomcollection_counter = 0  
        self.invalid_geoms = 0

    @methdispatch
    def serialize_geom_type(self, geom):
        """
        This function handles the different types of a geojson object.
        Each type is registerd as its own function and called when found, 
        if none of the types match the input geom the current function is
        executed. 

        Currently the following geometry types are registered:
        - shapely.geometry.LineString
        - shapely.geometry.MultiLineString
        - shapely.geometry.Polygon
        - shapely.geometry.MultiPolygon
        - shapely.geometry.Point
        - shapely.geometry.MultiPoint
        - shapely.geometry.GeometryCollection
        - geojson.Feature
        - geojson.FeatureCollection

        Any non-registered geometry wil return as an error that cannot be mapped.
        """
        return print('error: {} cannot be mapped'.format(geom))

    @serialize_geom_type.register(geometry.LineString)
    def extract_line(self, geom):
        """
        *geom* type is LineString instance.
        """
        arc = list(geom.coords)
        self.coordinates.extend(arc)
        self.lines.append(geom)

        # get index of last added item and store as arc
        obj = self.obj
        idx_arc = len(self.lines) - 1
        if 'arcs' not in obj:
            obj['arcs'] = [] 
            
        obj['arcs'].append(idx_arc)
        obj.pop('coordinates', None)

    @serialize_geom_type.register(geometry.MultiLineString)
    def extract_multiline(self, geom):
        """
        *geom* type is MultiLineString instance. 
        """
        for line in geom:
            self.extract_line(line)

    @serialize_geom_type.register(geometry.Polygon)
    def extract_ring(self, geom):
        """
        *geom* type is Polygon instance.
        """
        arc = list(geom.exterior.coords)
        self.coordinates.extend(arc)
        self.rings.append(geom)

        # get index of last added item and store as arcs
        idx_arc = len(self.rings) - 1
        obj = self.obj
        if 'arcs' not in obj:
            obj['arcs'] = []
            
        obj['arcs'].append(idx_arc)
        obj.pop('coordinates', None)

    @serialize_geom_type.register(geometry.MultiPolygon)
    def extract_multiring(self, geom):
        """
        *geom* type is MultiPolygon instance. 
        """
        for ring in geom:
            self.extract_ring(ring)

    @serialize_geom_type.register(geometry.MultiPoint)
    @serialize_geom_type.register(geometry.Point)
    def extract_point(self, geom):
        """
        *geom* type is Point or MultiPoint instance.
        coordinates are directly passed to arcs
        """
        obj = self.obj
        if 'arcs' not in obj:
            obj['arcs'] = obj['coordinates']
        obj.pop('coordinates', None)

    @serialize_geom_type.register(geometry.GeometryCollection)
    def extract_geometrycollection(self, geom):
        """
        *geom* type is GeometryCollection instance.
        """
        obj = self.data[self.key]
        self.geomcollection_counter += 1
        self.records_collection = len(geom)

        # iterate over the parsed shape(geom) 
        # the original data objects is set as self._obj
        # the following lines can catch a GeometryCollection two levels deep
        # improvements on this are welcome
        for idx, geom in enumerate(geom):
            # if geom is GeometryCollection, collect geometries within collection on right level
            if isinstance(geom, geometry.GeometryCollection):
                self.records_collection = len(geom)
                if self.geomcollection_counter == 1:
                    self.obj = obj['geometries']
                    self.geom_level_1 = idx
                if self.geomcollection_counter == 2:
                    self.obj = obj['geometries'][self.geom_level_1]['geometries']  
            
            # geom is NOT a GeometryCollection, determine location within collection
            else:
                if self.geomcollection_counter == 1:
                    self.obj = obj['geometries'][idx]
                    # if last record in collection is parsed set collection counter one level up
                    if idx == self.records_collection - 1:
                        self.geomcollection_counter += -1                    
                if self.geomcollection_counter == 2:
                    self.obj =  obj['geometries'][self.geom_level_1]['geometries'][idx]
                    # if last record in collection is parsed set collection counter one level up
                    if idx == self.records_collection - 1:
                        self.geomcollection_counter += -1                    

            # set type for next loop
            self.serialize_geom_type(geom)
        
    @serialize_geom_type.register(geojson.FeatureCollection)
    def extract_featurecollection(self, geom):
        """
        *geom* type is FeatureCollection instance.
        """
        # convert FeatureCollection into a GeometryCollection
        obj = self.obj
        obj['type'] = 'GeometryCollection'
        obj['geometries'] = {}        
        zfill_value = len(str(len(obj['features'])))

        # each Feature becomes a new GeometryCollection
        for idx, feature in enumerate(obj['features']):
            # A GeoJSON Feature is mapped to a GeometryCollection
            feature['type'] = 'GeometryCollection'
            feature['geometries'] = [feature['geometry']]
            feature.pop('geometry', None)
            obj['geometries']['feature_{}'.format(str(idx).zfill(zfill_value))] = feature
        # all Features parsed into GeometryCollections, so drop features array
        obj.pop('features', None)       
        data = obj['geometries']
        
        # new data object is created, throw the geometries back to main()
        self.worker(data)

    @serialize_geom_type.register(geojson.Feature)
    def extract_feature(self, geom):
        """
        *geom* type is Feature instance.        
        """
        
        obj = self.obj
        
        # A GeoJSON Feature is mapped to a GeometryCollection
        obj['type'] = 'GeometryCollection'
        obj['geometries'] = [obj['geometry']]
        obj.pop('geometry', None)

        geom = geometry.shape(obj)
        if not geom.is_valid:
            self.invalid_geoms += 1
            del self.data[self.key]
            return        

        self.serialize_geom_type(geom)
        
        
    def worker(self, data):
        """"
        Extracts the lines and rings from the specified hash of geometry objects.

        Returns an object with three new properties:

        * coordinates - shared buffer of [x, y] coordinates
        * lines - lines extracted from the hash, of the form [start, end], as shapely objects
        * rings - rings extracted from the hash, of the form [start, end], as shapely objects

        For each line or polygon geometry in the input hash, including nested
        geometries as in geometry collections, the `coordinates` array is replaced
        with an equivalent `arcs` array that, for each line (for line string
        geometries) or ring (for polygon geometries), points to one of the above
        lines or rings.

        Points geometries are not collected within the new properties, but are placed directly
        into the `arcs` array within each object.
        """

        self.data = data

        # iterate over the input dictionary or geojson object
        # use list since https://stackoverflow.com/a/11941855
        for key in list(self.data):
            # based on the geom type the right function is serialized
            self.key = key
            self.obj = self.data[self.key]

            # determine if type is a feature or collections of features
            # otherwise treat as geometric objects
            try:
                geom = geometry.shape(self.obj)
                # object can be mapped, but may not be valid. remove invalid objects and continue
                if not geom.is_valid:
                    self.invalid_geoms += 1
                    del self.data[self.key]
                    continue                
            except ValueError:
                geom = geojson.loads(geojson.dumps(self.obj))
                
            #print(geom)
            self.serialize_geom_type(geom)
            
            # reset geom collection counter and level
            self.geomcollection_counter = 0
            self.geom_level_1 = 0
        
        topo = {
            "type": "Topology",
            "coordinates": self.coordinates,
            "lines": self.lines,
            "rings": self.rings,
            "objects": self.data
        }
        
        # show the number of invalid geometries have been removed if any
        if self.invalid_geoms > 0:
            logging.warning('removed {} invalid geometric object{}'.format(
                self.invalid_geoms, '' if self.invalid_geoms == 1 else 's'))        
        
        return topo
    
def _extracter(data):
    data = copy.deepcopy(data)
    Extract = _Extract()
    e = Extract.worker(data)
    return e