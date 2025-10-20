"""The string message module."""

from .msg import Msg


class StringMsg(Msg):
    """The string message class."""

    __slots__ = ('data',)

    def __init__(self, data: str = ""):
        """Initialize."""
        super().__init__()
        self.data = data

    def __eq__(self, other):
        if isinstance(other, str):
            return self.data == other
        if isinstance(other, StringMsg):
            return self.data == other.data
        raise NotImplementedError()
