import json
import copy
import logging
import pprint
import numpy as np
from shapely import geometry
from ..utils import instance
from ..utils import serialize_as_svg
from ..utils import TopoOptions
from ..ops import winding_order
from ..ops import ignore_shapely2_warnings

try:
    from shapely.errors import GeometryTypeError
except ImportError:
    GeometryTypeError = ValueError


class Extract(object):
    """
    This class targets the following objectives:
    1. Detection of geometrical type of the object
    2. Extraction of linestrings from the object

    The extract function is the first step in the topology computation.
    The following sequence is adopted:
    1. extract
    2. join
    3. cut
    4. dedup
    5. hashmap

    For each line or polygon geometry in the input hash, including nested
    geometries as in geometry collections, the `coordinates` array is replaced
    with an equivalent `"coordinates"` array that points to one of the
    linestrings as indexed in `bookkeeping_geoms` and stored in `linestrings`.

    For Points geometries count the same, but are stored in `coordinates` and
    referenced in `bookkeeping_coords`.

    Parameters
    ----------
    data : _any_ geometric type
        Different types of a geometry object, originating from shapely, geojson,
        geopandas and dictionary or list of objects that contain a `__geo_interface__`.

    Returns
    -------
    dict
        object created including the keys `type`, `linestrings`, `coordinates` `bookkeeping_geoms`, `bookkeeping_coords`, `objects`
    """

    def __init__(self, data, options={}):
        # initiation topology options
        if isinstance(options, TopoOptions):
            self.options = options
        else:
            self.options = TopoOptions(options)
        self._bookkeeping_geoms = []
        self._bookkeeping_coords = []
        self._linestrings = []
        self._coordinates = []
        self._geomcollection_counter = 0
        self._is_single = True
        self._invalid_geoms = 0
        self._tried_geojson = False
        self._is_multi_geom = False
        self._geom_offset = 0

        self.output = self._extractor(data)

    def __repr__(self):
        return "Extract(\n{}\n)".format(pprint.pformat(self.output))

    def to_dict(self):
        """
        Convert the Extract object to a dictionary.
        """
        topo_object = copy.copy(self.output)
        topo_object["options"] = vars(self.options)
        return topo_object

    def to_svg(self, separate=False):
        """
        Display the linestrings as SVG.

        Parameters
        ----------
        separate : boolean
            If `True`, each of the linestrings will be displayed separately.
            Default is `False`
        """
        serialize_as_svg(self.output, separate, include_junctions=False)

    def _extractor(self, data):
        """
        Entry point for the class Extract.

        The extract function is the first step in the topology computation.
        The following sequence is adopted:
        1. extract
        2. join
        3. cut
        4. dedup
        5. hashmap

        Returns an object including two new properties:

        * linestrings - linestrings extracted from the hash, of the form [start, end],
        as shapely objects
        * bookkeeping_geoms - record array storing index numbers of linestrings
        used in each object.

        For each line or polygon geometry in the input hash, including nested
        geometries as in geometry collections, the `coordinates` array is replaced
        with an equivalent `"coordinates"` array that points to one of the
        linestrings as indexed in `bookkeeping_geoms` and stored in `linestrings`.

        For Points geometries count the same, but are stored in `coordinates` and
        referenced in `bookkeeping_coords`.
        """

        self._data = data
        self._serialize_geom_type(data)

        # prepare to return object
        data = {
            "type": "Topology",
            "linestrings": self._linestrings,
            "coordinates": self._coordinates,
            "bookkeeping_geoms": self._bookkeeping_geoms,
            "bookkeeping_coords": self._bookkeeping_coords,
            "objects": self._data,
        }

        # show the number of invalid geometries have been removed if any
        if self._invalid_geoms > 0:
            logging.warning(
                "removed {} invalid geometric object{}".format(
                    self._invalid_geoms, "" if self._invalid_geoms == 1 else "s"
                )
            )
            self._invalid_geoms = 0
        if self._tried_geojson:
            logging.warning(
                "Objects might be recognized if python package `geojson` is installed."
            )
        return data

    # @singledispatch_class
    def _serialize_geom_type(self, geom):
        """
        This function handles the different types that can occur within known
        geographical data. Each type is registered as its own function and called when
        found, if none of the types match the input geom the current function is
        executed.

        The following geometry types are registered:
        - shapely.geometry.LineString
        - shapely.geometry.MultiLineString
        - shapely.geometry.Polygon
        - shapely.geometry.MultiPolygon
        - shapely.geometry.Point
        - shapely.geometry.MultiPoint
        - shapely.geometry.GeometryCollection
        - fiona.Collection
        - geojson.Feature
        - geojson.FeatureCollection
        - geopandas.GeoDataFrame
        - geopandas.GeoSeries
        - dict of objects that provide a __geo_interface__
        - list of objects that provide a __geo_interface__
        - list of geopandas.GeoDataFrames
        - object that provide a __geo_interface__
        - TopoJSON dict
        - TopoJSON string
        - GeoJSON string

        Any non-registered geometry wil return as an error that cannot be mapped.
        """
        if instance(geom) == "LineString":
            self._extract_line(geom)
        elif instance(geom) == "MultiLineString":
            self._extract_multiline(geom)
        elif instance(geom) == "Polygon":
            self._extract_ring(geom)
        elif instance(geom) == "MultiPolygon":
            self._extract_multiring(geom)
        elif instance(geom) == "Point":
            self._extract_point(geom)
        elif instance(geom) == "MultiPoint":
            self._extract_multipoint(geom)
        elif instance(geom) == "GeometryCollection":
            self._extract_geometrycollection(geom)
        elif instance(geom) == "FeatureCollection":
            self._extract_featurecollection(geom)
        elif instance(geom) == "Feature":
            if type(geom).__module__ == "fiona.model":
                self._extract_fiona_feature(geom)
            else:
                self._extract_feature(geom)
        elif instance(geom) == "Collection":
            self._extract_fiona_collection(geom)
        elif instance(geom) == "GeoDataFrame":
            self._extract_geopandas_geodataframe(geom)
        elif instance(geom) == "GeoSeries":
            self._extract_geopandas_geoseries(geom)
        elif instance(geom) == "list":
            self._extract_list(geom)
        elif instance(geom) == "str":
            self._extract_string(geom)
        elif instance(geom) == "dict":
            self._extract_dictionary(geom)
        else:
            # if no type is recognized: maybe the object has a __geo_interface__
            if hasattr(self._data, "__geo_interface__"):
                data = copy.deepcopy(self._data.__geo_interface__)
                # convert type _Array or array to list
                for key in data.keys():
                    if str(type(data[key]).__name__).startswith(("_Array", "array")):
                        data[key] = data[key].tolist()
                # convert (nested) tuples to lists
                data = json.loads(json.dumps(data))
                self._data = [data]
                self._extract_list([data])
            else:
                return print("error: {} cannot be mapped".format(geom))

    def _extract_line(self, geom):
        """
        This function extracts a LineString instance.

        Parameters
        ----------
        geom : shapely.geometry.LineString
            LineString instance
        """

        # only process non-single geometries:
        if self._is_single:
            return self._extractor([geom])
        # only process non-empty geometries
        if not geom.is_empty:
            idx_bk = len(self._bookkeeping_geoms)
            idx_ls = len(self._linestrings)
            # record index and store linestring geom
            self._bookkeeping_geoms.append([idx_ls])
            self._linestrings.append(geom)

            # track record in object as well
            obj = self._obj
            if "arcs" not in obj:
                obj["arcs"] = []
            obj["arcs"].append(idx_bk)
            obj.pop("coordinates", None)
        # when geometry is empty, set arcs key to None
        else:
            obj = self._obj
            obj["arcs"] = None
            obj.pop("coordinates", None)
            # self._extract_point(geom)

    def _extract_multiline(self, geom):
        """
        This function extracts a MultiLineString instance.

        Parameters
        ----------
        geom : shapely.geometry.MultiLineString
            MultiLineString instance
        """

        # only process non-single geometries:
        if self._is_single:
            data = [geom]
            return self._extractor(data)
        for line in geom.geoms:
            self._extract_line(line)

    def _extract_ring(self, geom):
        """
        This function extracts a Polygon instance.

        Parameters
        ----------
        geom : shapely.geometry.Polygon
            Polygon instance
        """

        # only process non-single geometries:
        if self._is_single:
            return self._extractor([geom])
        idx_bk = len(self._bookkeeping_geoms)
        idx_ls = len(self._linestrings)

        # orient the outer polygon clockwise and the inner polygon counterclockwise
        # to conform TopoJSON standard (CW_CCW)
        if self.options.winding_order is not None:
            geom = winding_order(geom=geom, order=self.options.winding_order)
        boundary = geom.boundary
        # catch ring with holes
        if isinstance(boundary, geometry.MultiLineString):
            # record index as list of items
            # and store each linestring geom
            lst_idx = list(range(idx_ls, idx_ls + len(boundary.geoms)))
            self._bookkeeping_geoms.append(lst_idx)
            for ls in boundary.geoms:
                self._linestrings.append(ls)
        else:
            # record index and store single linestring geom
            self._bookkeeping_geoms.append([idx_ls])
            self._linestrings.append(boundary)
        # track record in object as well
        obj = self._obj
        if "arcs" not in obj:
            obj["arcs"] = []
        obj["arcs"].append(idx_bk)
        obj.pop("coordinates", None)

    def _extract_multiring(self, geom):
        """
        This function extracts a MultiPolygon instance.

        Parameters
        ----------
        geom : shapely.geometry.MultiPolygon
            MultiPolygon instance
        """

        # only process non-single geometries:
        if self._is_single:
            return self._extractor([geom])
        for ring in geom.geoms:
            self._extract_ring(ring)

    def _extract_point(self, geom):
        """
        This function extracts a Point instance.
        coordinates are directly passed to "coordinates"

        Parameters
        ----------
        geom : shapely.geometry.Point
            Point instance
        """

        # only process non-single geometries:
        if self._is_single:
            return self._extractor([geom])
        # only process non-empty point geometries
        if not geom.is_empty:
            idx_bk = len(self._bookkeeping_coords)
            idx_pt = len(self._coordinates)
            # record index and store linestring geom
            self._bookkeeping_coords.append([idx_pt])
            self._coordinates.append(np.array(geom.coords))

            # track record in object as well
            obj = self._obj
            if "reset_coords" not in obj:
                obj["coordinates"] = []
                obj["reset_coords"] = True
            obj["coordinates"].append(idx_bk)

    def _extract_multipoint(self, geom):
        """
        This function extracts a MultiPoint instance.

        Parameters
        ----------
        geom : shapely.geometry.MultiPoint
            MultiPoint instance
        """

        # only process non-single geometries:
        if self._is_single:
            return self._extractor([geom])
        for point in geom.geoms:
            self._extract_point(point)

    def _extract_geometrycollection(self, geom):
        """
        This function extracts a GeometryCollection instance.

        Parameters
        ----------
        geom : shapely.geometry.GeometryCollection
            GeometryCollection instance
        """

        self._is_single = False
        if not hasattr(self, "_key"):
            obj = geom.__geo_interface__
            self._key = "feature_0"
            self._data = {self._key: obj}
        else:
            obj = self._data[self._key]
        # obj = self._data[self._key]
        self._geomcollection_counter += 1
        self.records_collection = len(geom.geoms)

        # iterate over the parsed shape(geom)
        # the original data objects is set as self._obj
        # the following lines can catch a GeometryCollection until two levels deep
        # improvements on this are welcome
        for idx, geo in enumerate(geom.geoms):
            # if geom is GeometryCollection, collect geometries within collection
            # on right level
            if isinstance(geo, geometry.GeometryCollection):
                self.records_collection = len(geo.geoms)
                if self._geomcollection_counter == 1:
                    self._obj = obj["geometries"]
                    self._geom_level_1 = idx
                elif self._geomcollection_counter == 2:
                    self._obj = obj["geometries"][self._geom_level_1]["geometries"]
            # geom is NOT a GeometryCollection, determine location within collection
            else:
                if self._geomcollection_counter == 1:
                    self._obj = obj["geometries"][idx]
                    # if last record in collection is parsed set collection counter
                    # one level up
                    if idx == self.records_collection - 1:
                        self._geomcollection_counter += -1
                elif self._geomcollection_counter == 2:
                    self._obj = obj["geometries"][self._geom_level_1]["geometries"][idx]
                    # if last record in collection is parsed set collection counter
                    # one level up
                    if idx == self.records_collection - 1:
                        self._geomcollection_counter += -1
            # set type for next loop
            self._serialize_geom_type(geo)

    def _extract_featurecollection(self, geom):
        """
        This function extracts a FeatureCollection instance.

        Parameters
        ----------
        geom : geojson.FeatureCollection
            FeatureCollection instance
        """

        # convert FeatureCollection into a dict of features
        if not hasattr(self, "_obj"):
            geom = copy.deepcopy(geom)
            obj = geom
            self._obj = geom
        else:
            obj = self._obj
        data = {}
        zfill_value = len(str(len(obj["features"])))

        # each Feature becomes a new GeometryCollection
        for idx, feature in enumerate(obj["features"]):
            # A GeoJSON Feature is mapped to a GeometryCollection
            # => directly mapped to specific geometry, so that to save the attributes
            feature["type"] = feature["geometry"]["type"]

            feature_dict = {
                **(feature.get("properties") if feature.get("properties") else {}),
                **{"geometry": geometry.shape(feature["geometry"])},
            }

            if feature["type"] == "GeometryCollection":
                feature_dict["geometries"] = feature["geometry"]["geometries"]

            if self.options.ignore_index or not feature.get("id"):
                data["feature_{}".format(str(idx).zfill(zfill_value))] = feature_dict
            else:
                data[feature.get("id")] = feature_dict  # feature

        # check for overwritten duplicate keys
        if len(data) < len(obj["features"]):
            msg = "index in data duplicated, use `ignore_index=True` to overwrite index"
            raise IndexError(msg)

        # new data dictionary is created, throw the geometries back to main()
        self._is_single = False
        self._extractor(data)

    def _extract_feature(self, geom):
        """
        This function extracts a Feature instance.

        Parameters
        ----------
        geom : geojson.Feature
            Feature instance
        """

        if not hasattr(self, "_obj"):
            obj = geom
            self._key = "feature_0"
            self._data = {self._key: geom}
        else:
            obj = self._obj
        # A GeoJSON Feature is mapped to a GeometryCollection
        obj["type"] = "GeometryCollection"
        obj["geometries"] = [obj["geometry"]]
        obj.pop("geometry", None)

        geom = geometry.shape(obj)
        if not geom.is_valid:
            self._invalid_geoms += 1
            del self._data[self._key]
            return
        self._is_single = False
        self._serialize_geom_type(geom)

    def _extract_fiona_collection(self, geom):
        """
        This function extracts a Fiona Collection.

        Parameters
        ----------
        geom : fiona.Collection
            Collection instance
        """
        try:
            import geojson
        except ImportError:
            raise ImportError(
                "To parse a `fiona.Collection`, you'll need the python package `geojson`"
            )
        # convert Fiona Collection into a GeoJSON Feature Collection
        # Use geojson.Feature to properly convert Fiona features to GeoJSON format
        features = [
            geojson.Feature(
                geometry=feat["geometry"], properties=dict(feat["properties"])
            )
            for feat in geom
        ]
        geom = geojson.FeatureCollection(features)
        # re-parse feat_col in _extractor()
        self._is_single = False
        self._extractor(geom)

    def _extract_fiona_feature(self, geom):
        """
        This function extracts a Fiona Feature.

        Parameters
        ----------
        geom : fiona.model.Feature
            Feature instance
        """
        try:
            import geojson
        except ImportError:
            raise ImportError(
                "To parse a `fiona.model.Feature`, you'll need the python package `geojson`"
            )
        # convert Fiona Feature into a GeoJSON Feature
        geojson_feat = geojson.Feature(
            geometry=geom["geometry"], properties=dict(geom["properties"])
        )
        # re-parse feature in _extractor()
        self._is_single = False
        self._extractor(geojson_feat)

    def _extract_geopandas_geodataframe(self, geom):
        """*geom* type is GeoDataFrame instance.

        Parameters
        ----------
        geom : geopandas.GeoDataFrame
            GeoDataFrame instance
        """

        if geom.crs:
            self._defined_crs_source = geom.crs
        # DataFrame index must be unique for orient='index'.
        if geom.index.is_unique:
            self._data = geom.to_dict(orient="index")
        else:
            self._data = dict(enumerate(geom.to_dict(orient="records")))
        self._extract_dictionary(self._data)

    def _extract_geopandas_geoseries(self, geom):
        """
        This function extracts a GeoSeries instance.

        Parameters
        ----------
        geom : geopandas.GeoSeries
            GeoSeries instance
        """

        self._data = geom.to_dict()
        self._extract_dictionary(self._data)

    def _extract_list(self, geom):
        """
        This function extracts a List instance.

        Parameters
        ----------
        geom : list
            List instance
        """
        # check if there are multiple entries in the `object_name` in settings.
        # currently only supports multiple GeoDataFrames as input entries
        if len(self.options.object_name) > 1:
            # list consist of objects
            if len(self.options.object_name) != len(geom):
                raise LookupError(
                    "the number of data objects does not match the number of object_name"
                )
            geom = [
                subgeom["features"] if "features" in subgeom else subgeom
                for subgeom in geom
            ]
            geom_offset = np.cumsum([len(subgeom) for subgeom in geom]).tolist()
            geom_offset.pop()
            geom_offset.insert(0, 0)
            self._geom_offset = geom_offset
            for ix, subgeom in enumerate(geom):
                subgeom = subgeom.copy()
                start = geom_offset[ix]
                if instance(subgeom) == "list":
                    # geojson feature collection
                    for feat in subgeom:
                        if "properties" in feat:
                            feat["properties"].update(
                                {"__geom_name": self.options.object_name[ix]}
                            )
                        else:
                            feat.setdefault(
                                "properties",
                                {"__geom_name": self.options.object_name[ix]},
                            )
                    geom[ix] = dict(enumerate(subgeom, start))
                else:
                    # geopandas geodataframe
                    subgeom["__geom_name"] = self.options.object_name[ix]
                    geom[ix] = dict(enumerate(subgeom.to_dict(orient="records"), start))
            for ix in range(1, len(geom)):
                geom[0].update(geom[ix])
            data = geom[0]
            self._is_multi_geom = True
        else:
            # list consist of features
            # convert list to indexed-dictionary
            # Each feature will be processed individually by _serialize_geom_type
            data = dict(enumerate(geom))
        # new data dictionary is created, throw the geometries back to main()
        self._is_single = False
        self._extractor(data)

    def _extract_string(self, geom):
        """
        This function extracts a String instance.
        Both TopoJSON and GeoJSON string instances are recognized

        Parameters
        ----------
        geom : str
            String instance
        """
        if '"type": "Topology"' in geom:
            from ..utils import serialize_as_geojson

            geom = json.loads(geom)
            data = serialize_as_geojson(geom)
        else:
            try:
                import geojson

                data = geojson.loads(geom)
            except ImportError:
                raise ImportError(
                    "String was tried to read with the Python package `geojson`, but it is not installed."
                )
        self._extractor(data)

    def _extract_dictionary(self, geom):
        """
        This function extracts a Dictionary instance.

        Parameters
        ----------
        geom : dict
            Dictionary instance
        """

        self._is_single = False
        if (
            "type" in geom.keys()
            and geom["type"].casefold() == "FeatureCollection".casefold()
        ):
            return self._extract_featurecollection(geom)
        self._data = copy.deepcopy(self._data)

        # iterate over the input dictionary or geographical object
        for key in list(self._data):
            # based on the geom type the right function is serialized
            self._key = key
            self._obj = self._data[self._key]

            try:
                # detect if object is a shapely geometry
                if hasattr(self._obj, "geom_type"):
                    geom = self._obj
                    self._obj = geom.__geo_interface__
                    self._data[self._key] = self._obj
                # detect if object contains shapely supported geometries:
                elif "geometry" in self._obj.keys() and hasattr(
                    self._obj["geometry"], "geom_type"
                ):
                    # extract geometry and collect type and properties
                    geom = self._obj["geometry"]
                    self._obj.pop("geometry", None)

                    if geom.geom_type == "GeometryCollection":
                        geometries = self._obj["geometries"]
                        self._obj.pop("geometries", None)
                        self._obj = {
                            "properties": self._obj,
                            "type": geom.geom_type,
                            "geometries": geometries,
                        }
                    else:
                        self._obj = {"properties": self._obj, "type": geom.geom_type}
                    self._data[self._key] = self._obj
                # no direct shapely geometries available. Try forcing
                else:
                    # detect if the object contains a __geo_interface__.
                    if hasattr(self._obj, "__geo_interface__"):
                        self._obj = self._obj.__geo_interface__
                        self._data[self._key] = self._obj
                    # try parsing the object into a shapely geometry. If this not succeeds
                    # then the object might be a GeoJSON Feature or FeatureCollection. If
                    # this fails as well then the object is not recognized and removed.
                    try:
                        with ignore_shapely2_warnings():
                            geom = geometry.shape(self._obj)
                        # object can be mapped, but may not be valid. remove invalid objects
                        # and continue
                        if not geom.is_valid:
                            self._invalid_geoms += 1
                            del self._data[self._key]
                            continue
                    except GeometryTypeError:
                        # object might be a GeoJSON Feature or FeatureCollection
                        # check if geojson is installed
                        try:
                            import geojson

                            geom = geojson.GeoJSON.to_instance(self._obj)
                        except ImportError:
                            # no geojson installed. remove object
                            self._tried_geojson = True
                            self._invalid_geoms += 1
                            del self._data[self._key]
                            continue
                    except ValueError:
                        # object is not valid, remove invalid objects
                        # and continue
                        self._invalid_geoms += 1
                        del self._data[self._key]
                        continue
                    except AttributeError:
                        # check if geojson is installed
                        try:
                            import geojson

                            geom = geojson.loads(self._obj)
                        except ImportError:
                            # no geojson installed. remove object
                            self._tried_geojson = True
                            self._invalid_geoms += 1
                            del self._data[self._key]
                            continue
                    except (IndexError, TypeError):
                        # object is not valid
                        self._invalid_geoms += 1
                        del self._data[self._key]
                        continue
            except AttributeError:
                # object is not valid
                self._invalid_geoms += 1
                del self._data[self._key]
                continue
            # the geom object is recognized, lets serialize the geometric type.
            # this function redirects the geometric object based on its type to
            # an equivalent function. Adopting this approach avoids the usage of
            # multiple if-else statements.
            self._serialize_geom_type(geom)

            # reset geom collection counter and level
            self._geomcollection_counter = 0
            self._geom_level_1 = 0
