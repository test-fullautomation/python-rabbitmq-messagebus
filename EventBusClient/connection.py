#  Copyright 2020-2023 Robert Bosch GmbH
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
# File: connection.py
#
# Initially created by Nguyen Huynh Tri Cuong (MS/EMC51) / July 2025.
#
# Description:
#
#   ConnectionManager: Manages RabbitMQ connections, channels, and exchanges.
#
# History:
#
# 17.07.2025 / V 1.0.0 / Nguyen Huynh Tri Cuong
# - Initialize
#
# *******************************************************************************
import asyncio
# import logging
from typing import Optional
import aio_pika
from qlogger import QLogger

# logger = logging.getLogger(__name__)
logger = QLogger().get_logger("event_bus_client")

class ConnectionManager:
   """
ConnectionManager: Manages RabbitMQ connections, channels, and exchanges.
   """
   def __init__(self, loop: Optional[asyncio.AbstractEventLoop] = None):
      """
ConnectionManager: Initializes the connection manager with an event loop.

**Arguments:**

* ``loop``

   / *Condition*: optional / *Type*: asyncio.AbstractEventLoop /

   The event loop to use for asynchronous operations. If not provided, the current event loop is used.
      """
      self._loop = loop or asyncio.get_event_loop()
      self._connection: Optional[aio_pika.RobustConnection] = None
      self._channel: Optional[aio_pika.Channel] = None
      self._reconnect_lock = asyncio.Lock()
      self._exchange_handlers = []

   async def connect(self, host: str, port: int, exchange_name: str, exchange_type: str):
      """
Establish a robust connection to RabbitMQ and declare the exchange.

**Arguments:**

* ``host``

   / *Condition*: required / *Type*: str /

   The hostname or IP address of the RabbitMQ server.

* ``port``

   / *Condition*: required / *Type*: int /

   The port number on which the RabbitMQ server is listening.

* ``exchange_name``

   / *Condition*: required / *Type*: str /

   The name of the exchange to declare or use.

* ``exchange_type``

   / *Condition*: required / *Type*: str /

   The type of the exchange (e.g., "direct", "topic", "fanout", "x-rtopic").
      """
      # self._exchange_name = exchange_name
      # self._exchange_type = exchange_type
      await self._establish_connection(host, port)
      # await self._declare_exchange()

   def register_exchange_handler(self, handler):
      """
Register an exchange handler to handle messages from the exchange.

**Arguments:**

* ``handler``

   / *Condition*: required / *Type*: ExchangeHandler /

   The exchange handler to register. It should be an instance of ExchangeHandler or its subclasses.
      """
      self._exchange_handlers.append(handler)

   def unregister_exchange_handler(self, handler):
      """
Unregister an exchange handler.

**Arguments:**

* ``handler``

   / *Condition*: required / *Type*: ExchangeHandler /

   The exchange handler to unregister. It should be an instance of ExchangeHandler or its subclasses.
      """
      if handler in self._exchange_handlers:
         self._exchange_handlers.remove(handler)

   async def _establish_connection(self, host: str, port: int):
      """
Establish a robust connection to RabbitMQ and create a channel.

**Arguments:**

* ``host``

   / *Condition*: required / *Type*: str /

   The hostname or IP address of the RabbitMQ server.

* ``port``

   / *Condition*: required / *Type*: int /

   The port number on which the RabbitMQ server is listening.
      """
      self._connection = await aio_pika.connect_robust(
         host=host,
         port=port,
         loop=self._loop
      )

      self._channel = await self._connection.channel()
      # self._channel.close_callbacks.add(
      #    lambda exc: asyncio.create_task(self.reconnect(host, port, exc)))
      for handler in self._exchange_handlers:
         self._channel.close_callbacks.add(
            lambda exc, h=handler: asyncio.create_task(h.handle_channel_close(self, exc)))

      self._connection.close_callbacks.add(
         lambda exc: asyncio.create_task(self.reconnect(host, port, exc)))
      # Optional: QoS tuning
      await self._channel.set_qos(prefetch_count=10)

   # async def _declare_exchange(self):
   #    """
   #    Declare the exchange to ensure it exists.
   #    """
   #    self._exchange = await self._channel.declare_exchange(
   #       name=self._exchange_name,
   #       type=self._exchange_type,
   #       durable=True
   #    )

   async def get_channel(self) -> aio_pika.Channel:
      """
Get the current channel for publishing messages.

**Returns:**

   / *Type*: aio_pika.Channel | None /

   Channel instance or None if not available.
      """
      return self._channel

   # async def get_exchange(self) -> aio_pika.Exchange:
   #    return self._exchange

   async def close(self):
      """
Gracefully close the connection and channel.
      """
      if self._channel and not self._channel.is_closed:
         await self._channel.close()
      if self._connection and not self._connection.is_closed:
         await self._connection.close()

   async def reconnect(self, host: str, port: int, exc: Exception = None):
      """
Reconnect to RabbitMQ in case of connection loss or error.

**Arguments:**

* ``host``

   / *Condition*: required / *Type*: str /

   The hostname or IP address of the RabbitMQ server.

* ``port``

   / *Condition*: required / *Type*: int /

   The port number on which the RabbitMQ server is listening.

* ``exc``

   / *Condition*: optional / *Type*: Exception /

   The exception that caused the reconnection attempt, if any. If not provided, it defaults to None.
      """
      async with self._reconnect_lock:
         if exc:
            if isinstance(exc, aio_pika.exceptions.AMQPConnectionError):
               logger.error(f"[ConnectionManager] AMQPConnectionError: {exc}")
            elif isinstance(exc, asyncio.TimeoutError):
               logger.error(f"[ConnectionManager] TimeoutError: {exc}")
            elif isinstance(exc, ConnectionRefusedError):
               logger.error(f"[ConnectionManager] ConnectionRefusedError: {exc}")
            else:
               logger.error(f"[ConnectionManager] Unknown exception: {exc}")
         else:
            logger.info("[ConnectionManager] Connection closed, reconnecting...")
         print("[ConnectionManager] Reconnecting...")
         await self._establish_connection(host, port)
         for handler in self._exchange_handlers:
            if hasattr(handler, "setup"):
               await handler.setup(self)
         print("[ConnectionManager] Reconnected successfully.")
