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
import threading
import inspect
from typing import Any, Callable, Optional, Type, MutableMapping, Awaitable
from aio_pika.abc import AbstractIncomingMessage
from EventBusClient.serializer.base_serializer import Serializer
from EventBusClient.serializer.pickle_serializer import PickleSerializer
from EventBusClient.message.base_message import BaseMessage
from EventBusClient import LOGGER
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
      callback: Callable[[BaseMessage, MutableMapping[str, Any]], None] | list[Callable[[BaseMessage, MutableMapping[str, Any]], None]] = None,
      serializer: Serializer = None,
      cache_size_default: int = 200,
      callback_isolation: str = "threaded",  # "direct" | "threaded"
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
      self._callback = callback if isinstance(callback, list) else [callback] if callback else []
      self._message_cls = message_cls
      self._serializer = serializer or PickleSerializer()

      self._queue: aio_pika.abc.AbstractQueue | None = None
      self._consumer_tag: str | None = None
      self._cache: Optional[SubscriptionCache[Any]] = None
      self._cache_default = cache_size_default

      self._callback_isolation = callback_isolation

      # Dedicated callback loop/thread (used only if isolation="threaded")
      self._cb_loop: Optional[asyncio.AbstractEventLoop] = None
      self._cb_thread: Optional[threading.Thread] = None
      self._cb_ready = threading.Event()

   @property
   def cache(self) -> SubscriptionCache[Any]:
      """
Get the subscription cache, initializing it if necessary.

**Returns:**

  / *Type*: SubscriptionCache /

  The subscription cache instance.
      """
      if self._cache is None:
         self._cache = SubscriptionCache(maxlen=self._cache_default)
      return self._cache

   async def start(self, cache_size: Optional[int] = None):
      """
Start the subscriber by declaring a queue, binding it to the exchange, and consuming messages.

**Arguments:**

* ``cache_size``

  / *Condition*: optional / *Type*: Optional[int] /

  The maximum size of the subscription cache. If not provided, defaults to the instance's default cache size.

**Returns:**

  / *Type*: SubscriptionCache /

  The subscription cache instance.
      """
      self._queue = await self._channel.declare_queue(
         name="",
         exclusive=True,
         auto_delete=True
      )
      self._cache = SubscriptionCache(maxlen=cache_size or self._cache_default)
      await self._queue.bind(self._exchange, routing_key=self._routing_key)
      if self._callback_isolation == "threaded":
         self._start_callback_loop()
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

         # Stop isolated callback loop
         if self._callback_isolation == "threaded":
            self._stop_callback_loop()

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
            LOGGER.info(f"[AsyncSubscriber] Received message: {obj} with headers: {message.headers}")
            LOGGER.info(f"[AsyncSubscriber] Cache id: {id(self._cache)}. Cache: {self._cache}")
            if self._cache is not None:
               LOGGER.info(f"[AsyncSubscriber] Caching message: {obj}. Cache id: {id(self._cache)}")
               self._cache.append(obj)

            if not isinstance(obj, self._message_cls):
               raise TypeError(f"Expected {self._message_cls}, got {type(obj)}")

            if self._callback:
               # for cb in self._callback:
               #    if asyncio.iscoroutinefunction(cb):
               #       await cb(obj, dict(message.headers))
               #    else:
               #       cb(obj, message.headers)
               self._schedule_handlers(obj, dict(message.headers))

         except Exception as e:
            LOGGER.info(f"[AsyncSubscriber] Error handling message: {e}")

   def _schedule_handlers(self, message: BaseMessage, headers: dict) -> None:
      """
Schedule all handlers without awaiting them. Used when ack_after_handler=False.

**Arguments:**

* ``message``

  / *Condition*: required / *Type*: BaseMessage /

  The message to be processed by the handlers.

* ``headers``

  / *Condition*: required / *Type*: dict /

  Additional headers associated with the message.

**Returns:**

  / *Type*: None /

  Nothing. Handlers are scheduled for execution.
      """
      if not self._callback:
         return

      loop = asyncio.get_running_loop()

      for h in self._callback:
         if self._callback_isolation == "threaded":
            if inspect.iscoroutinefunction(h):
               # async handler on dedicated callback loop (safe if it calls send_sync)
               fut = asyncio.run_coroutine_threadsafe(h(message, headers), self._cb_loop)  # type: ignore[arg-type]
               # ensure exceptions are observed (avoid "exception was never retrieved")
               fut.add_done_callback(lambda f: f.exception())
            else:
               # sync handler on a worker thread (not blocking bus loop)
               loop.run_in_executor(None, h, message, headers)
         else:
            # direct mode: run on bus loop
            if inspect.iscoroutinefunction(h):
               loop.create_task(h(message, headers))
            else:
               loop.run_in_executor(None, h, message, headers)

   async def _invoke_handlers(self, message: BaseMessage, headers: dict) -> bool:
      """
Await all handlers (used when ack_after_handler=True).

**Arguments:**

* ``message``

  / *Condition*: required / *Type*: BaseMessage /

  The message to be processed by the handlers.

* ``headers``

  / *Condition*: required / *Type*: dict /

  Additional headers associated with the message.

**Returns:**

  / *Type*: bool /

  True if all handlers succeeded, False if any handler failed.
      """
      if not self._callback:
         return True

      async def _one(h):
         if self._callback_isolation == "threaded":
            if inspect.iscoroutinefunction(h):
               fut = asyncio.run_coroutine_threadsafe(h(message, headers), self._cb_loop)  # type: ignore[arg-type]
               # propagate any exception to this loop
               return await asyncio.wrap_future(fut)
            else:
               loop = asyncio.get_running_loop()
               return await loop.run_in_executor(None, h, message, headers)
         else:
            if inspect.iscoroutinefunction(h):
               return await h(message, headers)
            else:
               loop = asyncio.get_running_loop()
               return await loop.run_in_executor(None, h, message, headers)

      if self._handler_mode == "sequential":
         ok = True
         for h in self._callback:
            try:
               await _one(h)
            except Exception:
               LOGGER.exception("Handler failed (sequential): routing_key=%s", self.routing_key)
               ok = False
         return ok

      # parallel (default)
      tasks = [asyncio.create_task(_one(h)) for h in self._callback]
      results = await asyncio.gather(*tasks, return_exceptions=True)
      all_ok = True
      for r in results:
         if isinstance(r, Exception):
            all_ok = False
      if not all_ok:
         LOGGER.debug("One or more handlers failed (parallel) for routing_key=%s", self.routing_key)
      return all_ok

   # --------------------- callback loop management ---------------------

   def _start_callback_loop(self) -> None:
      """
Start a dedicated event loop in a separate thread for handling callbacks.
      """
      if self._cb_loop:
         return

      def _runner():
         loop = asyncio.new_event_loop()
         asyncio.set_event_loop(loop)
         self._cb_loop = loop
         self._cb_ready.set()
         try:
            loop.run_forever()
         finally:
            # best-effort drain
            try:
               pending = [t for t in asyncio.all_tasks(loop) if not t.done()]
               for t in pending:
                  t.cancel()
               if pending:
                  loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
               loop.run_until_complete(loop.shutdown_asyncgens())
            finally:
               loop.close()

      self._cb_thread = threading.Thread(target=_runner, name="CallbackLoop", daemon=True)
      self._cb_thread.start()
      self._cb_ready.wait(timeout=3.0)

   def _stop_callback_loop(self) -> None:
      """
Stop the dedicated event loop and thread used for handling callbacks.
      """
      if self._cb_loop and self._cb_loop.is_running():
         self._cb_loop.call_soon_threadsafe(self._cb_loop.stop)
      if self._cb_thread:
         self._cb_thread.join(timeout=3.0)
      self._cb_loop = None
      self._cb_thread = None
      self._cb_ready.clear()

   @property
   def routing_key(self):
       return self._routing_key

   @property
   def callback(self):
       return self._callback

