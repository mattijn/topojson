# from .extract import Extract
# from .join import Join
# from .cut import Cut
# from .dedup import Dedup
from .hashmap import Hashmap

# import copy


class Topology(Hashmap):
    """
    dedup duplicates and merge contiguous arcs
    """

    def __init__(
        self,
        data,
        snap_vertices=False,
        snap_value_gridsize=1e6,
        simplify=False,
        simplify_factor=1,
    ):
        # first set the input settings data objects
        topo_setting_keys = (
            "snap_vertices",
            "simplify",
            "snap_value_gridsize",
            "simplify_factor",
        )
        self.settings = dict.fromkeys(topo_setting_keys)
        self.settings.update({"snap_vertices": snap_vertices})
        self.settings.update({"simplify": simplify})
        self.settings.update({"snap_value_gridsize": snap_value_gridsize})
        self.settings.update({"simplify_factor": simplify_factor})

        # execute previous step
        self.topology = super().__init__(data)

        # do something after hashmapping in necessary


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

