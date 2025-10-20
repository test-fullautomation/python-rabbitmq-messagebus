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
import threading
from concurrent.futures import TimeoutError as _FutTimeout, ThreadPoolExecutor
from typing import Callable, Awaitable, Optional, Type, Union
from JsonPreprocessor import CJsonPreprocessor
from EventBusClient.subscription_cache import SubscriptionCache
from .exchange_handler.base import ExchangeHandler
from .message.base_message import BaseMessage
from .message.basic_message import BasicMessage
from .connection import ConnectionManager
from .plugin_loader import PluginLoader, CONFIG_SCHEMA, ConfigValidator
from .serializer.base_serializer import Serializer
from .qlogger import QLogger
from .startup_policy import StartupPolicy, NoWait, PolicyChain, build_policy_from_config
from .rendezvous import Rendezvous
from EventBusClient import LOGGER, LOGGER_NAME
from .wait_mode import WaitMode
from EventBusClient.version import VERSION, VERSION_DATE

# logger = QLogger().get_logger("event_bus_client")
# logger = logging.getLogger(__name__)

def get_running_loop_or_none() -> Optional[asyncio.AbstractEventLoop]:
   try:
      return asyncio.get_running_loop()
   except RuntimeError:
      # "no running event loop" in this thread
      return None


def is_on_loop(loop: asyncio.AbstractEventLoop) -> bool:
   try:
      return asyncio.get_running_loop() is loop
   except RuntimeError:
      return False

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
      auto_reconnect: bool = True,
      host: str = "localhost",
      port: int = 5672,
      logger_config: dict = None,
      startup_policies: list[StartupPolicy] | None = None,
      **kwargs
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
      if logger_config:
         if "logger_name" not in logger_config or not logger_config.logger_name:
            logger_config.logger_name = "event_bus_client"

         EventBusClient.LOGGER_NAME = logger_config.logger_name
         if "logfile" not in logger_config:
            logger_config.logfile = None
         self._logger_handler = QLogger().set_handler(logger_config)

      if startup_policies:
         self._startup_policy = PolicyChain(startup_policies)
      else:
         self._startup_policy = startup_policy
      # self._startup_policy = startup_policy or NoWait()
      self.rendezvous = Rendezvous(self)

      self.loop = loop # or asyncio.get_event_loop()
      self.connection = ConnectionManager(loop=None, auto_reconnect=auto_reconnect)
      self.exchange_handler = exchange_handler
      self.prefetch_count = prefetch_count
      self.serializer = serializer
      self.zone_id = zone_id
      self.alias = alias
      self.system_up = False
      self.host = host
      self.port = port
      self._connected = False

      # General-cache policy
      self.general_cache_policy: str = kwargs.get("general_cache_policy",
                                                           "off")  # "off" | "on_connect" | "on_demand"
      self.general_routing_keys = kwargs.get("general_routing_keys",
                                                      ["general"])
      self.general_message_cls = kwargs.get("general_message_cls", BaseMessage)
      self.general_cache = None
      self._wait_exec = None  # lazy ThreadPoolExecutor for async=True legacy waits
      
   def getVersion(self) -> str:
      """
Returns the version of EventBusClient as string.
      """
      return VERSION
    
   def getVersionDate(self) -> str:
      """
Returns the version date of EventBusClient as string.
      """
      return VERSION_DATE

   async def _ensure_general_listener(self) -> None:
      """
Ensure the general listener is running (idempotent).
      """
      if self.general_cache is not None:
         return

      self.general_cache = await self.exchange_handler.subscribe(routing_key=self.general_routing_keys , message_cls=self.general_message_cls, callback=None)

   async def enable_general_cache(self, *, routing_keys, message_cls) -> None:
      """
Enable the general cache with the specified routing keys and message class.

**Arguments:**

* ``routing_keys``

  / *Condition*: required / *Type*: Union[str, list] /

  The routing keys to subscribe to for the general cache. Can be a single string or a list of strings.

* ``message_cls``

  / *Condition*: required / *Type*: Type[BaseMessage] /

  The class of messages to subscribe to for the general cache. Must be a subclass of BaseMessage.
      """
      self.general_cache_policy = "on_connect"
      self.general_routing_keys = routing_keys # if isinstance(routing_keys, (list, tuple)) else [routing_keys]
      self.general_message_cls = message_cls
      # idempotent; will no-op if already running
      await self._ensure_general_listener()

   def _wait_exec(self) -> ThreadPoolExecutor:
      """
      Returns the ThreadPoolExecutor instance used for executing wait operations.
      If the executor does not exist, it is created with a maximum of 4 worker threads.

      Returns:
          ThreadPoolExecutor: The thread pool executor for wait operations.
      """
      if self.__dict__.get("_wait_exec") is None:
         self._wait_exec = ThreadPoolExecutor(max_workers=4)
      return self._wait_exec

   def wait_on_general_topic_for_one(
           self, msg, *, timeout: float = 30.0, interval: float = 0.1, asynchronous: bool = False
   ):
      """
Wait for a specific message on the general topic.

**Arguments:**

* ``msg``

  / *Condition*: required / *Type*: Any /

  The message to wait for. This can be any object that can be compared for equality.

* ``timeout``

  / *Condition*: optional / *Type*: float / *Default*: 30.0 /

  The maximum time to wait for the message, in seconds. Defaults to 30.0 seconds.

* ``interval``

  / *Condition*: optional / *Type*: float / *Default*: 0.1 /

  **Note:** This parameter is accepted for compatibility with older interfaces but is not used in the current implementation.

* ``asynchronous``

  / *Condition*: optional / *Type*: bool / *Default*: False /

  If True, the wait will be performed asynchronously using a ThreadPoolExecutor. Defaults to False.

**Returns:**

  / *Type*: bool /

  True if the message was received within the timeout period, False otherwise.
      """
      if not self.general_cache:
         # lazy start if policy allows (captures from now on)
         if self.general_cache_policy in ("on_demand", "off"):
            self._submit(self._ensure_general_listener())
         else:
            raise RuntimeError("General cache not available")
      cache: SubscriptionCache = self.general_cache
      if not asynchronous:
         return cache.wait_for_one(msg, timeout=timeout)
      return self._wait_exec().submit(cache.wait_for_one, msg, timeout)

   def wait_on_general_topic_for_many(
           self, msgs, *, mode: int = WaitMode.ALL_IN_GIVEN_ORDER.value, timeout: float = 30.0, interval: float = 0.1,
           asynchronous: bool = False
   ):
      """
Wait for multiple specific messages on the general topic.

**Arguments:**

* ``msgs``

  / *Condition*: required / *Type*: List[Any] /

  The list of messages to wait for. Each message can be any object that can be compared for equality.

* ``mode``

  / *Condition*: optional / *Type*: int / *Default*: WaitMode.ALL_IN_GIVEN_ORDER.value /

  The mode for waiting:

  - WaitMode.ALL_IN_GIVEN_ORDER: Wait for all messages in the order they are provided.

  - WaitMode.ALL_IN_RANDOM_ORDER: Wait for all messages in any order.

  - WaitMode.ANY: Wait for any one of the messages.

  Defaults to WaitMode.ALL_IN_GIVEN_ORDER.value.

* ``timeout``

  / *Condition*: optional / *Type*: float / *Default*: 30.0 /

  The maximum time to wait for the messages, in seconds. Defaults to 30.0 seconds.

* ``interval``

  / *Condition*: optional / *Type*: float / *Default*: 0.1 /

  **Note:** This parameter is accepted for compatibility with older interfaces but is not used in the current implementation.

* ``asynchronous``

  / *Condition*: optional / *Type*: bool / *Default*: False /

  If True, the wait will be performed asynchronously using a ThreadPoolExecutor. Defaults to False.

**Returns:**

  / *Type*: List[int] /

  A list of indices of the messages that were received, based on the specified mode.
      """
      if not self.general_cache:
         if self.general_cache_policy in ("on_demand", "off"):
            self._submit(self._ensure_general_listener())
         else:
            raise RuntimeError("General cache not available")
      cache: SubscriptionCache = self.general_cache
      if not asynchronous:
         return cache.wait_for_many(msgs, mode=WaitMode(mode), timeout=timeout)
      return self._wait_exec().submit(cache.wait_for_many, msgs, WaitMode(mode), timeout)

   def wait_on_cache_for_one(
           self, cache: SubscriptionCache, msg, *, timeout: float = 30.0, interval: float = 0.1,
           asynchronous: bool = False
   ):
      """
Wait for a specific message in the given subscription cache.

**Arguments:**

* ``cache``

  / *Condition*: required / *Type*: SubscriptionCache /

  The subscription cache to wait on. This should be an instance of SubscriptionCache.

* ``msg``

  / *Condition*: required / *Type*: Any /

  The message to wait for. This can be any object that can be compared for equality.

* ``timeout``

  / *Condition*: optional / *Type*: float / *Default*: 30.0 /

  The maximum time to wait for the message, in seconds. Defaults to 30.0 seconds.

* ``interval``

  / *Condition*: optional / *Type*: float / *Default*: 0.1 /

  **Note:** This parameter is accepted for compatibility with older interfaces but is not used in the current implementation.

* ``asynchronous``

  / *Condition*: optional / *Type*: bool / *Default*: False /

  If True, the wait will be performed asynchronously using a ThreadPoolExecutor. Defaults to False.

**Returns:**

  / *Type*: bool /

  True if the message was received within the timeout period, False otherwise.
      """
      if not asynchronous:
         return cache.wait_for_one(msg, timeout=timeout)
      return self._wait_exec().submit(cache.wait_for_one, msg, timeout)

   def wait_on_cache_for_many(
           self, cache: SubscriptionCache, msgs, *, mode: int = WaitMode.ALL_IN_GIVEN_ORDER.value,
           timeout: float = 30.0, interval: float = 0.1, asynchronous: bool = False
   ):
      """
Wait for multiple specific messages in the given subscription cache.

**Arguments:**

* ``cache``

  / *Condition*: required / *Type*: SubscriptionCache /

  The subscription cache to wait on. This should be an instance of SubscriptionCache.

* ``msgs``

  / *Condition*: required / *Type*: List[Any] /

  The list of messages to wait for. Each message can be any object that can be compared for equality.

* ``mode``

  / *Condition*: optional / *Type*: int / *Default*: WaitMode.ALL_IN_GIVEN_ORDER.value /

  The mode for waiting:

  - WaitMode.ALL_IN_GIVEN_ORDER: Wait for all messages in the order they are provided.

  - WaitMode.ALL_IN_RANDOM_ORDER: Wait for all messages in any order.

  - WaitMode.ANY: Wait for any one of the messages.

  Defaults to WaitMode.ALL_IN_GIVEN_ORDER.value.

* ``timeout``

  / *Condition*: optional / *Type*: float / *Default*: 30.0 /

  The maximum time to wait for the messages, in seconds. Defaults to 30.0 seconds.

* ``interval``

  / *Condition*: optional / *Type*: float / *Default*: 0.1 /

  **Note:** This parameter is accepted for compatibility with older interfaces but is not used in the current implementation.

* ``asynchronous``

  / *Condition*: optional / *Type*: bool / *Default*: False /

  If True, the wait will be performed asynchronously using a ThreadPoolExecutor. Defaults to False.

**Returns:**

  / *Type*: List[int] /

  A list of indices of the messages that were received, based on the specified mode.
      """
      if not asynchronous:
         return cache.wait_for_many(msgs, mode=WaitMode(mode), timeout=timeout)
      return self._wait_exec().submit(cache.wait_for_many, msgs, WaitMode(mode), timeout)

   @staticmethod
   def constructor_params_from_config(config_path: str,
                                      startup_policy: Optional[StartupPolicy] = None,
                                      zone_id: Optional[str] = None,
                                      alias: Optional[str] = None) -> tuple:
      """
Returns a tuple of parameters for the EventBusClient constructor, loaded from config and provided arguments.

**Arguments:**

* ``config_path``

  / *Condition*: required / *Type*: str /

  Path to the configuration file in JSONP format. This file should contain the necessary configuration for the event bus client, including exchange handler and serializer settings.

* ``startup_policy``

  / *Condition*: optional / *Type*: StartupPolicy / *Default*: None /

  The startup policy to use for the client. If not provided, no startup policy will be used.

* ``zone_id``

  / *Condition*: optional / *Type*: str / *Default*: None /

  The zone ID for the client. If not provided, no zone ID will be used.

* ``alias``

  / *Condition*: optional / *Type*: str / *Default*: None /

  The alias for the client. If not provided, no alias will be used.

**Returns:**

  / *Type*: tuple /

  A tuple containing the following elements in order:

    - exchange_handler: An instance of ExchangeHandler loaded from the configuration.

    - serializer: An instance of Serializer loaded from the configuration.

    - loop: None (the event loop will be set later).

    - zone_id: The provided zone_id argument.

    - alias: The provided alias argument.

    - startup_policy: The provided startup_policy argument.

    - prefetch_count: The prefetch count loaded from the configuration (default is 10 if not specified).

    - auto_reconnect: The auto_reconnect setting loaded from the configuration (default is True if not specified).
      """
      config = PluginLoader.load_config(config_path)
      plugin_loader = PluginLoader()
      handler_cls: Type[ExchangeHandler] = plugin_loader.get_exchange_handler(config.exchange_handler)
      serializer_cls: Type[Serializer] = plugin_loader.get_serializer(config.serializer)
      serializer = serializer_cls()
      handler = handler_cls(serializer=serializer)
      auto_reconnect = config.get("auto_reconnect", True)
      return (
         handler,
         serializer,
         None,  # loop
         zone_id,
         alias,
         startup_policy,
         config.get("qos_prefetch", 10),
         auto_reconnect,
         config.get("host", "localhost"),
         config.get("port", 5672),
         config
      )

   @classmethod
   async def from_config(cls,
                         config_path: Optional[str] = None,
                         startup_policy: Optional[StartupPolicy] = None,
                         zone_id: Optional[str] = None,
                         alias: Optional[str] = None,
                         start_connection: bool = True,
                         config_source: Optional[Union[str, dict]] = None) -> EventBusClient:
      """
Create an EventBusClient instance from a configuration file.

**Arguments:**

* ``config_path``

  / *Condition*: required / *Type*: str /

  Path to the configuration file in JSONP format. This file should contain the necessary configuration for the event bus client, including exchange handler and serializer settings.

* ``config_source``

  / *Condition*: required / *Type*: Union[str, dict] /

  Configuration source as a JSON string or dictionary. This can be used instead of config_path to provide configuration directly.

* ``startup_policy``

  / *Condition*: optional / *Type*: StartupPolicy / *Default*: None /

  The startup policy to use for the client. If not provided, no startup policy will be used.

* ``zone_id``

  / *Condition*: optional / *Type*: str / *Default*: None /

  The zone ID for the client. If not provided, no zone ID will be used.

* ``alias``

  / *Condition*: optional / *Type*: str / *Default*: None /

  The alias for the client. If not provided, no alias will be used.

* ``start_connection``

  / *Condition*: optional / *Type*: bool / *Default*: True /

  If True, the client will automatically connect to the event bus server after creation. Defaults to True.

**Returns:**

  / *Type*: EventBusClient /

  An instance of EventBusClient configured according to the provided configuration file or source.
      """
      default_values = {
         "plugins_path": "./plugins",
         "host": "localhost",
         "port": 5672,
         "auto_reconnect": True,
         "qos_prefetch": 10,
         "logfile": None,
         "loglevel": "INFO",
         "logger_name": "event_bus_client"
      }
      # LOGGER.info(f"Loading EventBusClient configuration from {'path: ' + config_path if config_path else 'source'}")
      if (config_path is None and config_source is None) or (config_path is not None and config_source is not None):
         raise ValueError(f"Exactly one of config_path or config_source must be provided. config_path: {config_path}")

      if config_path is not None:
         config = PluginLoader.load_config(config_path)
      elif config_source is not None:
         if isinstance(config_source, str):
            config = CJsonPreprocessor().jsonLoads(config_source)
         elif isinstance(config_source, dict):
            config = config_source
         else:
            raise ValueError("config_source must be a str, dict, or JsonPreprocessor object")

         ConfigValidator(CONFIG_SCHEMA).validate(config)

      # Setup logger
      if "logger_name" not in config or not config.logger_name:
         config.logger_name = default_values["logger_name"]

      EventBusClient.LOGGER_NAME = config.logger_name
      logger_handler = None
      if "logfile" in config and config.logfile:
         logger_handler = QLogger().set_handler(config)

      if not "logfile" in config:
         config.logfile = None

      plugin_loader = PluginLoader()

      # Dynamic load components
      handler_cls: Type[ExchangeHandler] = plugin_loader.get_exchange_handler(config.exchange_handler)
      serializer_cls: Type[Serializer] = plugin_loader.get_serializer(config.serializer)

      serializer = serializer_cls()
      handler = handler_cls(serializer=serializer)
      auto_reconnect = config.get("auto_reconnect", True)
      client = cls(exchange_handler=handler,
                   serializer=serializer,
                   startup_policy=startup_policy,
                   auto_reconnect=auto_reconnect,
                   zone_id=zone_id,
                   alias=alias,
                   host=config.get("host", "localhost"),
                   port=config.get("port", 5672),
                   prefetch_count=config.get("qos_prefetch", 10))

      if not logger_handler:
         client._logger_handler = QLogger().set_handler(config)
      else:
         client._logger_handler = logger_handler


      notice = "Create event bus successfully from configurations:\n"
      for k in CONFIG_SCHEMA:
         if k in config:
            notice += f"  {k}: {config[k]}\n"
         else:
            notice += f"  {k}: {default_values[k]} (default)\n"

      LOGGER.info(notice)

      if start_connection:
         await client.connect(
            host=config.get("host", "localhost"),
            port=config.get("port", 5672),
            prefetch_count=config.get("prefetch_count", 10)
         )

      return client

   async def connect(self, host=None, port=None, prefetch_count: int = None, **kwargs):
      """
Connect to the event bus server and set up the exchange handler.

**Arguments:**

* ``host``

  / *Condition*: optional / *Type*: str / *Default*: None /

  Hostname of the event bus server. Defaults to None.

* ``port``

  / *Condition*: optional / *Type*: int / *Default*: None /

  Port number of the event bus server. Defaults to None.

* ``prefetch_count``

    / *Condition*: optional / *Type*: int / *Default*: None /

    The number of messages to prefetch from the server. This controls how many messages can be sent to the client before they are acknowledged. Defaults to None.
      """
      try:
         self.loop = asyncio.get_running_loop()
         self.connection.reset_loop(self.loop)
         self.exchange_handler.reset_loop(self.loop)
         self.host = host if host is not None else self.host
         self.port = port if port is not None else self.port
         self.prefetch_count = prefetch_count if prefetch_count is not None else self.prefetch_count
         await self.connection.connect(self.host, self.port, self.prefetch_count, **kwargs)
         await self.exchange_handler.setup(self.connection)
         self._connected = True
         # await self._startup_policy.wait_until_ready(self)
         cfg = kwargs.get("config_dict")  # or wherever you stash the parsed JSON
         if cfg and "event_bus" in cfg and not self._startup_policy:
            self._startup_policy = build_policy_from_config(cfg["event_bus"])

         # run policies (if any)
         if self._startup_policy:
            await self._startup_policy.wait_until_ready(self)
      except Exception as e:
         LOGGER.error(f"Failed to connect: {e}")
         raise

   async def send(self, routing_key: Union[str, list], message: BaseMessage, headers: dict = None, threadsafe=False):
      """
Send a message to the event bus with the specified routing key.

**Arguments:**

* ``routing_key``

  / *Condition*: required / *Type*: Union[str, list] /

  The routing key used to route the message to the appropriate subscribers. It can be a single string or a list of strings.

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
      # await self.exchange_handler.publish(message, routing_key, headers, threadsafe=threadsafe)
      LOGGER.info(f"[async def send] Sending message with routing key '{routing_key}': {message}")
      if isinstance(routing_key, list):
         for rk in routing_key:
            await self.exchange_handler.publish(message, rk, headers, threadsafe=threadsafe)
      else:
         await self.exchange_handler.publish(message, routing_key, headers, threadsafe=threadsafe)

      LOGGER.info(f"[async def send] Sent message with routing key '{routing_key}': {message}")

   async def off(self, routing_key: Union[str, list], callback: Optional[Callable[[BaseMessage], Awaitable[None]]] = None):
      """
