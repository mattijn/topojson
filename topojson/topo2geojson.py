"""
Functions that extract GeoJSON-ish data structures from TopoJSON
(https://github.com/mbostock/topojson) topology data.
Author: Sean Gillies (https://github.com/sgillies)
Source code: https://github.com/sgillies/topojson/blob/master/topojson.py


Combine with code to read .topojson and write .geojson:
Author: Matthew Perry (https://github.com/perrygeo/topo2geojson)
Source code: https://gist.github.com/perrygeo/1e767e42e8bc54ad7262 

As mentioned by Matthew:
This is not ready for production use and probably contains lots of bugs. 
It might be a useful starting point but it is not yet a robust tool
"""

from itertools import chain
import json
import sys
from shapely.geometry import shape


def rel2abs(arc, scale=None, translate=None):
    """Yields absolute coordinate tuples from a delta-encoded arc.
    If either the scale or translate parameter evaluate to False, yield the
    arc coordinates with no transformation."""
    if scale and translate:
        a, b = 0, 0
        for ax, bx in arc:
            a += ax
            b += bx
            yield scale[0] * a + translate[0], scale[1] * b + translate[1]
    else:
        for x, y in arc:
            yield x, y


def coordinates(arcs, topology_arcs, scale=None, translate=None):
    """Return GeoJSON coordinates for the sequence(s) of arcs.
    
    The arcs parameter may be a sequence of ints, each the index of a
    coordinate sequence within topology_arcs
    within the entire topology -- describing a line string, a sequence of 
    such sequences -- describing a polygon, or a sequence of polygon arcs.
    
    The topology_arcs parameter is a list of the shared, absolute or
    delta-encoded arcs in the dataset.
    The scale and translate parameters are used to convert from delta-encoded
    to absolute coordinates. They are 2-tuples and are usually provided by
    a TopoJSON dataset. 
    """
    if isinstance(arcs[0], int):
        coords = [
            list(rel2abs(topology_arcs[arc if arc >= 0 else ~arc], scale, translate))[
                :: arc >= 0 or -1
            ][i > 0 :]
            for i, arc in enumerate(arcs)
        ]
        return list(chain.from_iterable(coords))
    elif isinstance(arcs[0], (list, tuple)):
        return list(coordinates(arc, topology_arcs, scale, translate) for arc in arcs)
    else:
        raise ValueError("Invalid input %s", arcs)


def geometry(obj, topology_arcs, scale=None, translate=None):
    """Converts a topology object to a geometry object.
    
    The topology object is a dict with 'type' and 'arcs' items, such as
    {'type': "LineString", 'arcs': [0, 1, 2]}.
    See the coordinates() function for a description of the other three
    parameters.
    """
    return {
        "type": obj["type"],
        "coordinates": coordinates(obj["arcs"], topology_arcs, scale, translate),
    }


def convert(topojson_path, geojson_path):

    with open(topojson_path, "r") as fh:
        f = fh.read()
        topology = json.loads(f)

    # file can be renamed, the first 'object' is more reliable
    layername = topology["objects"].keys()[0]

    features = topology["objects"][layername]["geometries"]
    scale = topology["transform"]["scale"]
    trans = topology["transform"]["translate"]

    with open(geojson_path, "w") as dest:
        fc = {"type": "FeatureCollection", "features": []}

        for id, tf in enumerate(features):
            f = {"id": id, "type": "Feature"}
            f["properties"] = tf["properties"].copy()

            geommap = geometry(tf, topology["arcs"], scale, trans)
            geom = shape(geommap).buffer(0)
            assert geom.is_valid
            f["geometry"] = geom.__geo_interface__

            fc["features"].append(f)

        dest.write(json.dumps(fc))

