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

import aio_pika

from EventBusClient.message.base_message import BaseMessage
from EventBusClient.publisher import AsyncPublisher
from EventBusClient.subscriber import AsyncSubscriber
from typing import Type, Optional
# from EventBusClient.qlogger import QLogger
from EventBusClient import LOGGER

# logger = logging.getLogger(__name__)
# logger = QLogger().get_logger("event_bus_client")

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

      self._unroutable_policy = "drop"
      self._alternate_exchange = None
      self._on_unroutable = "log"
      self._on_unroutable_cb = None
      self._unroutable_sink = None
      self._return_callback_set = False
      self.declare_args = {}

   def configure_unroutable(self, *,
                            policy: str,
                            alternate_exchange: Optional[str],
                            on_unroutable: str,
                            unroutable_sink: Optional[list[str]],
                            on_unroutable_callback):
      """
Configure the unroutable message handling policy.

**Arguments:**

* ``policy``

  / *Condition*: required / *Type*: str /

  The unroutable message handling policy. Options are "drop", "log", "return", "alternate-exchange".

* ``alternate_exchange``

  / *Condition*: optional / *Type*: str /

  The name of the alternate exchange to use if the policy is "alternate-exchange".

* ``on_unroutable``

  / *Condition*: required / *Type*: str /

  The action to take for unroutable messages. Options are "log", "cache", "callback", "raise".

* ``unroutable_sink``

  / *Condition*: optional / *Type*: list /

  The sink (list) to store unroutable messages if the action is "cache".

* ``on_unroutable_callback``

  / *Condition*: optional / *Type*: Callable /

  The callback function to invoke for unroutable messages if the action is "callback".
      """
      self._unroutable_policy = policy
      self._alternate_exchange = alternate_exchange
      self._on_unroutable = on_unroutable
      self._unroutable_sink = unroutable_sink
      self._on_unroutable_cb = on_unroutable_callback

   def _handle_unroutable(self, info: dict) -> None:
      """
Handle unroutable messages based on the configured action.

**Arguments:**

* ``info``

  / *Condition*: required / *Type*: dict /

  Information about the unroutable message.
      """
      mode = self._on_unroutable
      if mode == "log":
         LOGGER.warning("Unroutable message: %s", info)
      elif mode == "cache" and self._unroutable_sink is not None:
         try:
            self._unroutable_sink.append(info)  # <-- use sink
         except Exception:
            LOGGER.exception("Failed to cache unroutable message")
      elif mode == "callback" and self._on_unroutable_cb:
         try:
            self._on_unroutable_cb(info)
         except Exception:
            LOGGER.exception("on_unroutable_callback raised")
      elif mode == "raise":
         raise RuntimeError(f"Unroutable publish: {info!r}")
      else:
         LOGGER.warning("Unknown on_unroutable=%r; logging: %s", mode, info)

   def _on_basic_return(self, channel: aio_pika.robust_channel.RobustChannel, message: aio_pika.IncomingMessage) -> None:
      """
Handle basic.return AMQP messages for unroutable messages.

**Arguments:**

* ``message``

  / *Condition*: required / *Type*: aio_pika.IncomingMessage /

  The incoming message that was returned as unroutable.
      """
      info = {
         "routing_key": getattr(message, "routing_key", None),
         "exchange": getattr(message, "exchange", None),
         "headers": dict(getattr(message, "headers", {}) or {}),
         "reply_code": getattr(message, "reply_code", None),
         "reply_text": getattr(message, "reply_text", None),
         "body": getattr(message, "body", b""),
      }
      try:
         self._handle_unroutable(info)
      except Exception as ex:
         LOGGER.exception("Unroutable handler raised an exception. Details: %s", ex)
         if self._on_unroutable == "raise":
            raise


   def _install_return_handler(self) -> None:
      """
Install the AMQP return handler on the channel for handling unroutable messages.
      """
      if not self._channel or self._return_callback_set:
         return

      cb = self._on_basic_return

      # aio-pika versions differ; try a few names:
      for attr in ("return_callbacks", "add_on_return_callback", "add_return_callback", "set_return_callback", "set_on_return_callback"):
         if hasattr(self._channel, attr):
            try:
               if attr == "return_callbacks":
                    getattr(self._channel, attr).add(cb)  # type: ignore[misc]
                    self._return_callback_set = True
                    LOGGER.info("Registered AMQP return callback via %s.add", attr)
                    return
               else:
                  getattr(self._channel, attr)(cb)  # type: ignore[misc]
                  self._return_callback_set = True
                  LOGGER.info("Registered AMQP return callback via %s", attr)
                  return
            except Exception as ex:
                  pass

      LOGGER.warning("Could not register AMQP return callback on channel; 'return' policy will only set mandatory=True")

   def reset_loop(self, loop: asyncio.AbstractEventLoop = None):
      """
Reset the event loop used by the exchange handler.

**Arguments:**

* ``loop``

  / *Condition*: optional / *Type*: asyncio.AbstractEventLoop /

  The new event loop to use. If not provided, the current event loop will be used.
      """
      self._loop = loop or asyncio.get_event_loop()

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

   # noinspection PyMethodMayBeStatic
   def with_alternate_exchange(func):
      """
Decorator to set up and finalize alternate exchange configuration around the decorated method.

**Arguments:**

* ``func``

  / *Condition*: required / *Type*: Callable /

  The method to be decorated.
      """
      async def wrapper(self, *args, **kwargs):
         await self.setup_alternate_exchange()
         result = await func(self, *args, **kwargs)
         await self.finalize_setup()
         return result
      return wrapper

   async def setup_alternate_exchange(self):
      """
Set up the alternate exchange configuration based on the unroutable policy.
      """
      # Alternate Exchange policy
      if self._unroutable_policy == "alternate-exchange":
         ae_name = self._alternate_exchange or f"{self.exchange_name}.ae"
         self.declare_args["alternate-exchange"] = ae_name

   async def finalize_setup(self):
      """
Finalize the setup of the exchange handler by configuring the alternate exchange and return handler.
      """
      # If AE policy, declare AE (fanout) + a durable unroutable queue and bind it
      if self._unroutable_policy == "alternate-exchange":
         ae_name = self._alternate_exchange or f"{self.exchange_name}.ae"
         ae = await self._channel.declare_exchange(ae_name, aio_pika.ExchangeType.FANOUT, durable=True)
         dq_name = f"{self.exchange_name}.unroutable"
         dq = await self._channel.declare_queue(dq_name, durable=True)
         await dq.bind(ae, routing_key="")  # fanout ignores routing_key

      # If RETURN policy, register channel return handler (feature-detected)
      if self._unroutable_policy == "return":
         self._install_return_handler()

   async def teardown(self):
      """
Tear down the exchange handler by closing the channel and cleaning up resources.
      """
      for subscriber in self._subscribers:
         await subscriber.stop()
         LOGGER.info(f"Unsubscribed {len(self._subscribers)} subscribers.")
      self._subscribers.clear()

      # if self._exchange:
      #    await self._exchange.delete()
      #    self._exchange = None

      if self._connection:
         self._connection.unregister_exchange_handler(self)

   @abstractmethod
   async def publish(self, message: BaseMessage, routing_key: str, headers: dict = None, threadsafe: bool = False, mandatory: bool = False): ...

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
            LOGGER.info(f"Unsubscribed callback from routing key: {routing_key}")
            break
      else:
         LOGGER.warning(f"No subscriber found for routing key: {routing_key} with the given callback.")

   async def handle_channel_close(self, exc: Exception = None):
      """
Handle channel closure by attempting to re-create the channel.

**Arguments:**

* ``exc``

  / *Condition*: optional / *Type*: Exception /

  The exception that caused the channel to close, if any. If not provided, it defaults to None.
      """
      LOGGER.info(f"[ConnectionManager] Channel closed. Exception: {exc} \nAttempting to re-create channel...")
      if self._connection and not self._connection.is_closed:
         self._channel = await self.setup(self._connection)
         self._channel.close_callbacks.add(
            lambda expt: asyncio.create_task(self.handle_channel_close(expt)))
         await self._channel.set_qos(prefetch_count=10)
         LOGGER.info("[ConnectionManager] Channel re-created successfully.")