Unsubscribe from messages with the specified routing key.

**Arguments:**

* ``routing_key``

  / *Condition*: required / *Type*: Union[str, list] /

  The routing key to unsubscribe from. It can be a single string or a list of strings.

* ``callback``

  / *Condition*: optional / *Type*: Callable[[BaseMessage], Awaitable[None]] / *Default*: None /

  The callback function to remove from the subscriber list. If not provided, all callbacks for the routing key will be unsubscribed.
      """
      if not self._connected:
         raise RuntimeError("EventBusClient is not connected")
      # await self.exchange_handler.unsubscribe(routing_key, callback)
      if isinstance(routing_key, list):
         for rk in routing_key:
            await self.exchange_handler.unsubscribe(rk, callback)
      else:
         await self.exchange_handler.unsubscribe(routing_key, callback)

   async def on(self,
                routing_key: str,
                message_cls: Type[BaseMessage],
                callback: Optional[Union[Callable[[BaseMessage, dict], Awaitable[None]], list[Callable[[BaseMessage, dict], Awaitable[None]]]]] = None,
                cache_size: Optional[int] = None):
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
      try:
         await self.exchange_handler.teardown()
         await self.connection.close()
         self._connected = False
      except BaseException as e:
         LOGGER.info(f"Error during close: {e}")

   def is_connected(self) -> bool:
      """
