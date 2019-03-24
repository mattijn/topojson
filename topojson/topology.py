from .extract import Extract
from .join import Join
from .cut import Cut
from .dedup import Dedup
from .hashmap import Hashmap
import copy


def topology(
    data, snap_vertices=False, gridsize_to_snap=1e6, simplify=False, simplify_factor=1
):
    # initialize classes
    extractor = Extract()
    joiner = Join()
    cutter = Cut()
    deduper = Dedup()
    hashmapper = Hashmap()

    # copy data
    try:
        data = copy.deepcopy(data)
    except:
        data = data.copy()

    # apply topology to data
    data = extractor.main(data)

    if snap_vertices:
        data = joiner.main(data, quant_factor=gridsize_to_snap)
    else:
        data = joiner.main(data, quant_factor=None)

    data = cutter.main(data)
    data = deduper.main(data)
    if simplify:
        data = hashmapper.main(data, simplify_factor=simplify_factor)
    else:
        data = hashmapper.main(data, simplify_factor=None)

    return data

