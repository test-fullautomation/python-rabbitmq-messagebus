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
import logging
from typing import Optional
import aio_pika
from serializer.base_serializer import Serializer
from serializer.pickle_serializer import PickleSerializer
# from event_bus_client import EventBusClient
from publisher import AsyncPublisher
from subscriber import AsyncSubscriber
from message.base_message import BaseMessage
from serializer.base_serializer import Serializer

logger = logging.getLogger(__name__)


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
      self._exchange: Optional[aio_pika.Exchange] = None
      self._exchange_name: str = ""
      self._exchange_type: str = ""
      self._reconnect_lock = asyncio.Lock()

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
      self._exchange_name = exchange_name
      self._exchange_type = exchange_type
      await self._establish_connection(host, port)
      # await self._declare_exchange()

   async def _establish_connection(self, host: str, port: int):
      self._connection = await aio_pika.connect_robust(
         host=host,
         port=port,
         loop=self._loop
      )

      self._channel = await self._connection.channel()
      self._channel.close_callbacks.add(self.reconnect)

      self._connection.close_callbacks.add(self.reconnect)
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
      return self._channel

   async def get_exchange(self) -> aio_pika.Exchange:
      return self._exchange

   async def close(self):
      """
      Gracefully close the connection and channel.
      """
      if self._channel and not self._channel.is_closed:
         await self._channel.close()
      if self._connection and not self._connection.is_closed:
         await self._connection.close()

   async def reconnect(self, host: str, port: int):
      """
Reconnect to RabbitMQ server and re-establish the connection and channel.

**Arguments:**

* ``host``

    / *Condition*: required / *Type*: str /

    The hostname or IP address of the RabbitMQ server.

* ``port``

    / *Condition*: required / *Type*: int /

    The port number on which the RabbitMQ server is listening.
      """
      async with self._reconnect_lock:
         print("[ConnectionManager] Reconnecting...")
         await self._establish_connection(host, port)
         # await self._declare_exchange()
         print("[ConnectionManager] Reconnected successfully.")