Check if the client is currently connected to the event bus.

**Returns:**

  / *Type*: bool /

  True if the client is connected, False otherwise.
      """
      return self._connected and self.connection.is_connected()

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
      # if self.zone_id:
      #    parts.append(self.zone_id)
      # if self.alias:
      #    parts.append(self.alias)
      return ".".join(parts)

   # ---------- Background loop lifecycle ----------
   def start_background_loop(self, *, loop_name: str = "EventBusClientLoop") -> None:
      """
Start a dedicated asyncio loop in a background thread if not already running.
Safe to call multiple times.

This method is useful for blocking synchronous APIs that need to run in a separate thread
to avoid blocking the main thread, especially in environments where the main thread is already running an event
loop (e.g., GUI applications, web servers).

This method will create a new thread that runs an asyncio event loop, allowing you to submit coroutines
for execution without blocking the main thread. It also ensures that the loop is ready before returning.
It will not start a new loop if one is already running in the background.

**Arguments:**

* ``loop_name``

  / *Condition*: optional / *Type*: str / *Default*: "EventBusClientLoop" /

  The name of the background thread running the asyncio loop. Defaults to "EventBusClientLoop".
      """
      if getattr(self, "_bg_loop_running", False):
         return

      self._loop_ready_evt = getattr(self, "_loop_ready_evt", threading.Event())
      self._bg_loop_running = False

      def _runner():
         try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self._bg_loop_running = True
            self._loop_ready_evt.set()
            self.loop.run_forever()
         finally:
            try:
               # best-effort graceful shutdown
               pending = [t for t in asyncio.all_tasks(self.loop) if not t.done()]
               for t in pending:
                  t.cancel()
               if pending:
                  self.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
               self.loop.run_until_complete(self.loop.shutdown_asyncgens())
            finally:
               self.loop.close()
               self._bg_loop_running = False

      self._bg_thread = threading.Thread(target=_runner, name=loop_name, daemon=True)
      self._bg_thread.start()
      # Wait the loop to be ready
      if not self._loop_ready_evt.wait(timeout=3.0):
         raise RuntimeError("Failed to start background asyncio loop")

   async def kill_aiormq_tasks_now(self):
      this = asyncio.current_task()
      victims = []
      for t in asyncio.all_tasks():
         if t is this or t.done():
            continue
         try:
            c = t.get_coro()
            mod = getattr(c, "__module__", "")
            qual = getattr(c, "__qualname__", "")
            if "aiormq" in mod or "aio_pika" in mod or "Connection.__" in qual or "Channel._reader" in qual:
               victims.append(t)
         except Exception:
            pass

      for t in victims:
         t.cancel()
      if victims:
         await asyncio.gather(*victims, return_exceptions=True)

   def stop_background_loop(self, *, timeout: float = 3.0) -> None:
      """
