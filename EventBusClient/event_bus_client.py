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
# File: event_bus_client.py
#
# Initially created by Nguyen Huynh Tri Cuong (MS/EMC51) / July 2025.
#
# Description:
#
#   EventBusClient: Client for interacting with the event bus system.
#
# History:
#
# 17.07.2025 / V 1.0.0 / Nguyen Huynh Tri Cuong
# - Initialize
#
# *******************************************************************************
import logging
import asyncio
from typing import Callable, Awaitable, Optional, Type
from publisher import AsyncPublisher
from subscriber import AsyncSubscriber
from exchange_handler.base import ExchangeHandler
from message.base_message import BaseMessage
from connection import ConnectionManager
from plugin_loader import PluginLoader  # Import PluginLoader
from serializer.base_serializer import Serializer
from qlogger import QLogger

logger = QLogger().get_logger("event_bus_client")
# logger = logging.getLogger(__name__)

class EventBusClient:
   """
EventBusClient: Client for interacting with the event bus system.
   """
   def __init__(
      self,
      exchange_handler: ExchangeHandler,
      serializer: Optional[Serializer] = None,
      loop: Optional[asyncio.AbstractEventLoop] = None
   ):
      """
EventBusClient: Initializes the event bus client with an exchange handler and serializer.

**Arguments:**

* ``exchange_handler``

    / *Condition*: required / *Type*: ExchangeHandler /

    The exchange handler used to manage message exchanges.

* ``serializer``

    / *Condition*: optional / *Type*: Serializer /

    The serializer used to serialize and deserialize messages. Defaults to PickleSerializer if not provided.

* ``loop``

    / *Condition*: optional / *Type*: asyncio.AbstractEventLoop /

    The event loop to use for asynchronous operations. If not provided, the current event loop will be used.
      """
      self.loop = loop or asyncio.get_event_loop()
      self.connection = ConnectionManager(loop=self.loop)
      self.exchange_handler = exchange_handler
      self.serializer = serializer
      self._connected = False

   @classmethod
   async def from_config(cls, config_path: str):
      """
Create an EventBusClient instance from a configuration file.

**Arguments:**

* ``config_path``

    / *Condition*: required / *Type*: str /

    Path to the configuration file in JSONP format. This file should contain the necessary configuration for the event bus client, including exchange handler and serializer settings.
      """
      plugin_loader = PluginLoader()
      config = plugin_loader.load_config(config_path)

      if not "logfile" in config:
         config.logfile = None

      # Dynamic load components
      handler_cls: Type[ExchangeHandler] = plugin_loader.get_exchange_handler(config.exchange_handler)
      serializer_cls: Type[Serializer] = plugin_loader.get_serializer(config.serializer)

      serializer = serializer_cls()
      handler = handler_cls(serializer=serializer)
      client = cls(exchange_handler=handler, serializer=serializer)
      await client.connect(
         host=config.get("host", "localhost"),
         port=config.get("port", 5672),
         exchange_name=config.get("exchange_name", "event_bus")
      )

      client._logger_handler = QLogger().set_handler(config)
      return client

   async def connect(self, host="localhost", port=5672, exchange_name="event_bus"):
      """
Connect to the event bus server and set up the exchange handler.

**Arguments:**

* ``host``

    / *Condition*: optional / *Type*: str /

    Hostname of the event bus server. Defaults to "localhost".

* ``port``

    / *Condition*: optional / *Type*: int /

    Port number of the event bus server. Defaults to 5672.

* ``exchange_name``

    / *Condition*: optional / *Type*: str /

    Name of the exchange to connect to. Defaults to "event_bus".
      """
      await self.connection.connect(host, port, exchange_name, self.exchange_handler.exchange_type)
      await self.exchange_handler.setup(self.connection)
      self._connected = True

   async def send(self, routing_key: str, message: BaseMessage, headers: dict = None, threadsafe=False):
      """
Send a message to the event bus with the specified routing key.

**Arguments:**

* ``routing_key``

    / *Condition*: required / *Type*: str /

    The routing key used to route the message to the appropriate subscribers.

* ``message``

    / *Condition*: required / *Type*: BaseMessage /

    The message to be sent. It should be an instance of BaseMessage or its subclasses.

* ``headers``

    / *Condition*: optional / *Type*: dict /

    Additional headers to include with the message. This can be used for metadata or routing information.

* ``threadsafe``

    / *Condition*: optional / *Type*: bool /

    If True, the message will be sent in a threadsafe manner. Defaults to False.
      """
      if not self._connected:
         raise RuntimeError("EventBusClient is not connected")
      await self.exchange_handler.publish(message, routing_key, headers, threadsafe=threadsafe)

   async def on(self, routing_key: str, message_cls: Type[BaseMessage], callback):
      if not self._connected:
         raise RuntimeError("EventBusClient is not connected")
      await self.exchange_handler.subscribe(routing_key, message_cls, callback)

   async def close(self):
      await self.exchange_handler.teardown()
      await self.connection.close()
      self._connected = False


async def main():
   # Example usage
   client = await EventBusClient.from_config("config/config.jsonp")
   await client.connect()
   await client.send("test.routing.key", BaseMessage())
   await client.on("test.routing.key", BaseMessage, lambda msg: print(msg))
   await client.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("EventBusClient is ready to use.")
    asyncio.run(main())
