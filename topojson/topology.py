from topojson.extract import _Extract
from topojson.join import _Join
from topojson.cut import _Cut
from topojson.dedup import _Dedup
from topojson.hashmap import _Hashmap
import copy


def _topology(data, quant_factor=None):
    # initialize classes
    Extract = _Extract()
    Join = _Join()
    Cut = _Cut()
    Dedup = _Dedup()
    Hashmap = _Hashmap()

    # copy data
    data = copy.deepcopy(data)

    # apply topology to data
    data = Extract.main(data)
    data = Join.main(data, quant_factor)
    data = Cut.main(data)
    data = Dedup.main(data)
    data = Hashmap.main(data)

    return data