Stop the background loop (if we created it) and join the thread.

This method is useful for cleaning up resources when the client is no longer needed.

**Arguments:**

* ``timeout``

  / *Condition*: optional / *Type*: float / *Default*: 3.0 /

  The maximum time to wait for the background loop to stop. Defaults to 3.0 seconds.
      """
      if not getattr(self, "_bg_loop_running", False):
         return
      if self.loop and self.loop.is_running():
         self.loop.call_soon_threadsafe(self.loop.stop)
         # asyncio.run(self.kill_aiormq_tasks_now())
         # self.loop.call_soon_threadsafe(self.kill_aiormq_tasks_now)
      if getattr(self, "_bg_thread", None):
         self._bg_thread.join(timeout=timeout)

      self._bg_loop_running = False
      # if not getattr(self, "_bg_loop_running", False) or not self.loop:
      #    return
      #
      # async def _graceful_stop():
      #    # cancel any leftover tasks on this loop
      #    this = asyncio.current_task()
      #    tasks = [t for t in asyncio.all_tasks() if t is not this and not t.done()]
      #    for t in tasks:
      #       t.cancel()
      #    if tasks:
      #       await asyncio.gather(*tasks, return_exceptions=True)
      #    await self.loop.shutdown_asyncgens()
      #
      #    # run the graceful stop ON the loop
      #
      # fut = asyncio.run_coroutine_threadsafe(_graceful_stop(), self.loop)
      # try:
      #    fut.result(timeout=timeout)
      # finally:
      #    # now it is safe to stop and join
      #    self.loop.call_soon_threadsafe(self.loop.stop)
      #    if getattr(self, "_bg_thread", None):
      #       self._bg_thread.join(timeout=timeout)

   def _submit(self, coro, *, timeout: float | None = None):
      """
