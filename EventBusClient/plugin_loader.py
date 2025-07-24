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
from serializer.base_serializer import Serializer
from exchange_handler.base import ExchangeHandler
from message.base_message import BaseMessage
from utils import Utils
from pydotdict import DotDict
# from exchange_handler.topic_handler import TopicExchangeHandler


class PluginLoader:
   def __init__(self, base_path: str = None):
      """
PluginLoader: Dynamically loads serializers, exchange handlers, and messages.

**Arguments:**

* ``base_path``

   / *Condition*: optional / *Type*: str /

   Base path to search for plugins. Defaults to the directory of this file.
      """
      self.base_path = base_path or os.path.dirname(os.path.abspath(__file__))

      self.serializer_dict: Dict[str, Type[Serializer]] = {}
      self.exchange_handler_dict: Dict[str, Type[ExchangeHandler]] = {}
      self.message_dict: Dict[str, Type[BaseMessage]] = {}

      self._load_all_modules()
      self._register_classes()

   def _load_all_modules(self):
      """
Load all Python modules from built-in folders and plugins.
      """
      search_paths = [
         os.path.join(self.base_path, "serializer"),
         os.path.join(self.base_path, "message"),
         os.path.join(self.base_path, "exchange_handler"),
         os.path.join(self.base_path, "plugins")
      ]

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

   def load_config(self, config_path: str) -> DotDict | None:
      """
Load configuration from a JSONP file located in the same directory as the given config path.

**Arguments:**

* ``config_path``

   / *Condition*: required / *Type*: str /

   Path to the configuration file. If it is a relative path, it will be resolved to an absolute path.

**Returns:**

   / *Type*: DotDict | None /

   A DotDict containing the configuration data if the file exists and is loaded successfully, otherwise None.
      """
      file_path = config_path if os.path.isabs(config_path) else os.path.abspath(config_path)
      if file_path:
         config_dir = os.path.dirname(os.path.abspath(file_path))
         return CJsonPreprocessor().jsonLoad(
            os.path.join(config_dir, "config.jsonp")
         )
      return None


if __name__ == "__main__":
   # Example usage
   loader = PluginLoader()
   print("Available serializers:", loader.serializer_dict.keys())
   print("Available exchange handlers:", loader.exchange_handler_dict.keys())
   print("Available messages:", loader.message_dict.keys())