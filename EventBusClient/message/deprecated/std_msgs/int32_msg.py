"""The int32 message module."""

from numpy import int32
from .msg import Msg


class Int32Msg(Msg):
    """The int32 message class."""

    __slots__ = ('data',)

    def __init__(self, data: int32 = 0):
        """Initialize."""
        super().__init__()
        self.data = data

    def __eq__(self, other):
        if isinstance(other, (int, int32)):
            return self.data == other
        if isinstance(other, Int32Msg):
            return self.data == other.data
        raise NotImplementedError()