Submit an async coroutine to the background loop and wait for result (blocking).

**Arguments:**

* ``timeout``

  / *Condition*: optional / *Type*: float / *Default*: 3.0 /

  The maximum time to wait for the background loop to stop. Defaults to 3.0 seconds.
      """
      LOGGER.info(f"Submitting coroutine {coro} to background loop with timeout {timeout}")
      if not getattr(self, "_bg_loop_running", False):
         # If user already provided a running loop elsewhere, we cannot block current thread.
         # So always start our own loop for sync API.
         LOGGER.info("Starting background loop for sync operation")
         self.start_background_loop()
      LOGGER.info("caller_thread=%s loop_is_same=%s",
                  threading.current_thread().name,
                  (get_running_loop_or_none() is self.loop))
      if get_running_loop_or_none() is self.loop:
         import traceback
         stack = traceback.format_stack(limit=6)
         LOGGER.info("Stack (last 4 calls):\n%s", "".join(stack))

      LOGGER.info("Background loop is running, submitting coroutine")
      if not self.loop.is_running():
         LOGGER.error("Event loop is not running")
      if hasattr(self, "_bg_thread") and not self._bg_thread.is_alive():
         LOGGER.error("Background thread is not alive")
      fut = asyncio.run_coroutine_threadsafe(coro, self.loop)
      try:
         LOGGER.info("Waiting for coroutine result")
         return fut.result(timeout=timeout)
      except _FutTimeout as e:
         fut.cancel()
         raise TimeoutError("Operation timed out") from e

   # ---------- Sync wrappers over existing async APIs ----------
   @classmethod
   def from_config_sync(cls,
                        config_path: Optional[str] = None,
                        startup_policy: Optional[StartupPolicy] = None,
                        zone_id: Optional[str] = None,
                        alias: Optional[str] = None,
                        config_source: Optional[Union[str, dict]] = None) -> EventBusClient:
      """
