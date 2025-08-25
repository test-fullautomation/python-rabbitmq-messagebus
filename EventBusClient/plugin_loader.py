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
# File: plugin_loader.py
#
# Initially created by Nguyen Huynh Tri Cuong (MS/EMC51) / July 2025.
#
# Description:
#
#   PluginLoader: Dynamically loads serializers, exchange handlers, and messages.
#
# History:
#
# 17.07.2025 / V 1.0.0 / Nguyen Huynh Tri Cuong
# - Initialize
#
# *******************************************************************************
import os
import sys
import pkgutil
import importlib
from typing import Dict, Type
from JsonPreprocessor.CJsonPreprocessor import CJsonPreprocessor
from .serializer.base_serializer import Serializer
from .exchange_handler.base import ExchangeHandler
from .message.base_message import BaseMessage
from .utils import Utils
from pydotdict import DotDict
# from exchange_handler.topic_handler import TopicExchangeHandler


CONFIG_SCHEMA = {
    "plugins_path": str,
    "host": str,
    "port": int,
    "serializer": str,
    "exchange_handler": str,
    "auto_reconnect": bool,
    "qos_prefetch": int
}

class ConfigValidator:
   """
Validates configuration data against a given schema.
Raises ValueError if validation fails.
   """
   def __init__(self, schema: dict):
      self.schema = schema

   def validate(self, config: dict):
      """
Validate the configuration against the schema.

**Arguments:**

* ``config``

  / *Condition*: required / *Type*: dict /

  Configuration data to validate.
      """
      required_keys = ["serializer", "exchange_handler"]
      for key in required_keys:
         if key not in config:
            raise ValueError(f"Missing required key: {key}")

      for key, value_type in self.schema.items():
         if key in config:
            if not isinstance(config[key], value_type):
               raise ValueError(f"Key '{key}' must be of type {value_type.__name__}, got {type(config[key]).__name__}")
            if key == "port":
               if not (1024 <= config[key] <= 65535):
                  raise ValueError("Port must be between 1024 and 65535")
            if key == "plugins_path":
               path = config[key]
               paths = path if isinstance(path, (list, tuple)) else [path]
               for p in paths:
                  # if not isinstance(p, str) or not os.path.exists(os.path.abspath(p)):
                  
                  if not isinstance(p, str) or not os.path.exists(
                          os.path.join(os.path.dirname(os.path.abspath(__file__)), p) if not os.path.isabs(p) else p):
                     raise ValueError(f"plugins_path '{p}' is not a valid path")

      extra_keys = set(config.keys()) - set(self.schema.keys())
      if extra_keys:
         raise ValueError(f"Unknown config keys: {', '.join(list(extra_keys))}")

      return True


