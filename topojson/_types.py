"""Types of the public API."""

from collections.abc import Sequence
from typing import Literal, TypeAlias, TypedDict


class Transform(TypedDict):
    """A TopoJSON transform: the size of a cell of the grid along each axis
    (`scale`) and its bottom-left corner (`translate`)."""

    scale: Sequence[float]
    translate: Sequence[float]


class Slider(TypedDict, total=False):
    """The settings of a slider of `Topology.to_widget`."""

    min: float
    max: float
    step: float
    value: float
    base: float


Quantize: TypeAlias = bool | float | Transform
Algorithm: TypeAlias = Literal["dp", "vw"]
Package: TypeAlias = Literal["shapely", "simplification", "geos"]
WindingOrder: TypeAlias = Literal["CW_CCW", "CCW_CW"]
