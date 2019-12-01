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
        object=None,
        topology=True,
        prequantize=False,
        topoquantize=False,
        presimplify=False,
        toposimplify=False,
        simplify_with="shapely",
        simplify_algorithm="dp",
        winding_order=None,
    ):
        # get all arguments
        arguments = locals()
        if arguments["object"]:
            arguments = arguments["object"]

        if "topology" in arguments:
            self.topology = arguments["topology"]
        else:
            self.topology = True

        if "prequantize" in arguments:
            self.prequantize = arguments["prequantize"]
        else:
            self.prequantize = False

        if "topoquantize" in arguments:
            self.topoquantize = arguments["topoquantize"]
        else:
            self.topoquantize = False

        if "presimplify" in arguments:
            self.presimplify = arguments["presimplify"]
        else:
            self.presimplify = False

        if "toposimplify" in arguments:
            self.toposimplify = arguments["toposimplify"]
        else:
            self.toposimplify = False

        if "simplify_with" in arguments:
            self.simplify_with = arguments["simplify_with"]
        else:
            self.simplify_with = "shapely"

        if "simplify_algorithm" in arguments:
            self.simplify_algorithm = arguments["simplify_algorithm"]
        else:
            self.simplify_algorithm = "dp"

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
    elif url is True:
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


def serialize_as_svg(topo_object, separate=False, include_junctions=False):
    from IPython.display import SVG, display
    from shapely import geometry

    keys = topo_object.keys()
    if "arcs" in keys:
        arcs = topo_object["arcs"]
        # dequantize if quantization is applied
        if "transform" in keys:
            from .ops import dequantize
            from .ops import np_array_from_arcs
            import numpy as np

            np_arcs = np_array_from_arcs(arcs)

            transform = topo_object["transform"]
            scale = transform["scale"]
            translate = transform["translate"]

            np_arcs = dequantize(np_arcs, scale, translate)
            l_arcs = []
            for ls in np_arcs:
                l_arcs.append(ls[~np.isnan(ls)[:, 0]].tolist())
            arcs = l_arcs

        arcs = [geometry.LineString(arc) for arc in arcs]

    else:
        arcs = topo_object["linestrings"]

    if separate and not include_junctions:
        for ix, line in enumerate(arcs):
            svg = line._repr_svg_()
            print(ix, line.wkt)
            display(SVG(svg))
    elif separate and include_junctions:
        pts = topo_object["junctions"]
        for ix, line in enumerate(arcs):
            svg = geometry.GeometryCollection(
                [line, geometry.MultiPoint(pts)]
            )._repr_svg_()
            print(ix, line.wkt)
            display(SVG(svg))

    elif not separate and include_junctions:
        pts = topo_object["junctions"]
        display(
            geometry.GeometryCollection(
                [geometry.MultiLineString(arcs), geometry.MultiPoint(pts)]
            )
        )
    else:
        display(geometry.MultiLineString(arcs))


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
        if tooltip is True:
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


def serialize_as_ipywidgets(topo_object, toposimplify, topoquantize):
    from ipywidgets import interact
    from ipywidgets import fixed
    import ipywidgets as widgets

    style = {"description_width": "initial"}
    ts = toposimplify
    tq = topoquantize

    # set to simplification package for speed
    topo_object.output["options"].simplify_with = "simplification"

    alg = widgets.RadioButtons(
        options=[("Douglas-Peucker", "dp"), ("Visvalingam-Whyatt", "vw")],
        value="dp",
        description="Simplify algortihm",
        disabled=False,
        style=style,
    )
    eps = widgets.FloatSlider(
        min=ts["min"],
        max=ts["max"],
        step=ts["step"],
        value=ts["value"],
        description="Toposimplify Factor",
        style=style,
    )
    qnt = widgets.FloatLogSlider(
        min=tq["min"],
        max=tq["max"],
        step=tq["step"],
        value=tq["value"],
        base=tq["base"],
        description="Topoquantize Factor",
        style=style,
    )

    return interact(
        toposimpquant, epsilon=eps, quant=qnt, algo=alg, topo=fixed(topo_object)
    )


def toposimpquant(epsilon, quant, algo, topo):
    topo.output["options"].simplify_algorithm = algo
    return topo.toposimplify(epsilon).topoquantize(quant).to_alt()
