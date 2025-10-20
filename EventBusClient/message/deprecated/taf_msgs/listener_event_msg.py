"""The listener event message module."""

from numpy import float64
from EventBusClient.message.deprecated.std_msgs import Msg
from .listener_event_indexer import EventIndex


class ListenerEventMsg(Msg):
    """The listener event message class."""

    __slots__ = ('event', 'timestamp',)

    def __init__(self, event=EventIndex(), timestamp: float64 = 0.):
        """Initialize."""
        super().__init__()
        self.event = event
        self.timestamp = timestamp

    def __eq__(self, other):
        if isinstance(other, tuple):
            return self.event == other[0] and \
                self.timestamp == other[1]
        if isinstance(other, ListenerEventMsg):
            return self.event == other.event and \
                self.timestamp == other.timestamp
        raise NotImplementedError()
