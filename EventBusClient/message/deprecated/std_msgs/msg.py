"""The base message module."""

import pickle

from .header import Header


class Msg():
    """The base message class."""

    __slots__ = ('header',)

    def __init__(self):
        """Initialize."""
        self.header = Header()

    def __eq__(self, other):
        raise NotImplementedError()

    def serialize(self) -> bytes:
        """Serialize."""
        return pickle.dumps(self, -1)

    @classmethod
    def deserialize(cls, data):
        """Deserialize."""
        return pickle.loads(data)
