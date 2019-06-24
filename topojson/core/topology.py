import pprint
import json
from .hashmap import Hashmap


class Topology(Hashmap):
    """
    dedup duplicates and merge contiguous arcs
    """

    def __init__(self, data, **kwargs):

        # execute previous steps
        super().__init__(data, **kwargs)

        # do something after hashmapping in necessary

    def __repr__(self):
        return "Topology(\n{}\n)".format(pprint.pformat(self.output))

    def to_dict(self):
        return self.output

    def to_json(self):
        return json.dumps(self.output)


# def topology(
#     data, snap_vertices=False, snap_value_gridsize=1e6, simplify=False, simplify_factor=1
# ):


#     # execute the topoloy
#     super().__init__(data)


#     # initialize classes
#     extractor = Extract()
#     joiner = Join()
#     cutter = Cut()
#     deduper = Dedup()
#     hashmapper = Hashmap()

#     # copy data
#     try:
#         data = copy.deepcopy(data)
#     except:
#         data = data.copy()

#     # apply topology to data
#     data = extractor.main(data)

#     if snap_vertices:
#         data = joiner.main(data, quant_factor=gridsize_to_snap)
#     else:
#         data = joiner.main(data, quant_factor=None)

#     data = cutter.main(data)
#     data = deduper.main(data)
#     if simplify:
#         data = hashmapper.main(data, simplify_factor=simplify_factor)
#     else:
#         data = hashmapper.main(data, simplify_factor=None)

#     return data

