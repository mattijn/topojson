from functools import singledispatch, update_wrapper
from types import SimpleNamespace
import pprint
import json

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

# ----------------- topology options object ------------------
class TopoOptions(object):
    def __init__(
        self,
        object={},
        topology=True,
        prequantize=False,
        presimplify=False,
        toposimplify=False,
        winding_order=None,  # default should become "CW_CCW",
    ):
        # get all arguments and check if `object` is created.
        # If so, use the key values of `object`, otherwise ignore `object`
        arguments = locals()
        if bool(arguments["object"]) != False:
            arguments = arguments["object"]["options"]

        if "topology" in arguments:
            self.topology = arguments["topology"]
        else:
            self.topology = True

        if "prequantize" in arguments:
            self.prequantize = arguments["prequantize"]
        else:
            self.prequantize = False

        if "presimplify" in arguments:
            self.presimplify = arguments["presimplify"]
        else:
            self.presimplify = False

        if "toposimplify" in arguments:
            self.toposimplify = arguments["toposimplify"]
        else:
            self.toposimplify = False

        if "winding_order" in arguments:
            self.winding_order = arguments["winding_order"]
        else:
            self.winding_order = None

    def __repr__(self):
        return "TopoOptions(\n  {}\n)".format(pprint.pformat(self.__dict__))


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


# ----------------- serialization functions ------------------
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


def serialize_as_svg(topo_object, separate):
    from IPython.display import SVG, display
    from shapely import geometry

    if separate:
        for ix, line in enumerate(topo_object["linestrings"]):
            svg = line._repr_svg_()
            print(ix, line.wkt)
            display(SVG(svg))
    else:
        display(geometry.MultiLineString(topo_object["linestrings"]))


def serialize_as_json(topo_object, fp):
    if fp:
        return print(json.dumps(topo_object), f=fp)
    else:
        return json.dumps(topo_object)


def serialize_as_altair(
    topo_object,
    mesh=True,
    color=None,
    tooltip=True,
    projection="identity",
    objectname="data",
):
    import altair as alt

    # create a mesh visualization
    if mesh and color is None:
        data = alt.InlineData(
            values=topo_object, format=alt.DataFormat(mesh=objectname, type="topojson")
        )
        chart = (
            alt.Chart(data, width=300)
            .mark_geoshape(filled=False)
            .project(type=projection, reflectY=True)
        )

    # creating a chloropleth visualisation
    elif color is not None:
        data = alt.InlineData(
            values=topo_object,
            format=alt.DataFormat(feature=objectname, type="topojson"),
        )
        if tooltip == True:
            tooltip = [color]
        chart = (
            alt.Chart(data, width=300)
            .mark_geoshape()
            .encode(
                color=alt.Color(color, legend=alt.Legend(columns=2)), tooltip=tooltip
            )
            .project(type=projection, reflectY=True)
        )

    return chart

