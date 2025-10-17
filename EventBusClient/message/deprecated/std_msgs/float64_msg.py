"""The float64 message module."""

from numpy import float64
from .msg import Msg


class Float64Msg(Msg):
    """The float64 message class."""

    __slots__ = ('data',)

    def __init__(self, data: float64 = 0.):
        """Initialize."""
        super().__init__()
        self.data = data

    def __eq__(self, other):
        if isinstance(other, (float, float64)):
            return self.data == other
        if isinstance(other, Float64Msg):
            return self.data == other.data
        raise NotImplementedError()
