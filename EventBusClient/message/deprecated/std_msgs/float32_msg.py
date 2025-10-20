"""The float32 message module."""

from numpy import float32
from .msg import Msg


class Float32Msg(Msg):
    """The float32 message class."""

    __slots__ = ('data',)

    def __init__(self, data: float32 = 0.):
        """Initialize."""
        super().__init__()
        self.data = data

    def __eq__(self, other):
        if isinstance(other, (float, float32)):
            return self.data == other
        if isinstance(other, Float32Msg):
            return self.data == other.data
        raise NotImplementedError()
