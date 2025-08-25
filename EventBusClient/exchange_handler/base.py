#  Copyright 2020-2025 Robert Bosch GmbH
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
# *******************************************************************************
#
# File: base.py
#
# Initially created by Nguyen Huynh Tri Cuong (MS/EMC51) / July 2025.
#
# Description:
#
#   Base class for exchange handlers in the event bus system.
#
# History:
#
# 17.07.2025 / V 1.0.0 / Nguyen Huynh Tri Cuong
# - Initialize
#
# *******************************************************************************
import asyncio
# import  logging
from abc import ABC, abstractmethod
from EventBusClient.message.base_message import BaseMessage
from EventBusClient.publisher import AsyncPublisher
from EventBusClient.subscriber import AsyncSubscriber
from typing import Type, Optional
from EventBusClient.qlogger import QLogger

# logger = logging.getLogger(__name__)
logger = QLogger().get_logger("event_bus_client")

class ExchangeHandler(ABC):
   _EXCHANGE_TYPE = "ExchangeHandler"

   _instance_number = 0

   def __init__(self, name: str = None, serializer=None, loop: asyncio.AbstractEventLoop = None):
      """
ExchangeHandler: Initializes the exchange handler with a name, serializer, and event loop.

**Arguments:**

* ``name``

  / *Condition*: optional / *Type*: str /

  The name of the exchange handler. If not provided, it defaults to a generated name based on the class type and instance number.

* ``serializer``

  / *Condition*: optional / *Type*: Serializer /

  The serializer used to serialize and deserialize messages. If not provided, it defaults to None.

* ``loop``

  / *Condition*: optional / *Type*: asyncio.AbstractEventLoop /

  The event loop to use for asynchronous operations. If not provided, the current event loop will be used.
      """
      self.exchange_name = name if name is not None else f"{self._EXCHANGE_TYPE}_{getattr(self.__class__, '_instance_number', 0)}"
      self.__class__._instance_number += 1
      self.exchange_type = self._EXCHANGE_TYPE
      self._loop = loop or asyncio.get_event_loop()
      self._serializer = serializer
      self._channel = None
      self._exchange = None
      self._publisher = None
      self._connection = None
      self._subscribers: list[AsyncSubscriber] = []

   @abstractmethod
   async def setup(self, connection_manager):
      """
Set up the exchange handler by establishing a channel and declaring the exchange.

**Arguments:**

* ``connection_manager``

  / *Condition*: required / *Type*: ConnectionManager /

  The connection manager used to get the channel and exchange for publishing messages.
      """
      connection_manager.register_exchange_handler(self)

   async def teardown(self):
      """
Tear down the exchange handler by closing the channel and cleaning up resources.
      """
      for subscriber in self._subscribers:
         await subscriber.stop()
         logger.info(f"Unsubscribed {len(self._subscribers)} subscribers.")
      self._subscribers.clear()

      # if self._exchange:
      #    await self._exchange.delete()
      #    self._exchange = None

      if self._connection:
         self._connection.unregister_exchange_handler(self)

   @abstractmethod
   async def publish(self, message: BaseMessage, routing_key: str, headers: dict = None, threadsafe: bool = False): ...

   @abstractmethod
   async def subscribe(self, routing_key: str, message_cls: Type[BaseMessage], callback, cache_size: Optional[int]): ...

   async def unsubscribe(self, routing_key: str, callback):
      """
Unsubscribe a callback from a specific routing key.

**Arguments:**

* ``routing_key``

  / *Condition*: required / *Type*: str /

  The routing key to unsubscribe from.

* ``callback``

  / *Condition*: required / *Type*: Callable /

  The callback function to remove from the subscriber list.
      """
      for subscriber in self._subscribers:
         if subscriber.routing_key == routing_key and subscriber.callback == callback:
            await subscriber.stop()
            self._subscribers.remove(subscriber)
            logger.info(f"Unsubscribed callback from routing key: {routing_key}")
            break
      else:
         logger.warning(f"No subscriber found for routing key: {routing_key} with the given callback.")

   async def handle_channel_close(self, exc: Exception = None):
      """
Handle channel closure by attempting to re-create the channel.

**Arguments:**

* ``exc``

  / *Condition*: optional / *Type*: Exception /

  The exception that caused the channel to close, if any. If not provided, it defaults to None.
      """
      logger.info(f"[ConnectionManager] Channel closed. Exception: {exc} \nAttempting to re-create channel...")
      if self._connection and not self._connection.is_closed:
         self._channel = await self.setup(self._connection)
         self._channel.close_callbacks.add(
            lambda expt: asyncio.create_task(self.handle_channel_close(expt)))
         await self._channel.set_qos(prefetch_count=10)
         logger.info("[ConnectionManager] Channel re-created successfully.")