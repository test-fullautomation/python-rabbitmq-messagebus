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
# File: headers_handler.py
#
# Initially created by Nguyen Huynh Tri Cuong (MS/EMC51) / January 2026.
#
# Description:
#
#   HeadersExchangeHandler: Handles headers-based message exchanges.
#   Routes messages based on message header attributes instead of routing keys.
#
# History:
#
# 29.01.2026 / V 1.0.0 / Nguyen Huynh Tri Cuong
# - Initialize
#
# *******************************************************************************
import asyncio
from typing import Callable, Type, Optional, Dict, Any
from EventBusClient.exchange_handler.base import ExchangeHandler
from EventBusClient.publisher import AsyncPublisher
from EventBusClient.subscriber import AsyncSubscriber
from EventBusClient.message.base_message import BaseMessage
from EventBusClient.connection import ConnectionManager
from EventBusClient import LOGGER


class HeadersExchangeHandler(ExchangeHandler):
   """
HeadersExchangeHandler: Handles headers-based message exchanges.

Unlike topic or direct exchanges that route based on routing keys, the headers
exchange routes messages based on header attributes. This allows for more
complex routing logic based on multiple criteria.

**Binding Arguments:**

When subscribing, you can specify header matching criteria:

* ``x-match``: Matching mode
  - ``all``: All specified headers must match (AND logic)
  - ``any``: At least one header must match (OR logic)

* Other key-value pairs: Headers to match against

**Example:**

::

   # Subscribe to messages where format=pdf AND type=report
   await handler.subscribe(
       binding_headers={"x-match": "all", "format": "pdf", "type": "report"},
       message_cls=ReportMessage,
       callback=process_report
   )

   # Publish with matching headers
   await handler.publish(
       message=report,
       routing_key="",  # Ignored for headers exchange
       headers={"format": "pdf", "type": "report", "author": "john"}
   )
   """
   _NAME = "Headers Exchange Handler"
   _EXCHANGE_TYPE = "headers"

   def __init__(self, name: str = None, serializer=None, loop: asyncio.AbstractEventLoop = None):
      """
Initialize the HeadersExchangeHandler.

**Arguments:**

* ``name``

  / *Condition*: optional / *Type*: str /

  The name of the exchange. If not provided, a default name will be generated.

* ``serializer``

  / *Condition*: optional / *Type*: Serializer /

  The serializer used to serialize and deserialize messages.
  Defaults to PickleSerializer if not provided.

* ``loop``

  / *Condition*: optional / *Type*: asyncio.AbstractEventLoop /

  The event loop to use for asynchronous operations.
  If not provided, the current event loop will be used.
      """
      super().__init__(name, serializer, loop)

   @ExchangeHandler.with_alternate_exchange
   async def setup(self, connection_manager: ConnectionManager):
      """
Set up the exchange handler by establishing a channel and declaring the headers exchange.

**Arguments:**

* ``connection_manager``

  / *Condition*: required / *Type*: ConnectionManager /

  The connection manager used to get the channel and exchange for publishing messages.
      """
      self._channel = await connection_manager.get_channel()
      self._exchange = await self._channel.declare_exchange(
         name=self.exchange_name,
         type=self._EXCHANGE_TYPE,
         durable=True,
         auto_delete=False,
         arguments=self.declare_args if self.declare_args else None
      )
      self._publisher = AsyncPublisher(self._channel, self._exchange, self._serializer)
      self._connection = connection_manager
      await super().setup(connection_manager)
      LOGGER.info(f"HeadersExchangeHandler setup complete for exchange: {self.exchange_name}")

   async def publish(
      self,
      message: BaseMessage,
      routing_key: str = "",
      headers: dict = None,
      threadsafe: bool = False,
      mandatory: bool = False
   ):
      """
Publish a message to the headers exchange.

Note: For headers exchanges, the routing_key is typically ignored.
Routing is determined by the headers parameter matching subscriber bindings.

**Arguments:**

* ``message``

  / *Condition*: required / *Type*: BaseMessage /

  The message to be published.

* ``routing_key``

  / *Condition*: optional / *Type*: str /

  The routing key (typically ignored for headers exchange, can be empty string).

* ``headers``

  / *Condition*: optional / *Type*: dict /

  Headers used for routing. These are matched against subscriber binding headers.
  This is the primary routing mechanism for headers exchanges.

* ``threadsafe``

  / *Condition*: optional / *Type*: bool /

  If True, the publish operation will be thread-safe.

* ``mandatory``

  / *Condition*: optional / *Type*: bool /

  If True, the message will be returned if it cannot be routed.
      """
      mandatory = self._unroutable_policy == "return"
      if threadsafe:
         try:
            running = asyncio.get_running_loop()
         except RuntimeError:
            running = None

         if running is not self._loop:
            LOGGER.info(f"Publishing message with headers: {headers} in a thread-safe manner")
            future = asyncio.run_coroutine_threadsafe(
               self._publisher.publish(message, routing_key, headers, mandatory=mandatory),
               loop=self._loop
            )
            result = await asyncio.wrap_future(future)
            return result

      await self._publisher.publish(message, routing_key, headers, mandatory=mandatory)
      LOGGER.debug(f"Published message with headers: {headers}")
      return None

   async def subscribe(
      self,
      routing_key: str = "",
      message_cls: Type[BaseMessage] = None,
      callback: Callable[[BaseMessage, Dict[str, Any]], None] = None,
      cache_size: Optional[int] = None,
      binding_headers: Optional[Dict[str, Any]] = None
   ):
      """
Subscribe to messages on the headers exchange based on header matching.

**Arguments:**

* ``routing_key``

  / *Condition*: optional / *Type*: str /

  The routing key (typically ignored for headers exchange, can be empty string).

* ``message_cls``

  / *Condition*: required / *Type*: Type[BaseMessage] /

  The class of the message that this subscriber will handle.

* ``callback``

  / *Condition*: optional / *Type*: Callable[[BaseMessage, Dict], None] /

  The callback function called when a matching message is received.

* ``cache_size``

  / *Condition*: optional / *Type*: int /

  Maximum size of the subscription cache.

* ``binding_headers``

  / *Condition*: optional / *Type*: Dict[str, Any] /

  Headers to match for this subscription. Should include:
  - ``x-match``: "all" (all headers must match) or "any" (at least one must match)
  - Other key-value pairs to match against message headers

  Example: {"x-match": "all", "format": "pdf", "priority": "high"}

**Returns:**

  / *Type*: SubscriptionCache /

  A cache object for accessing received messages synchronously.
      """
      subscriber = AsyncSubscriber(
         channel=self._channel,
         exchange=self._exchange,
         routing_key=routing_key,
         message_cls=message_cls,
         callback=callback,
         serializer=self._serializer,
         binding_arguments=binding_headers
      )

      cache = await subscriber.start(cache_size=cache_size)
      self._subscribers.append(subscriber)
      LOGGER.info(f"Subscribed with binding headers: {binding_headers}")
      return cache

   async def subscribe_with_headers(
      self,
      binding_headers: Dict[str, Any],
      message_cls: Type[BaseMessage],
      callback: Callable[[BaseMessage, Dict[str, Any]], None] = None,
      cache_size: Optional[int] = None,
      match_all: bool = True
   ):
      """
Convenience method to subscribe with header-based routing.

**Arguments:**

* ``binding_headers``

  / *Condition*: required / *Type*: Dict[str, Any] /

  Headers to match (without x-match key, which is set by match_all parameter).

* ``message_cls``

  / *Condition*: required / *Type*: Type[BaseMessage] /

  The class of the message that this subscriber will handle.

* ``callback``

  / *Condition*: optional / *Type*: Callable /

  The callback function called when a matching message is received.

* ``cache_size``

  / *Condition*: optional / *Type*: int /

  Maximum size of the subscription cache.

* ``match_all``

  / *Condition*: optional / *Type*: bool / *Default*: True /

  If True, all headers must match (x-match=all).
  If False, any header can match (x-match=any).

**Returns:**

  / *Type*: SubscriptionCache /

  A cache object for accessing received messages synchronously.
      """
      headers_with_match = {"x-match": "all" if match_all else "any"}
      headers_with_match.update(binding_headers)
      return await self.subscribe(
         routing_key="",
         message_cls=message_cls,
         callback=callback,
         cache_size=cache_size,
         binding_headers=headers_with_match
      )
