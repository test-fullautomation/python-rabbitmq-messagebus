"""The header module."""

from numpy import uint32, float64


class Header():  # pylint: disable=R0903:too-few-public-methods
    """The header class."""

    __slots__ = ('seq', 'timestamp',)

    def __init__(self, seq: uint32 = 0, timestamp: float64 = 0.):
        """Initialize."""
        # sequence ID: consecutively increasing ID
        self.seq = seq
        # seconds since epoch
        self.timestamp = timestamp