Create an EventBusClient instance from a configuration file synchronously.

**Arguments:**

* ``path``

  / *Condition*: required / *Type*: str /

  Path to the configuration file in JSONP format. This file should contain the necessary configuration for the event bus client, including exchange handler and serializer settings.

**Returns:**

  / *Type*: EventBusClient /

  An instance of EventBusClient initialized with the configuration from the specified path.
      """
      loop = asyncio.new_event_loop()
      try:
         asyncio.set_event_loop(loop)
         client = loop.run_until_complete(cls.from_config(config_path, startup_policy, zone_id, alias, start_connection=False, config_source=config_source))
         return client
      finally:
         try:
            loop.run_until_complete(loop.shutdown_asyncgens())
         except Exception:
            pass
         loop.close()
         asyncio.set_event_loop(None)

   def connect_sync(self, host=None, port=None, prefetch_count: int = None,
                    *, timeout: float | None = 30.0) -> None:
      """
Blocking connect that spins a background loop if needed.

**Arguments:**

* ``host``

  / *Condition*: optional / *Type*: str / *Default*: "localhost" /

  The hostname of the event bus server. Defaults to "localhost".

* ``port``

  / *Condition*: optional / *Type*: int / *Default*: 5672 /

  The port number of the event bus server. Defaults to 5672.

