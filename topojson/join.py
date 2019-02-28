# pylint: disable=unsubscriptable-object
from shapely import geometry
from shapely.wkb import loads
from shapely.ops import shared_paths
from shapely.ops import linemerge
from shapely import speedups
from .utils.ops import select_unique_combs
import numpy as np
import itertools
import copy
import warnings

if speedups.available:
    speedups.enable()


class Join:
    """
    Identify junctions (intersection points) of shared paths.
    """

    def __init__(self):
        # initation topology items
        self.junctions = []
        self.segments = []
        self.valerr = False

    def prequantize(self, linestrings, quant_factor=1e6):
        """
        Function that applies quantization. Quantization removes information by 
        reducing the precision of each coordinate, effectively snapping each point 
        to a regular grid

        Parameters
        ----------
        linestrings: list of shapely.geometry.LineStrings
            LineStrings that will be quantized
        quant_factor : int
            Quantization factor. Normally this varies between 1e4, 1e5, 1e6. Where a 
            higher number means a bigger grid where the coordinates can snap to. 

        Returns
        -------
        kx, ky, x0, y0: int
            Scale (kx, ky) and translation (x0, y0) values
        """

        x0, y0, x1, y1 = geometry.MultiLineString(linestrings).bounds
        kx = 1 / ((quant_factor - 1) / (x1 - x0))
        ky = 1 / ((quant_factor - 1) / (y1 - y0))

        for ls in linestrings:
            ls_xy = np.array(ls.xy)
            ls_xy = (
                np.array([(ls_xy[0] - x0) / kx, (ls_xy[1] - y0) / ky])
                .T.round()
                .astype(int)
            )
            ls.coords = ls_xy[
                np.insert(np.absolute(np.diff(ls_xy, 1, axis=0)).sum(axis=1), 0, 1) != 0
            ]

        return kx, ky, x0, y0

    def shared_segs(self, g1, g2):
        """
        This function returns the segments that are shared with two input geometries.
        The shapely function `shapely.ops.shared_paths()` is adopted and can catch
        both the shared paths with the same direction for both inputs as well as the 
        shared paths with the opposite direction for one the two inputs.

        The returned object extents the `segments` property with detected segments.
        Where each seperate segment is a linestring between two points.        
        
        Parameters
        ----------
        g1 : shapely.geometry.LineString
            first geometry
        g2 : shapely.geometry.LineString
            second geometry
        """

        # detect potential shared paths between two linestrings
        try:
            fw_bw = shared_paths(g1, g2)
        except ValueError:
            self.valerr = True
            fw_bw = False
            # fw_bw = shared_paths(snap(g1, g2, tolerance=6), g2)

        # continue if any shared path was detected
        if fw_bw and not fw_bw.is_empty:

            forward = fw_bw[0]
            backward = fw_bw[1]

            if backward.is_empty:
                # only contains forward objects
                shared_segments = forward
            elif forward.is_empty:
                # only contains backward objects
                shared_segments = backward
            else:
                # both backward and forward contains objects, so combine
                shared_segments = geometry.MultiLineString(
                    [linemerge(forward), linemerge(backward)]
                )

            # add shared paths to segments
            self.segments.extend([list(shared_segments)])

            # also add the first coordinates of both geoms as a vertice to segments
            p1_g1 = geometry.Point([g1.xy[0][0], g1.xy[1][0]])
            p1_g2 = geometry.Point([g2.xy[0][0], g2.xy[1][0]])
            ls_p1_g1g2 = geometry.LineString([p1_g1, p1_g2])
            self.segments.extend([[ls_p1_g1g2]])

    def main(self, data, quant_factor=None):
        """
        Entry point for the class Join.

        The join function is the second step in the topology computation.
        The following sequence is adopted:
        1. extract
        2. join
        3. cut 
        4. dedup 
        5. hashmap  

        Detects the junctions of shared paths from the specified hash of linestrings.
        
        After decomposing all geometric objects into linestrings it is necessary to 
        detect the junctions or start and end-points of shared paths so these paths can 
        be 'merged' in the next step. Merge is quoted as in fact only one of the 
        shared path is kept and the other path is removed.

        Parameters
        ----------
        data : dict
            object created by the method topojson.extract.
        quant_factor : int, optional (default: None)
            quantization factor, used to constrain float numbers to integer values.
            - Use 1e4 for 5 valued values (00001-99999)
            - Use 1e6 for 7 valued values (0000001-9999999)
        
        Returns
        -------
        dict
            object expanded with 
            - new key: junctions
            - new key: transform (if quant_factor is not None)        
        """

        if not data["linestrings"]:
            data["junctions"] = self.junctions
            return data

        # quantize linestrings before comparing
        # if set to None or a value < 1 (True equals 1) no quantizing is applied.
        if quant_factor is not None:
            if quant_factor > 1:
                kx, ky, x0, y0 = self.prequantize(data["linestrings"], quant_factor)
                data["transform"] = {"scale": [kx, ky], "translate": [x0, y0]}

        # create list with unique combinations of lines using a rdtree
        line_combs = select_unique_combs(data["linestrings"])

        # iterate over index combinations
        for i1, i2 in line_combs:
            g1 = data["linestrings"][i1]
            g2 = data["linestrings"][i2]

            # check if geometry are equal
            # being equal meaning the geometry object coincide with each other.
            # a rotated polygon or reversed linestring are both considered equal.
            if not g1.equals(g2):
                # geoms are unique, let's find junctions
                self.shared_segs(g1, g2)

        # self.segments are nested lists of LineStrings, get coordinates of each nest
        s_coords = []
        for segment in self.segments:
            s_coords.extend(
                [
                    [
                        (x.xy[0][y], x.xy[1][y])
                        for x in segment
                        for y in range(len(x.xy[0]))
                    ]
                ]
            )
            # s_coords.extend([[y for x in segment for y in list(x.coords)]])

        # only keep junctions that appear only once in each segment (nested list)
        # coordinates that appear multiple times are not junctions
        for coords in s_coords:
            self.junctions.extend(
                [geometry.Point(i) for i in coords if coords.count(i) is 1]
            )

        # junctions can appear multiple times in multiple segments, remove duplicates
        self.junctions = [
            loads(xy) for xy in list(set([x.wkb for x in self.junctions]))
        ]

        # prepare to return object
        data["junctions"] = self.junctions

        return data


def join(data, quant_factor=None):
    """
    This function targets the following objectives: 
    1. Quantization of input linestrings if necessary
    2. Identifies junctions of shared paths

    The join function is the second step in the topology computation.
    The following sequence is adopted:
    1. extract
    2. join
    3. cut 
    4. dedup 
    5. hashmap  
    
    Parameters
    ----------
    data : dict
        object created by the method topojson.extract.
    quant_factor : int, optional (default: None)
        quantization factor, used to constrain float numbers to integer values.
        - Use 1e4 for 5 valued values (00001-99999)
        - Use 1e6 for 7 valued values (0000001-9999999)
    
    Returns
    -------
    dict
        object expanded with 
        - new key: junctions
        - new key: transform (if quant_factor is not None)
    """
    data = copy.deepcopy(data)
    joiner = Join()
    return joiner.main(data, quant_factor)
