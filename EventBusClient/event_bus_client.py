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
from __future__ import annotations
import logging
import asyncio
from typing import Callable, Awaitable, Optional, Type
from .exchange_handler.base import ExchangeHandler
from .message.base_message import BaseMessage
from .message.basic_message import BasicMessage
from .connection import ConnectionManager
from .plugin_loader import PluginLoader
from .serializer.base_serializer import Serializer
from .qlogger import QLogger
from .startup_policy import StartupPolicy, NoWait
from .rendezvous import Rendezvous

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
      loop: Optional[asyncio.AbstractEventLoop] = None,
      zone_id: Optional[str] = None,
      alias: Optional[str] = None,
      startup_policy: Optional[StartupPolicy] = None,
      prefetch_count: int = 10,
      auto_reconnect: bool = True
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
      self._startup_policy = startup_policy or NoWait()
      self.rendezvous = Rendezvous(self)

      self.loop = loop or asyncio.get_event_loop()
      self.connection = ConnectionManager(loop=self.loop, auto_reconnect=auto_reconnect)
      self.exchange_handler = exchange_handler
      self.prefetch_count = prefetch_count
      self.serializer = serializer
      self.zone_id = zone_id
      self.alias = alias
      self.system_up = False
      self._connected = False

   @classmethod
   async def from_config(cls, config_path: str, startup_policy: StartupPolicy | None = None) -> EventBusClient:
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
      auto_reconnect = config.get("auto_reconnect", True)
      client = cls(exchange_handler=handler, serializer=serializer, startup_policy=startup_policy, auto_reconnect=auto_reconnect)
      await client.connect(
         host=config.get("host", "localhost"),
         port=config.get("port", 5672),
         prefetch_count=config.get("prefetch_count", 10)
      )

      client._logger_handler = QLogger().set_handler(config)
      return client

   async def connect(self, host="localhost", port=5672, prefetch_count: int = 10):
      """
Connect to the event bus server and set up the exchange handler.

**Arguments:**

* ``host``

  / *Condition*: optional / *Type*: str / *Default*: "localhost" /

  Hostname of the event bus server. Defaults to "localhost".

* ``port``

  / *Condition*: optional / *Type*: int / *Default*: 5672 /

  Port number of the event bus server. Defaults to 5672.

* ``prefetch_count``

    / *Condition*: optional / *Type*: int / *Default*: 10 /

    The number of messages to prefetch from the server. This controls how many messages can be sent to the client before they are acknowledged. Defaults to 10.
      """
      await self.connection.connect(host, port, prefetch_count)
      await self.exchange_handler.setup(self.connection)
      self._connected = True
      await self._startup_policy.wait_until_ready(self)

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

   async def off(self, routing_key: str, callback: Optional[Callable[[BaseMessage], Awaitable[None]]] = None):
      """
Unsubscribe from messages with the specified routing key.

**Arguments:**

* ``routing_key``

  / *Condition*: required / *Type*: str /

  The routing key to unsubscribe from.

* ``callback``

  / *Condition*: optional / *Type*: Callable[[BaseMessage], Awaitable[None]] / *Default*: None /

  The callback function to remove from the subscriber list. If not provided, all callbacks for the routing key will be unsubscribed.
      """
      if not self._connected:
         raise RuntimeError("EventBusClient is not connected")
      await self.exchange_handler.unsubscribe(routing_key, callback)

   async def on(self, routing_key: str, message_cls: Type[BaseMessage], callback: Optional[Callable[[BaseMessage], Awaitable[None]]] = None, cache_size: Optional[int] = None):
      """
Subscribe to messages with the specified routing key and message class.

**Arguments:**

* ``routing_key``

  / *Condition*: required / *Type*: str /

  The routing key to subscribe to. Messages with this routing key will be routed to the callback.

* ``message_cls``

  / *Condition*: required / *Type*: Type[BaseMessage] /

  The class of the message to subscribe to. The callback will receive messages of this type.

* ``callback``

  / *Condition*: required / *Type*: Callable[[BaseMessage], Awaitable[None]] /

  The callback function to be called when a message is received. It should accept a single argument of type BaseMessage or its subclasses and return an awaitable (e.g., a coroutine).
      """
      if not self._connected:
         raise RuntimeError("EventBusClient is not connected")
      return await self.exchange_handler.subscribe(routing_key, message_cls, callback, cache_size)


   async def wait_until_ready(self, requirements: dict[str, int], timeout: float = 5.0) -> bool:
      """
Convenience wrapper over rendezvous.wait_for.

**Arguments:**
* ``requirements``

  / *Condition*: required / *Type*: dict[str, int] /

  A dictionary where keys are role names and values are the number of instances required for each role.

* ``timeout``

  / *Condition*: optional / *Type*: float /

  The maximum time to wait for the rendezvous to be satisfied. Defaults to 5.0 seconds.
      """
      return await self.rendezvous.wait_for(requirements, timeout=timeout)

   async def announce_ready(self, roles: list[str]) -> None:
      """
Convenience wrapper over rendezvous.announce_ready.

**Arguments:**

* ``roles``

  / *Condition*: required / *Type*: list[str] /

  A list of role names that this instance is ready for. This is used to signal readiness in the rendezvous system.
      """
      await self.rendezvous.announce_ready(roles)

   async def close(self):
      """
Close the connection to the event bus and clean up resources.
      """
      await self.exchange_handler.teardown()
      await self.connection.close()
      self._connected = False

   def build_routing_key(self, *path: str) -> str:
      """
Build a routing key from the given path components.

**Arguments:**

* ``path``

  / *Condition*: required / *Type*: str /

  The components of the routing key. Each component will be joined with a dot (.) to form the final routing key.

**Returns:**

* ``str``

  / *Type*: str /

  The constructed routing key as a string.
      """
      parts = [p for p in path if p]
      if self.zone_id:
         parts.append(self.zone_id)
      if self.alias:
         parts.append(self.alias)
      return ".".join(parts)


async def main():
   # Example usage
   client = await EventBusClient.from_config("config/config.jsonp")
   await client.connect()
   await client.send("test.routing.key", BasicMessage("Test"))
   await client.on("test.routing.key", BasicMessage, lambda msg: print(msg))
   await client.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("EventBusClient is ready to use.")
    asyncio.run(main())