* ``prefetch_count``

  / *Condition*: optional / *Type*: int / *Default*: 10 /

  The number of messages to prefetch from the server. This controls how many messages can be sent to the client before they are acknowledged. Defaults to 10.

* ``timeout``

  / *Condition*: optional / *Type*: float / *Default*: 30.0 /

  The maximum time to wait for the connection to be established. Defaults to 30.0 seconds.
      """
      try:
         self.start_background_loop()
         self.exchange_handler.reset_loop(self.loop)
         self.connection.reset_loop(self.loop)
         return self._submit(self.connect(host=host, port=port, prefetch_count=prefetch_count), timeout=timeout)
      except Exception as e:
         LOGGER.error(f"Failed to connect synchronously: {e}")
         raise Exception("Failed to connect synchronously")

   def send_sync(self, routing_key: str, message, headers: dict | None = None,
                 *, threadsafe: bool = False, timeout: float | None = 10.0) -> None:
      """
Blocking send wrapper.

**Arguments:**

* ``routing_key``

  / *Condition*: required / *Type*: str /

  The routing key used to route the message to the appropriate subscribers.

* ``message``

  / *Condition*: required / *Type*: BaseMessage /

  The message to be sent. It should be an instance of BaseMessage or its subclasses.

* ``headers``

  / *Condition*: optional / *Type*: dict | None /

  Additional headers to include with the message. This can be used for metadata or routing information.

* ``threadsafe``

  / *Condition*: optional / *Type*: bool / *Default*: False /

  If True, the message will be sent in a threadsafe manner. Defaults to False.

