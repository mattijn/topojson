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
        snap_vertices=None,
        simplify=None,
        snap_value_gridsize=None,
        simplify_factor=None,
        winding_order="CW_CCW",
    ):
        if snap_vertices:
            self.snap_vertices = snap_vertices
        if simplify:
            self.simplify = simplify
        if snap_value_gridsize:
            self.snap_value_gridsize = snap_value_gridsize
        if simplify_factor:
            self.simplify_factor = simplify_factor
        if winding_order:
            self.winding_order = winding_order

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
