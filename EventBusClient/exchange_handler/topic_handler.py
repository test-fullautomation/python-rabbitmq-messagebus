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
# File: topic_handler.py
#
# Initially created by Nguyen Huynh Tri Cuong (MS/EMC51) / July 2025.
#
# Description:
#
#   TopicExchangeHandler: Handles topic-based message exchanges.
#
# History:
#
# 17.07.2025 / V 1.0.0 / Nguyen Huynh Tri Cuong
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


class TopicExchangeHandler(ExchangeHandler):
   _EXCHANGE_TYPE = "topic"

   def __init__(self, name: str = None, serializer=None, loop: asyncio.AbstractEventLoop = None):
      super().__init__(name, serializer, loop)

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
      # self._exchange = await connection_manager.get_exchange()
      self._exchange = await self._channel.declare_exchange(
         self.exchange_name,
         self._EXCHANGE_TYPE,
         durable=True,
         auto_delete=False
      )
      self._publisher = AsyncPublisher(self._channel, self._exchange, self._serializer)

   async def publish(self, message: BaseMessage, routing_key: str, headers: dict = None, threadsafe: bool = False):
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
      """
      if threadsafe:
         future = asyncio.run_coroutine_threadsafe(
            self._publisher.publish(message, routing_key, headers),
            loop=self._loop
         )
         return await asyncio.wrap_future(future)  # Await result
      else:
         await self._publisher.publish(message, routing_key, headers)
         return None

   async def subscribe(
      self,
      routing_key: str,
      message_cls: Type[BaseMessage],
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
         routing_key=routing_key,
         message_cls=message_cls,
         callback=callback,
         serializer=self._serializer
      )
      # await subscriber.start()
      # self._subscribers.append(subscriber)

      cache = await subscriber.start(cache_size=cache_size)
      # optionally remember sub for later unsubscribe
      # self._subs[(topic, msg_cls)] = sub
      self._subscribers.append(subscriber)
      return cache

#    async def teardown(self):
#       """
# Teardown the exchange handler by stopping all subscribers and clearing the list of subscribers.
#       """
#       for subscriber in self._subscribers:
#          await subscriber.stop()
#       self._subscribers.clear()
#       await super().teardown()


if __name__ == "__main__":
   print("test")