**Returns:**

  / *Type*: None /

  This method does not return any value. It sends the message to the event bus and returns immediately.
      """
      LOGGER.info(f"Sending message with routing key '{routing_key}': {message}")
      return self._submit(self.send(routing_key, message, headers=headers, threadsafe=threadsafe), timeout=timeout)

   def on_sync(self, routing_key: str, message_cls, callback=None, *,
               cache_size: int = 200, timeout: float | None = 10.0):
      """
Blocking subscribe wrapper. Returns SubscriptionCache to use with get()/wait_for()/drain().

**Arguments:**

* ``routing_key``

  / *Condition*: required / *Type*: str /

  The routing key to subscribe to. Messages with this routing key will be routed to the callback.

* ``message_cls``

  / *Condition*: required / *Type*: Type[BaseMessage] /

  The class of the message to subscribe to. The callback will receive messages of this type.

* ``callback``

  / *Condition*: optional / *Type*: Callable[[BaseMessage], Awaitable[None]] /

  The callback function to be called when a message is received. It should accept a single argument of type BaseMessage or its subclasses and return an awaitable (e.g., a coroutine).

* ``cache_size``

  / *Condition*: optional / *Type*: int / *Default*: 200 /

  The size of the cache for storing received messages. This is useful for buffering messages before they are processed by the callback.

**Returns:**
  / *Type*: SubscriptionCache /

  A SubscriptionCache object that allows you to manage the subscription and access received messages.
      """
      LOGGER.info(f"Subscribing to routing key '{routing_key}' with message class '{message_cls.__name__}'")
      return self._submit(
         self.on(routing_key, message_cls, callback, cache_size=cache_size),
         timeout=timeout
      )

   def off_sync(self, routing_key: str, *, timeout: float | None = 10.0) -> None:
      """
Blocking unsubscribe wrapper.

**Arguments:**

* ``routing_key``

   / *Condition*: required / *Type*: str /

   The routing key to unsubscribe from. Messages with this routing key will no longer be routed to the callback.

**Returns:**

   / *Type*: None /

   This method does not return any value. It unsubscribes from the specified routing key and returns immediately.
      """
      return self._submit(self.off(routing_key), timeout=timeout)

   def wait_until_ready_sync(self, requirements: dict[str, int], *, timeout: float = 5.0) -> bool:
      """
Blocking rendezvous wait. Returns True if satisfied before timeout.

**Arguments:**

* ``requirements``

   / *Condition*: required / *Type*: dict[str, int] /

   A dictionary where keys are role names and values are the number of instances required for each role.

* ``timeout``

   / *Condition*: optional / *Type*: float / *Default*: 5.0 /

   The maximum time to wait for the rendezvous to be satisfied. Defaults to 5.0 seconds.

**Returns:**

   / *Type*: bool /

   True if the rendezvous requirements are satisfied before the timeout, False otherwise.
      """
      return bool(self._submit(self.wait_until_ready(requirements, timeout=timeout), timeout=timeout + 1.0))

   def announce_ready_sync(self, roles: list[str], *, timeout: float | None = 5.0) -> None:
      """
Blocking announce ready via rendezvous control topic.

**Arguments:**

* ``roles``

   / *Condition*: required / *Type*: list[str] /

   A list of role names that this instance is ready for. This is used to signal readiness in the rendezvous system.

**Returns:**

   / *Type*: None /

   This method does not return any value. It announces that the instance is ready for the specified roles.
      """
      return self._submit(self.announce_ready(roles), timeout=timeout)

   def close_sync(self, *, timeout: float | None = 10.0) -> None:
      """
Optional: call your async close/teardown then stop the loop.
If you don’t have an async `close()`, this just stops the loop.

**Arguments:**

* ``timeout``

  / *Condition*: optional / *Type*: float / *Default*: 10.0 /

  The maximum time to wait for the close operation to complete. Defaults to 10.0 seconds.
      """
      if hasattr(self, "close") and callable(getattr(self, "close")):
         try:
            self._submit(self.close(), timeout=timeout)
         except Exception:
            # best effort
            pass
      self.stop_background_loop()


async def main():
   # Example usage
   client = await EventBusClient.from_config("config/config.jsonp")
   await client.connect()
   await client.send("test.routing.key", BasicMessage("Test"))
   await client.on("test.routing.key", BasicMessage, lambda msg: print(msg))
   await client.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    LOGGER.info("EventBusClient is ready to use.")
    asyncio.run(main())
