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
# File: fanout_handler.py
#
# Initially created by Nguyen Huynh Tri Cuong (MS/EMC51) / Dec 2025.
#
# Description:
#
#   FanoutExchangeHandler: Handles fanout-based message exchanges.
#
# History:
#
# 17.12.2025 / V 1.0.0 / Nguyen Huynh Tri Cuong
# - Initialize
#
# *******************************************************************************
import asyncio
from typing import Callable, Type, Optional
from EventBusClient.exchange_handler.base import ExchangeHandler
from EventBusClient.publisher import AsyncPublisher
from EventBusClient.subscriber import AsyncSubscriber
from EventBusClient.message.base_message import BaseMessage
from EventBusClient.connection import ConnectionManager


class FanoutExchangeHandler(ExchangeHandler):
   _EXCHANGE_TYPE = "fanout"

   def __init__(self, name: str = None, serializer=None, loop: asyncio.AbstractEventLoop = None):
       """
Initialize the FanoutExchangeHandler with the given exchange name, serializer, and event loop.

**Arguments:**

* ``name``

  / *Condition*: optional / *Type*: str /

  The name of the fanout exchange. If not provided, a default name will be used.

* ``serializer``

  / *Condition*: optional / *Type*: Serializer /

  The serializer used for message serialization and deserialization. If not provided, a default serializer will be used.

* ``loop``

  / *Condition*: optional / *Type*: asyncio.AbstractEventLoop /

  The event loop to use for asynchronous operations. If not provided, the default event loop will be used.
       """
       super().__init__(name, serializer, loop)

   @ExchangeHandler.with_alternate_exchange
   async def setup(self, connection_manager: ConnectionManager):
      """
Set up the exchange handler by establishing a channel and declaring the exchange.
This method is called by the EventBusClient during initialization.
It initializes the channel and exchange, and prepares the publisher for sending messages.

**Arguments:**

* ``connection_manager``

  / *Condition*: required / *Type*: ConnectionManager /

  The connection manager used to get the channel and exchange for publishing messages.
      """
      self._channel = await connection_manager.get_channel()
      self._exchange = await self._channel.declare_exchange(
            self.exchange_name,
            self._EXCHANGE_TYPE,
            durable=True,
            auto_delete=False,
            arguments=self.declare_args if self.declare_args else None
      )
      self._publisher = AsyncPublisher(self._channel, self._exchange, self._serializer)
      self._connection = connection_manager
      await super().setup(connection_manager)

   async def publish(self, message: BaseMessage, routing_key="", headers: dict = None, threadsafe: bool = False, mandatory: bool = False):
      """
Publish a message to the exchange with the specified routing key.

**Arguments:**

* ``message``

  / *Condition*: required / *Type*: BaseMessage /

  The message to be published. It should be an instance of BaseMessage or its subclasses.

* ``routing_key``

  / *Condition*: required / *Type*: str /

  The routing key used to route the message to the appropriate subscribers.

*  ``headers``

  / *Condition*: optional / *Type*: dict /

  Additional headers to include with the message. This can be used for metadata or routing information.

* ``threadsafe``

  / *Condition*: optional / *Type*: bool / *Default*: False /

  If True, the publish operation will be executed in a thread-safe manner, allowing it to be called from non-async contexts.

* ``mandatory``

  / *Condition*: optional / *Type*: bool / *Default*: False /

  If True, the message must be routed to at least one queue. If it cannot be routed, it will be returned to the publisher.
      """
      mandatory = self._unroutable_policy == "return"
      if threadsafe:
         future = asyncio.run_coroutine_threadsafe(
                self._publisher.publish(message, routing_key="", headers=headers, mandatory=mandatory),
                loop=self._loop
         )
         return await asyncio.wrap_future(future)
      else:
         await self._publisher.publish(message, routing_key="", headers=headers, mandatory=mandatory)
         return None

   async def subscribe(
        self,
        routing_key: str = "",
        message_cls: Type[BaseMessage] = None,
        callback: Callable[[BaseMessage], None] = None,
        cache_size: Optional[int] = None
   ):
      """
 Subscribe to messages on the exchange with the specified routing key.

 **Arguments:**

 * ``routing_key``

   / *Condition*: required / *Type*: str /

   The routing key used to filter messages for this subscriber.

 * ``message_cls``

   / *Condition*: required / *Type*: Type[BaseMessage] /

   The class of the message that this subscriber will handle. It should be a subclass of BaseMessage.

 * ``callback``

   / *Condition*: required / *Type*: Callable[[BaseMessage], None] /

   The callback function that will be called when a message matching the routing key is received.
      """
      subscriber = AsyncSubscriber(
            channel=self._channel,
            exchange=self._exchange,
            routing_key="",  # Fanout ignores routing key
            message_cls=message_cls,
            callback=callback,
            serializer=self._serializer
      )
      cache = await subscriber.start(cache_size=cache_size)
      self._subscribers.append(subscriber)
      return cache
