"""The dict message module."""

from .msg import Msg


class DictMsg(Msg):
    """The dict message class."""

    __slots__ = ('data',)

    def __init__(self, data: dict = {}):
        """Initialize."""
        super().__init__()
        self.data = data

    def __eq__(self, other):
        if isinstance(other, dict):
            return self.data == other
        if isinstance(other, DictMsg):
            return self.data == other.data
        raise NotImplementedError()
