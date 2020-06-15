from functools import singledispatch, update_wrapper
from types import SimpleNamespace
import numpy as np
import pprint
import json
from .ops import dequantize
from .ops import np_array_from_arcs


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
        shared_coords=True,
        prevent_oversimplify=True,
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

        if "shared_coords" in arguments:
            self.shared_coords = arguments["shared_coords"]
        else:
            self.shared_coords = True

        if "prevent_oversimplify" in arguments:
            self.prevent_oversimplify = arguments["prevent_oversimplify"]
        else:
            self.prevent_oversimplify = True

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


# --------- supportive functions for serialization -----------
def coordinates(arcs, tp_arcs):
    """
    Return GeoJSON coordinates for the sequence(s) of arcs.
    
    The arcs parameter may be a sequence of ints, each the index of a coordinate 
    sequence within tp_arcs within the entire topology describing a line string, a 
    sequence of such sequences, describing a polygon, or a sequence of polygon arcs.
    """

    if isinstance(arcs[0], int):
        coords = np.concatenate(
            [
                tp_arcs[arc if arc >= 0 else ~arc][:: arc >= 0 or -1][i > 0 :]
                for i, arc in enumerate(arcs)
            ]
        )
        coords = coords[~np.isnan(coords).any(axis=1)].tolist()
        return coords
    elif isinstance(arcs[0], (list, tuple)):
        return list(coordinates(arc, tp_arcs) for arc in arcs)
    else:
        raise ValueError("Invalid input %s", arcs)


def geometry(obj, tp_arcs, transform=None):
    """
    Converts a topology object to a geometry object.
    
    The topology object is a dict with 'type' and 'arcs' items.
    """
    if obj["type"] == "GeometryCollection":
        geometries = [geometry(feat, tp_arcs) for feat in obj["geometries"]]
        return {"type": obj["type"], "geometries": geometries}

    if obj["type"] == "MultiPoint":
        if transform is not None:
            scale = transform["scale"]
            translate = transform["translate"]
            coords = obj["coordinates"]
            point_coords = dequantize(np.array(coords).T, scale, translate).T.tolist()
        else:
            point_coords = obj["coordinates"]
        return {"type": obj["type"], "coordinates": point_coords}

    if obj["type"] == "Point":
        if transform is not None:
            scale = transform["scale"]
            translate = transform["translate"]
            coords = [obj["coordinates"]]
            point_coord = dequantize(np.array(coords), scale, translate).tolist()
        else:
            point_coord = [obj["coordinates"]]
        return {"type": obj["type"], "coordinates": point_coord[0]}

    else:
        return {"type": obj["type"], "coordinates": coordinates(obj["arcs"], tp_arcs)}


def prettyjson(obj, indent=2, maxlinelength=80):
    """Renders JSON content with indentation and line splits/concatenations to fit maxlinelength.
    Only dicts, lists and basic types are supported"""

    # https://stackoverflow.com/a/56497521/104668

    items, _ = getsubitems(
        obj, itemkey="", islast=True, maxlinelength=maxlinelength, level=0
    )
    return indentitems(items, indent, level=0)


def getsubitems(obj, itemkey, islast, maxlinelength, level):
    items = []
    is_inline = (
        True  # at first, assume we can concatenate the inner tokens into one line
    )

    isdict = isinstance(obj, dict)
    islist = isinstance(obj, list)
    istuple = isinstance(obj, tuple)
    isbasictype = not (isdict or islist or istuple)

    # build json content as a list of strings or child lists
    if isbasictype:
        # render basic type
        keyseparator = "" if itemkey == "" else ": "
        itemseparator = "" if islast else ","
        items.append(itemkey + keyseparator + basictype2str(obj) + itemseparator)

    else:
        # render lists/dicts/tuples
        if isdict:
            opening, closing, keys = ("{", "}", iter(obj.keys()))
        elif islist:
            opening, closing, keys = ("[", "]", range(0, len(obj)))
        elif istuple:
            opening, closing, keys = (
                "[",
                "]",
                range(0, len(obj)),
            )  # tuples are converted into json arrays

        if itemkey != "":
            opening = itemkey + ": " + opening
        if not islast:
            closing += ","

        count = 0
        itemkey = ""
        subitems = []

        # get the list of inner tokens
        for (i, k) in enumerate(keys):
            islast_ = i == len(obj) - 1
            itemkey_ = ""
            if isdict:
                itemkey_ = basictype2str(k)
            inner, is_inner_inline = getsubitems(
                obj[k], itemkey_, islast_, maxlinelength, level + 1
            )
            subitems.extend(inner)  # inner can be a string or a list
            is_inline = (
                is_inline and is_inner_inline
            )  # if a child couldn't be rendered inline, then we are not able either

        # fit inner tokens into one or multiple lines, each no longer than maxlinelength
        if is_inline:
            multiline = True

            # in Multi-line mode items of a list/dict/tuple can be rendered in multiple lines if they don't fit on one.
            # suitable for large lists holding data that's not manually editable.

            # in Single-line mode items are rendered inline if all fit in one line, otherwise each is rendered in a separate line.
            # suitable for smaller lists or dicts where manual editing of individual items is preferred.

            # this logic may need to be customized based on visualization requirements:
            if isdict:
                multiline = False
            if islist:
                multiline = True

            if multiline:
                lines = []
                current_line = ""
                current_index = 0

                for (i, item) in enumerate(subitems):
                    item_text = item
                    if i < len(inner) - 1:
                        item_text = item + ","

                    if len(current_line) > 0:
                        try_inline = current_line + " " + item_text
                    else:
                        try_inline = item_text

                    if len(try_inline) > maxlinelength:
                        # push the current line to the list if maxlinelength is reached
                        if len(current_line) > 0:
                            lines.append(current_line)
                        current_line = item_text
                    else:
                        # keep fitting all to one line if still below maxlinelength
                        current_line = try_inline

                    # Push the remainder of the content if end of list is reached
                    if i == len(subitems) - 1:
                        lines.append(current_line)

                subitems = lines
                if len(subitems) > 1:
                    is_inline = False
            else:  # single-line mode
                totallength = len(subitems) - 1  # spaces between items
                for item in subitems:
                    totallength += len(item)
                if totallength <= maxlinelength:
                    str = ""
                    for item in subitems:
                        str += (
                            item + " "
                        )  # insert space between items, comma is already there
                    subitems = [str.strip()]  # wrap concatenated content in a new list
                else:
                    is_inline = False

        # attempt to render the outer brackets + inner tokens in one line
        if is_inline:
            item_text = ""
            if len(subitems) > 0:
                item_text = subitems[0]
            if len(opening) + len(item_text) + len(closing) <= maxlinelength:
                items.append(opening + item_text + closing)
            else:
                is_inline = False

        # if inner tokens are rendered in multiple lines already, then the outer brackets remain in separate lines
        if not is_inline:
            items.append(opening)  # opening brackets
            items.append(subitems)  # Append children to parent list as a nested list
            items.append(closing)  # closing brackets

    return items, is_inline


