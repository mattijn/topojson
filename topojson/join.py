# pylint: disable=unsubscriptable-object
from shapely import geometry
from shapely.wkb import loads
from shapely.ops import shared_paths
from shapely.ops import linemerge
from shapely import speedups
import itertools
import copy

if speedups.available:
    speedups.enable()


class _Join:
    """
    identify junctions (intersection points) of shared paths.
    """

    def __init__(self):
        # initation topology items
        self.junctions = []
        self.segments = []

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
            p1_g1 = geometry.Point(list(g1.coords[0]))
            p1_g2 = geometry.Point(list(g2.coords[0]))
            ls_p1_g1g2 = geometry.LineString([p1_g1, p1_g2])
            self.segments.extend([[ls_p1_g1g2]])

    def main(self, data):
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
        * why not de-duplicate (dedup) equal geometries in this object/function? 
        Current approach is to record them and deal with it, maybe combined, in `cut` 
        or `dedup` phase.

        The following links have been used as reference for this object/functions.
        TODO: delete when needed.
        
        to find shared paths:
        https://shapely.readthedocs.io/en/stable/manual.html#shared-paths
        
        to set up a R-tree:
        https://shapely.readthedocs.io/en/stable/manual.html#str-packed-r-tree
        
        get cartesian product:
        https://stackoverflow.com/a/34032549

        Use tolerance setting in snap for near-identical shared paths.
        Uuse snap to catch TopologyException for non-noded intersections
        """

        # first create list with all combinations of lines
        line_combs = list(itertools.combinations(data["linestrings"], 2))

        # iterate over line combinations
        for geoms in line_combs:
            g1 = geoms[0]
            g2 = geoms[1]
            # check if geometry are equal
            # being equal meaning the geometry object coincide with each other.
            # a rotated polygon or reversed linestring are both considered equal.
            if not g1.equals(g2):
                # geoms are unique, let's find junctions
                self.shared_segs(g1, g2)

        # self.segments are nested lists of LineStrings, get coordinates of each nest
        s_coords = []
        for segment in self.segments:
            s_coords.extend([[y for x in segment for y in list(x.coords)]])

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
        # # prepare to return object
        data["junctions"] = self.junctions

        return data


def _joiner(data):
    data = copy.deepcopy(data)
    Join = _Join()
    j = Join.main(data)
    return j
