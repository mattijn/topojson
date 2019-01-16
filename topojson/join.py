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
    identify junctions (intersection points) of shared paths.
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
        linestrings: list of shapely.LineStrings
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

    def main(self, data, quant_factor):
        """
        Detects the junctions of shared paths from the specified hash of linestrings.

        The join function is the second step in the topology computation.
        The following sequence is adopted:
        1. extract
        2. join
        3. cut 
        4. dedup
        5. hashmap
        
        After decomposing all geometric objects into linestrings it is necessary to 
        detect the junctions or start and end-points of shared paths so these paths can 
        be 'merged' in the next step. Merge is quoted as in fact only one of the 
        shared path is kept and the other path is removed.

        Developping Notes:
        # current implemented method using comprension lists
        s_coords = [y for x in s12 for y in list(x.coords)]
        pts = [i for i in s_coords if s_coords.count(i) is 1]

        # potential method using numpy array
        mls_xy = np.array(s12.__geo_interface__['coordinates'])
        mls_xy = mls_xy.reshape(-1, mls_xy.shape[-1])
        uniq_xy, ctx_xy = np.unique(mls_xy, axis=0, return_counts=True)
        pts = uniq_xy[ctx_xy == 1]
        
        The following links have been used as reference for this object/functions.
        
        to find shared paths:
        https://shapely.readthedocs.io/en/stable/manual.html#shared-paths
        
        to set up a R-tree:
        https://shapely.readthedocs.io/en/stable/manual.html#str-packed-r-tree

        Use tolerance setting in snap for near-identical shared paths.
        Uuse snap to catch TopologyException for non-noded intersections
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
    data = copy.deepcopy(data)
    joiner = Join()
    return joiner.main(data, quant_factor)
