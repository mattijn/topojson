# pylint: disable=unsubscriptable-object
from shapely import geometry
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
        shared paths with the opposite direction for the two inputs.

        The returned object extents the `segments` property with detected segments.
        Where each seperate segment is a linestring between two points.
        """

        fw_bw = shared_paths(g1, g2)
        if not fw_bw.is_empty:

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

            self.segments.extend(list(shared_segments))

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
        
        After decomposing all geometric objects into linestrings it is necessary to detect
        the junctions or start and end-points of shared paths so this paths can be 'merged'
        in the next step. Merge is quoted as in facht only one of the shared path is kept and 
        the other will be removed.

        Developping Notes:
        * why not de-duplicate (dedup) equal geometries in this object/function? 
        Current approach is to record them and deal with it, maybe combined, in `cut` or `dedup` phase.

        The following links have been used as referene in creating this object/functions.
        TODO: delete when needed.
        
        to find shared paths:
        https://shapely.readthedocs.io/en/stable/manual.html#shared-paths
        
        to set up a R-tree:
        https://shapely.readthedocs.io/en/stable/manual.html#str-packed-r-tree
        
        get cartesian product:
        https://stackoverflow.com/a/34032549
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
            # its quid pro quo to record equal geoms here. Let's leave it up to next phases

        # self.segments is a list of LineStrings, get all coordinates
        s_coords = [y for x in self.segments for y in list(x.coords)]

        # only keep junctions that appear only once
        # coordinates that appear multiple times are not junctions
        self.junctions = [geometry.Point(i) for i in s_coords if s_coords.count(i) is 1]

        # prepare to return object
        data["junctions"] = self.junctions

        return data


def _joiner(data):
    data = copy.deepcopy(data)
    Join = _Join()
    j = Join.main(data)
    return j
