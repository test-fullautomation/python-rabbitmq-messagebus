"""The uint32 message module."""

from numpy import uint32
from .msg import Msg


class UInt32Msg(Msg):
    """The uint32 message class."""

    __slots__ = ('data',)

    def __init__(self, data: uint32 = 0):
        """Initialize."""
        super().__init__()
        self.data = data

    def __eq__(self, other):
        if isinstance(other, (int, uint32)):
            return self.data == other
        if isinstance(other, UInt32Msg):
            return self.data == other.data
        raise NotImplementedError()
