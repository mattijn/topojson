# pylint: disable=unsubscriptable-object
import copy
import pprint
import numpy as np
from shapely import geometry
from shapely.errors import ShapelyError
from shapely.wkb import loads
from shapely.ops import shared_paths
from shapely.ops import linemerge
from shapely.set_operations import intersection_all
import shapely
from ..ops import select_unique_combs
from ..ops import simplify
from ..ops import quantize
from ..ops import bounds
from ..ops import compare_bounds
from ..ops import asvoid
from ..ops import explode
from ..utils import serialize_as_svg
from .extract import Extract


class Join(Extract):
    """
    This class targets the following objectives:
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

    def __init__(self, data, options={}):
        # execute previous step
        super().__init__(data, options)

        # initiation topology items
        self._junctions = []
        self._segments = []
        self._valerr = False

        # execute main function
        self.output = self._joiner(self.output)

    def __repr__(self):
        return "Join(\n{}\n)".format(pprint.pformat(self.output))

    def to_dict(self):
        """
        Convert the Join object to a dictionary.
        """
        topo_object = copy.copy(self.output)
        topo_object["options"] = vars(self.options)
        return topo_object

    def to_svg(self, separate=False, include_junctions=False):
        """
        Display the linestrings and junctions as SVG.

        Parameters
        ----------
        separate : boolean
            If `True`, each of the linestrings will be displayed separately.
            Default is `False`
        include_junctions : boolean
            If `True`, the detected junctions will be displayed as well.
            Default is `False`
        """
        serialize_as_svg(self.output, separate, include_junctions)

    def _joiner(self, data):
        """
        Entry point for the class Join. This function identifies junctions
        (intersection points) of shared paths.

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

        # presimplify linestrings if required
        if self.options.presimplify > 0:
            # set default if not specifically given in the options
            if type(self.options.presimplify) == bool:
                simplify_factor = 2
            else:
                simplify_factor = self.options.presimplify

            data["linestrings"] = simplify(
                data["linestrings"],
                simplify_factor,
                algorithm=self.options.simplify_algorithm,
                package=self.options.simplify_with,
                input_as="linestring",
                prevent_oversimplify=self.options.prevent_oversimplify,
            )

        # compute the bounding box of input geometry
        lsbs = bounds(data["linestrings"])
        ptbs = bounds(data["coordinates"])
        data["bbox"] = compare_bounds(lsbs, ptbs)

        if not data["linestrings"] and not data["coordinates"]:
            data["junctions"] = self._junctions
            return data

        # prequantize linestrings if required
        if self.options.prequantize > 0:
            # set default if not specifically given in the options
            if type(self.options.prequantize) == bool:
                quant_factor = 1e6
            else:
                quant_factor = self.options.prequantize

            data["linestrings"], data["transform"] = quantize(
                data["linestrings"], data["bbox"], quant_factor
            )

            data["coordinates"], data["transform"] = quantize(
                data["coordinates"], data["bbox"], quant_factor
            )

        if not self.options.topology or not data["linestrings"]:
            data["junctions"] = self._junctions
            return data

        if self.options.shared_coords:

            def _get_verts(geom):
                # get coords of each LineString
                return [x for x in geom.coords]

            geoms = {}
            junctions = []

            for ls in data["linestrings"]:
                verts = _get_verts(ls)
                for i, vert in enumerate(verts):
                    ran = geoms.pop(vert, None)
                    neighs = sorted(
                        [verts[i - 1], verts[i + 1 if i < len(verts) - 1 else 0]]
                    )
                    if ran and ran != neighs:
                        junctions.append(vert)
                    geoms[vert] = neighs

            self._junctions = [geometry.Point(xy) for xy in set(junctions)]
        else:

            idx_combs, tree = select_unique_combs(data["linestrings"])
            # collect geoms from tree (this are views or copies?)
            geom_combs = np.asarray(
                [
                    [tree.geometries.take(idx[0]), tree.geometries.take(idx[1])]
                    for idx in idx_combs
                ]
            )

            # find intersection between linestrings
            segments = intersection_all(geom_combs, axis=1)
            merged_segments = explode(shapely.line_merge(segments))

            # the start and end points of the merged_segments are the junctions
            coords, index_group_coords = shapely.get_coordinates(
                merged_segments, return_index=True
            )
            _, idx_start_segment = np.unique(index_group_coords, return_index=True)
            idx_start_end = np.append(idx_start_segment, idx_start_segment - 1)

            junctions = coords[idx_start_end]
            # junctions can appear multiple times in multiple segments, remove duplicates
            _, idx_uniq_junction = np.unique(asvoid(junctions), return_index=True)
            self._junctions = list(map(geometry.Point, junctions[idx_uniq_junction]))

        # prepare to return object
        data["junctions"] = self._junctions

        return data

    def _validate_linemerge(self, merged_line):
        """
        Return list of linestrings. If the linemerge was a MultiLineString
        then returns a list of multiple single linestrings
        """

        if not isinstance(merged_line, geometry.LineString):
            merged_line = [ls for ls in merged_line.geoms]
        else:
            merged_line = [merged_line]
        return merged_line

    def _shared_segs(self, g1, g2):
        """
        This function returns the segments that are shared with two input geometries.
        The shapely function `shapely.ops.shared_paths()` is adopted and can catch
        both the shared paths with the same direction for both inputs as well as the
        shared paths with the opposite direction for one the two inputs.

        The returned object extents the `segments` property with detected segments.
        Where each separate segment is a linestring between two points.

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
        except (ShapelyError, ValueError):
            self._valerr = True
            fw_bw = False

        # continue if any shared path was detected
        if fw_bw and not fw_bw.is_empty:

            forward = fw_bw.geoms[0]
            backward = fw_bw.geoms[1]

            if backward.is_empty:
                # only contains forward objects
                shared_segments = forward
            elif forward.is_empty:
                # only contains backward objects
                shared_segments = backward
            else:
                # both backward and forward contains objects, so combine
                forward = self._validate_linemerge(linemerge(forward))
                backward = self._validate_linemerge(linemerge(backward))

                shared_segments = geometry.MultiLineString(forward + backward)

            # add shared paths to segments
            self._segments.extend([list(shared_segments.geoms)])

            # also add the first coordinates of both geoms as a vertices to segments
            p1_g1 = geometry.Point([g1.xy[0][0], g1.xy[1][0]])
            p1_g2 = geometry.Point([g2.xy[0][0], g2.xy[1][0]])
            ls_p1_g1g2 = geometry.LineString([p1_g1, p1_g2])
            self._segments.extend([[ls_p1_g1g2]])