def basictype2str(obj):
    if isinstance(obj, str):
        strobj = '"' + str(obj) + '"'
    elif isinstance(obj, bool):
        strobj = {True: "true", False: "false"}[obj]
    else:
        strobj = str(obj)
    return strobj


def indentitems(items, indent, level):
    """Recursively traverses the list of json lines, adds indentation based on the current depth"""
    res = ""
    indentstr = " " * (indent * level)
    for (i, item) in enumerate(items):
        if isinstance(item, list):
            res += indentitems(item, indent, level + 1)
        else:
            islast = i == len(items) - 1
            # no new line character after the last rendered line
            if level == 0 and islast:
                res += indentstr + item
            else:
                res += indentstr + item + "\n"
    return res


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
    geopandas.GeoDataFrame
        topojson object parsed as GeoDataFrame
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
        if arcs:
            # dequantize if quantization is applied
            if "transform" in keys:

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
            line = geometry.LineString(line)
            svg = line._repr_svg_()
            print(ix, line.wkt)
            display(SVG(svg))
    elif separate and include_junctions:
        pts = topo_object["junctions"]
        for ix, line in enumerate(arcs):
            line = geometry.LineString(line)
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


def serialize_as_json(topo_object, fp, pretty=False, indent=4, maxlinelength=88):
    if fp:
        with open(fp, "w") as f:
            if pretty:
                print(
                    prettyjson(topo_object, indent=indent, maxlinelength=maxlinelength),
                    file=f,
                )
            else:
                json.dump(topo_object, fp=f)
    else:
        if pretty:
            return prettyjson(topo_object, indent=indent, maxlinelength=maxlinelength)
        else:
            return json.dumps(topo_object)


def serialize_as_geojson(
    topo_object,
    fp=None,
    pretty=False,
    indent=4,
    maxlinelength=88,
    validate=False,
    objectname="data",
):
    from shapely.geometry import shape

    # prepare arcs from topology object
    arcs = topo_object["arcs"]
    transform = None
    if "transform" in topo_object.keys():
        transform = topo_object["transform"]
        scale = transform["scale"]
        translate = transform["translate"]

    if arcs:
        np_arcs = np_array_from_arcs(arcs)
        # dequantize if quantization is applied
        np_arcs = dequantize(np_arcs, scale, translate)
    else:
        np_arcs = None

    # select object member from topology object
    features = topo_object["objects"][objectname]["geometries"]

    # prepare geojson featurecollection
    fc = {"type": "FeatureCollection", "features": []}

    # fill the featurecollection with geometry object members
    for index, feature in enumerate(features):
        f = {"id": index, "type": "Feature"}
        if "properties" in feature.keys():
            f["properties"] = feature["properties"].copy()

        # the transform is only used in cases of points or multipoints
        geommap = geometry(feature, np_arcs, transform)
        if validate:
            geom = shape(geommap).buffer(0)
            assert geom.is_valid
            f["geometry"] = geom.__geo_interface__
        else:
            f["geometry"] = geommap

        fc["features"].append(f)
    return fc


def serialize_as_altair(
    topo_object,
    mesh=True,
    color=None,
    tooltip=True,
    projection="identity",
    objectname="data",
    geo_interface=False,
):
    import altair as alt

    # create a mesh visualization
    if geo_interface and mesh:
        # chart object
        chart = (
            alt.Chart(topo_object, width=300)
            .mark_geoshape(filled=False)
            .project(type=projection, reflectY=True)
        )

    # create a mesh visualization
    elif mesh and color is None:
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
    topo_object.options.simplify_with = "simplification"

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
