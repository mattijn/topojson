from functools import singledispatch, update_wrapper
from types import SimpleNamespace
import pprint

# ----------- dummy files for geopandas and geojson ----------
class GeoDataFrame(object):
    pass


class GeoSeries(object):
    pass


geopandas = SimpleNamespace()
setattr(geopandas, "GeoDataFrame", GeoDataFrame)
setattr(geopandas, "GeoSeries", GeoSeries)


class Feature(object):
    pass


class FeatureCollection(object):
    pass


geojson = SimpleNamespace()
setattr(geojson, "Feature", Feature)
setattr(geojson, "FeatureCollection", FeatureCollection)
# //--------- dummy files for geopandas and geojson ----------

# ----------------- topology options object ------------------
class TopoOptions(object):
    def __init__(
        self,
        object={},
        snap_vertices=None,
        simplify=None,
        snap_value_gridsize=None,
        simplify_factor=None,
        winding_order=None,  # default should become "CW_CCW",
    ):
        # get all arguments and check if `object` is created.
        # If so, use the key values of `object`, otherwise ignore `object`
        arguments = locals()
        if bool(arguments["object"]) != False:
            arguments = arguments["object"]["options"]

        if "snap_vertices" in arguments:
            self.snap_vertices = arguments["snap_vertices"]
        else:
            self.snap_vertices = None

        if "simplify" in arguments:
            self.simplify = arguments["simplify"]
        else:
            self.simplify = None

        if "snap_value_gridsize" in arguments:
            self.snap_value_gridsize = arguments["snap_value_gridsize"]
        else:
            self.snap_value_gridsize = None

        if "simplify_factor" in arguments:
            self.simplify_factor = arguments["simplify_factor"]
        else:
            self.simplify_factor = None

        if "winding_order" in arguments:
            self.winding_order = arguments["winding_order"]
        else:
            self.simplify_factor = None

    def __repr__(self):
        return "TopoOptions(\n  {}\n)".format(pprint.pformat(self.__dict__))


# //--------------- topology options object ------------------


def singledispatch_class(func):
    """
    The singledispatch function only applies to functions. This function creates a 
    wrapper around the singledispatch so it can be used for class instances.
    
    Returns
    -------
    dispatch
        dispatcher for methods
    """

    dispatcher = singledispatch(func)

    def wrapper(*args, **kw):
        return dispatcher.dispatch(args[1].__class__)(*args, **kw)

    wrapper.register = dispatcher.register
    update_wrapper(wrapper, dispatcher)
    return wrapper


def serialize_as_geodataframe(topo_object, url=False):
    """
    Convert a topology dictionary or string into a GeoDataFrame.

    Parameters
    ----------
    topo_object : dict, str
        a complete object representing an topojson encoded file as 
        dict, str-object or str-url
    
    Returns
    -------
    gdf : geopandas.GeoDataFrame
        topojson object parsed GeoDataFrame
    """
    import fiona
    import geopandas
    import json

    # parse the object as byte string
    if isinstance(topo_object, dict):
        bytes_topo = str.encode(json.dumps(topo_object))
    elif url == True:
        import requests

        request = requests.get(topo_object)
        bytes_topo = bytes(request.content)
    else:
        bytes_topo = str.encode(topo_object)
    # into an in-memory file
    vsimem = fiona.ogrext.buffer_to_virtual_file(bytes_topo)

    # read the features from a fiona collection into a GeoDataFrame
    with fiona.Collection(vsimem, driver="TopoJSON") as f:
        gdf = geopandas.GeoDataFrame.from_features(f, crs=f.crs)
    return gdf
