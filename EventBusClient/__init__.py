# from .event_bus_client import EventBusClient
# from .connection import ConnectionManager
# from .publisher import AsyncPublisher
# from .subscriber import AsyncSubscriber
# from .message import BaseMessage, Header
# from .serializer.base import Serializer
from .qlogger import QLogger

LOGGER_NAME = "console"

def get_logger():
    return QLogger().get_logger(LOGGER_NAME)

LOGGER = get_logger()