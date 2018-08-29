from .utils.dispatcher import methdispatch
import json
from shapely import geometry 
import geojson

class Extract:
    """
    decompose shapes into lines and rings.
    """

    def __init__(self):
        # initatie topology items
        self.lines = []
        self.rings = []
        self.coordinates = []
        self.objects = {}  
        self._geomcollection_counter = 0  

    @methdispatch
    def serialize_geom_type(self, geom):
        """
        This function handles the different types of a geojson object.
        Each type is registerd as its own function and called when found, if 
        none of the types match the input geom the current function is
        executed. 

        Currently the following geometry types are registered:
        - LineString
        - MultiLineString
        - Polygon
        - MultiPolygon
        - Point
        - MultiPoint
        - GeometryCollection

        In our case this will return an error as the input geom did not 
        match any of the required types.
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
        obj = self._obj
        idx_arc = len(self.lines) - 1
        if 'arcs' not in obj:
            obj['arcs'] = [] 
            
        obj['arcs'].append(idx_arc)
        obj.pop('coordinates', None)
        
        #self.objects[key] = obj

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
        obj = self._obj
        if 'arcs' not in obj:
            obj['arcs'] = []
            
        obj['arcs'].append(idx_arc)
        obj.pop('coordinates', None)
        
        #self.objects[key] = obj

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
        obj = self._obj
        if 'arcs' not in obj:
            obj['arcs'] = obj['coordinates']
        obj.pop('coordinates', None)

    @serialize_geom_type.register(geometry.GeometryCollection)
    def extract_geometrycollection(self, geom):
        """
        *geom* type is GeometryCollection instance.
        """
        obj = self._data[self._key]
        self._geomcollection_counter += 1
        self._records_collection = len(geom)

        # iterate over the parsed shape(geom) 
        # the original data objects is set as self._obj
        # the following lines can catch a GeometryCollection two levels deep
        # improvements on this are welcome
        for idx, geom in enumerate(geom):
            # if geom is GeometryCollection, collect geometries within collection on right level
            if isinstance(geom, geometry.GeometryCollection):
                self._records_collection = len(geom)
                if self._geomcollection_counter == 1:
                    self._obj = obj['geometries']
                    self._geom_level_1 = idx
                if self._geomcollection_counter == 2:
                    self._obj = obj['geometries'][self._geom_level_1]['geometries']  
            
            # geom is another registered geometry, determine location within collection
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
            self.serialize_geom_type(geom)
        
    @serialize_geom_type.register(geojson.FeatureCollection)
    def extract_featurecollection(self, geom):
        """
        *geom* type is FeatureCollection instance.
        """
        # convert FeatureCollection into a GeometryCollection
        obj = self._obj
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
        
        # new data object is created, throw the geometries back to extract()
        self.extract(data)

    @serialize_geom_type.register(geojson.Feature)
    def extract_feature(self, geom):
        """
        *geom* type is Feature instance.        
        """
        obj = self._obj
        
        # A GeoJSON Feature is mapped to a GeometryCollection
        obj['type'] = 'GeometryCollection'
        obj['geometries'] = [obj['geometry']]
        obj.pop('geometry', None)

        geom = geometry.shape(obj)
        self.serialize_geom_type(geom)
        
    def extract(self, data):
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

        self._data = data
        self._prev_type = ''

        # iterate over the input dictionary or geojson object
        for key in self._data:
            # based on the geom type the right function is serialized
            self._key = key
            self._obj = self._data[self._key]

            # determine if type is a feature or collections of features
            # otherwise treat as geometric objects
            try:
                geom = geometry.shape(self._obj)
            except ValueError:
                geom = geojson.loads(geojson.dumps(self._obj))
                
            #print(geom)
            self.serialize_geom_type(geom)
            
            # reset geom collection counter and level
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