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
# File: subscriber.py
#
# Initially created by Nguyen Huynh Tri Cuong (MS/EMC51) / July 2025.
#
# Description:
#
#    AsyncSubscriber: Subscribes to messages from an exchange using aio_pika.
#
# History:
#
# 17.07.2025 / V 1.0.0 / Nguyen Huynh Tri Cuong
# - Initialize
#
# *******************************************************************************
import asyncio
import aio_pika
from typing import Any, Callable, Optional, Type
from aio_pika.abc import AbstractIncomingMessage
from EventBusClient.serializer.base_serializer import Serializer
from EventBusClient.serializer.pickle_serializer import PickleSerializer
from EventBusClient.message.base_message import BaseMessage
from .subscription_cache import SubscriptionCache


class AsyncSubscriber:
   """
AsyncSubscriber: Subscribes to messages from an exchange using aio_pika.
   """
   def __init__(
      self,
      channel: aio_pika.abc.AbstractChannel,
      exchange: aio_pika.abc.AbstractExchange,
      routing_key: str,
      message_cls: Type[BaseMessage],
      callback: Callable[[BaseMessage], None] = None,
      serializer: Serializer = None,
      cache_size_default: int = 200
   ):
      """
AsyncSubscriber: Initializes the subscriber with a channel, exchange, routing key, message class, callback, and optional serializer.

**Arguments:**

* ``channel``

  / *Condition*: required / *Type*: aio_pika.abc.AbstractChannel /

  The channel to subscribe to messages on.

* ``exchange``

  / *Condition*: required / *Type*: aio_pika.abc.AbstractExchange /

  The exchange to subscribe to messages from.

* ``routing_key``

  / *Condition*: required / *Type*: str /

  The routing key to filter messages.

* ``message_cls``

  / *Condition*: required / *Type*: Type[BaseMessage] /

  The class of the message to be processed. It should be a subclass of BaseMessage.

* ``callback``

  / *Condition*: required / *Type*: Callable[[BaseMessage], None] /

  The callback function to process the received messages. It should accept an instance of BaseMessage or its subclasses.

* ``serializer``

  / *Condition*: optional / *Type*: Serializer /

  The serializer used to deserialize messages. Defaults to PickleSerializer if not provided.
      """
      self._channel = channel
      self._exchange = exchange
      self._routing_key = routing_key
      self._callback = callback
      self._message_cls = message_cls
      self._serializer = serializer or PickleSerializer()

      self._queue: aio_pika.abc.AbstractQueue | None = None
      self._consumer_tag: str | None = None
      self._cache: Optional[SubscriptionCache[Any]] = None
      self._cache_default = cache_size_default

   @property
   def cache(self) -> SubscriptionCache[Any]:
      if self._cache is None:
         self._cache = SubscriptionCache(maxlen=self._cache_default)
      return self._cache

   async def start(self, cache_size: Optional[int] = None):
      """
Start the subscriber by declaring a queue, binding it to the exchange, and consuming messages.
      """
      self._queue = await self._channel.declare_queue(
         name="",
         exclusive=True,
         auto_delete=True
      )
      self._cache = SubscriptionCache(maxlen=cache_size or self._cache_default)
      await self._queue.bind(self._exchange, routing_key=self._routing_key)
      self._consumer_tag = await self._queue.consume(self._on_message)
      return self._cache

   async def stop(self):
      """
Stop the subscriber by canceling the consumer, unbinding the queue from the exchange, and deleting the queue.
      """
      try:
         if self._queue and self._consumer_tag:
            # Cancel consumer first to stop message delivery
            await self._queue.cancel(self._consumer_tag)
            self._consumer_tag = None

         # For exclusive+auto_delete queues, unbinding and deletion are optional
         # but we'll do it for clean shutdown
         if self._queue:
            try:
               await self._queue.unbind(self._exchange, routing_key=self._routing_key)
            except Exception:
               pass  # Ignore unbind errors

            try:
               await self._queue.delete(if_unused=False, if_empty=False)
            except Exception:
               pass  # Ignore delete errors

            self._queue = None

      except Exception as e:
         print(f"[AsyncSubscriber] Error during stop: {e}")
      finally:
         # Ensure cleanup even if there are errors
         self._consumer_tag = None
         self._queue = None

      # try:
      #    if self._queue and self._consumer_tag:
      #       # stop deliveries first
      #       await self._queue.cancel(self._consumer_tag)
      # except Exception:
      #    pass
      # finally:
      #    self._consumer_tag = None
      #
      #    # For exclusive+auto_delete queues this is optional, but safe:
      # try:
      #    if self._queue:
      #       try:
      #          await self._queue.unbind(self._exchange, routing_key=self._routing_key)
      #       except Exception:
      #          pass
      #       await self._queue.delete(if_unused=False, if_empty=False)
      # except Exception:
      #    pass
      # finally:

   async def _on_message(self, message: AbstractIncomingMessage):
      """
Handle incoming messages by deserializing them and invoking the callback.

**Arguments:**

* ``message``

  / *Condition*: required / *Type*: AbstractIncomingMessage /

  The incoming message to be processed. It should contain the serialized message body.
      """
      async with message.process():
         try:
            obj = self._serializer.deserialize(message.body)
            if self._cache:
               self._cache.append(obj)

            if not isinstance(obj, self._message_cls):
               raise TypeError(f"Expected {self._message_cls}, got {type(obj)}")

            if self._callback:
               if asyncio.iscoroutinefunction(self._callback):
                  await self._callback(obj)
               else:
                  self._callback(obj)
         except Exception as e:
            print(f"[AsyncSubscriber] Error handling message: {e}")

   @property
   def routing_key(self):
       return self._routing_key

   @property
   def callback(self):
       return self._callback

