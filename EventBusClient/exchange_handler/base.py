# pylint: disable=C0115
# pylint: disable=C0116
# pylint: disable=W0311
import asyncio
from abc import ABC, abstractmethod
from message.base_message import BaseMessage
from publisher import AsyncPublisher
from subscriber import AsyncSubscriber
from typing import Callable, Type

# print("test")
class ExchangeHandler(ABC):
   _EXCHANGE_TYPE = "ExchangeHandler"

   _instance_number = 0

   def __init__(self, name: str = None, serializer=None, loop: asyncio.AbstractEventLoop = None):
      self.exchange_name = name if name is not None else f"{self._EXCHANGE_TYPE}_{getattr(self.__class__, '_instance_number', 0)}"
      self.__class__._instance_number += 1
      self.exchange_type = self._EXCHANGE_TYPE
      self._loop = loop or asyncio.get_event_loop()
      self._serializer = serializer
      self._channel = None
      self._exchange = None
      self._publisher = None
      self._subscribers: list[AsyncSubscriber] = []

   @abstractmethod
   async def setup(self, connection_manager): ...

   @abstractmethod
   async def teardown(self): ...

   @abstractmethod
   async def publish(self, message: BaseMessage, routing_key: str, headers: dict = None, threadsafe: bool = False): ...

   @abstractmethod
   async def subscribe(self, routing_key: str, message_cls: Type[BaseMessage], callback): ...