class PluginLoader:
   """
The `PluginLoader` class dynamically loads serializers, exchange handlers, and messages.
   
This class scans specified directories for Python modules, imports them, and registers
any classes that match the expected base types (e.g., `Serializer`, `ExchangeHandler`,
and `BaseMessage`). It is designed to facilitate the dynamic discovery and use of
plugins in the application.
   """
   def __init__(self, base_path: str | os.PathLike | list[str | os.PathLike] | None = None):
      """
PluginLoader: Dynamically loads serializers, exchange handlers, and messages.

**Arguments:**

* ``base_path``

  / *Condition*: optional / *Type*: str, os\.PathLike, or list of these /

  Base path(s) to search for plugins. Defaults to the directory of this file.
      """
      # self.base_path = base_path or os.path.dirname(os.path.abspath(__file__))
      self.base_path = []
      if base_path is not None:
         paths = base_path if isinstance(base_path, (list, tuple)) else [base_path]
         plugin_dir = os.path.dirname(os.path.abspath(__file__))
         for p in paths:
            abs_path = os.fspath(p)
            if not os.path.isabs(abs_path):
               abs_path = os.path.join(plugin_dir, abs_path)
            self.base_path.append(os.path.abspath(abs_path))
      self.base_path.append(os.path.dirname(os.path.abspath(__file__)))
      self.serializer_dict: Dict[str, Type[Serializer]] = {}
      self.exchange_handler_dict: Dict[str, Type[ExchangeHandler]] = {}
      self.message_dict: Dict[str, Type[BaseMessage]] = {}

      self._load_all_modules()
      self._register_classes()

   def _load_all_modules(self):
      """
Load all Python modules from built-in folders and plugins.
      """
      search_paths = []
      for base in self.base_path:
         if os.path.isdir(base):
            for item in os.listdir(base):
               item_path = os.path.join(base, item)
               if os.path.isdir(item_path):
                  for sub in ["serializer", "message", "exchange_handler"]:
                     sub_path = os.path.join(item_path, sub)
                     if os.path.isdir(sub_path):
                        search_paths.append(sub_path)
               # Add the base directory itself
               search_paths.append(item_path)
         # Also add the direct subfolders for backward compatibility
         for sub in ["serializer", "message", "exchange_handler"]:
            direct_sub_path = os.path.join(base, sub)
            if os.path.isdir(direct_sub_path):
               search_paths.append(direct_sub_path)

      # Add search paths to sys.path if not already there
      for path in search_paths:
         if path not in sys.path:
            sys.path.append(path)

      # Walk and import all modules
      for finder, name, is_pkg in pkgutil.walk_packages(search_paths):
         try:
            if not is_pkg and not name.endswith(".base"):
               importlib.import_module(name)
         except Exception as ex:
            print(f"⚠️ Failed to load module '{name}': {ex}")

   def _register_classes(self):
      """
Register all serializers, exchange handlers, and messages found in the loaded modules.
      """
      # Register all serializers
      serializers = Utils.get_all_descendant_classes(Serializer)
      self.serializer_dict = {
         cls.__name__: cls for cls in serializers if hasattr(cls, "__name__")
      }

      # Register all exchange handlers
      handlers = Utils.get_all_descendant_classes(ExchangeHandler)
      self.exchange_handler_dict = {
         cls.__name__: cls for cls in handlers if hasattr(cls, "__name__")
      }

      # Register all messages
      messages = Utils.get_all_descendant_classes(BaseMessage)
      self.message_dict = {
         cls.__name__: cls for cls in messages if hasattr(cls, "__name__")
      }

   def get_serializer(self, name: str) -> Type[Serializer]:
      """
Get a serializer class by its name.

**Arguments:**

* ``name``

  / *Condition*: required / *Type*: str /

  Name of the serializer class to retrieve.

**Returns:**

  / *Type*: Serializer | None /

  Serializer class or None if not found.
      """
      if name not in self.serializer_dict:
         available = ", ".join(list(self.serializer_dict.keys()))
         raise ValueError(f"Unknown serializer: {name}. Please select one of: {available}")

      return self.serializer_dict.get(name)

   def get_exchange_handler(self, name: str) -> Type[ExchangeHandler]:
      """
Get an exchange handler class by its name.

**Arguments:**

* ``name``

  / *Condition*: required / *Type*: str /

  Name of the exchange handler class to retrieve.

**Returns:**

  / *Type*: ExchangeHandler | None /

  Exchange handler class or None if not found.
      """
      if name not in self.exchange_handler_dict:
         available = ", ".join(list(self.exchange_handler_dict.keys()))
         raise ValueError(f"Unknown exchange handler type: {name}. Please select one of: {available}")

      return self.exchange_handler_dict.get(name)

   def get_message(self, name: str) -> Type[BaseMessage]:
      """
Get a message class by its name.

**Arguments:**

* ``name``

  / *Condition*: required / *Type*: str /

  Name of the message class to retrieve

**Returns:**

  / *Type*: BaseMessage | None /

  Message class or None if not found.
      """
      return self.message_dict.get(name)

   @staticmethod
   def load_config(config_path: str) -> DotDict | None:
      """
Load configuration from a JSONP file and validate it against the schema.

**Arguments:**

* ``config_path``

  / *Condition*: required / *Type*: str /

  Path to the configuration file. If it is a relative path, it will be resolved to an absolute path.

**Returns:**

  / *Type*: DotDict | None /

  A DotDict containing the configuration data if the file exists and is loaded successfully, otherwise None.
      """
      file_path = config_path if os.path.isabs(config_path) else os.path.abspath(config_path)
      config_data = None
      if file_path:
         config_dir = file_path if os.path.isdir(file_path) else os.path.dirname(os.path.abspath(file_path))
         config_file = file_path if os.path.isfile(file_path) else os.path.join(config_dir, "config.jsonp")
         config_data = CJsonPreprocessor().jsonLoad(config_file)

      if config_data:
         ConfigValidator(CONFIG_SCHEMA).validate(config_data)

      return config_data

      #    return CJsonPreprocessor().jsonLoad(
      #       os.path.join(config_dir, "config.jsonp")
      #    )
      # return None


if __name__ == "__main__":
   # Example usage
   loader = PluginLoader()
   print("Available serializers:", loader.serializer_dict.keys())
   print("Available exchange handlers:", loader.exchange_handler_dict.keys())
   print("Available messages:", loader.message_dict.keys())