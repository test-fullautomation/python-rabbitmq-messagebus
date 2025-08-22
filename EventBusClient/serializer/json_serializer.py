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
# File: json_serializer.py
#
# Initially created by Nguyen Huynh Tri Cuong (MS/EMC51) / July 2025.
#
# Description:
#   JsonSerializer: Serializes BaseMessage subclasses to JSON strings.
#
# History:
#
# 17.07.2025 / V 1.0.0 / Nguyen Huynh Tri Cuong
# - Initialize
#
# *******************************************************************************
import json
from typing import Type
from EventBusClient.serializer.base_serializer import Serializer
from EventBusClient.message.base_message import BaseMessage


class JsonSerializer(Serializer):
   """
JsonSerializer: Serializes BaseMessage subclasses to JSON strings.
Requires message classes to implement:
   - to_dict()
   - from_dict(data: dict)
   """
   def serialize(self, msg: BaseMessage) -> bytes:
      """
Serialize a message object to JSON bytes.

**Arguments:**

* ``msg``

  / *Condition*: required / *Type*: BaseMessage /

  Message object to be serialized.

**Returns:**

  / *Type*: bytes /

  Serialized message as JSON bytes.
      """
      if hasattr(msg, "to_dict") and callable(msg.to_dict):
         try:
            json_str = json.dumps(msg.to_dict(), ensure_ascii=False)
            return json_str.encode("utf-8")
         except Exception as ex:
            raise RuntimeError(f"[JsonSerializer] Failed to serialize: {ex}")
      else:
         raise TypeError("[JsonSerializer] Message must implement to_dict()")

   def deserialize(self, data: bytes, message_cls: Type[BaseMessage] = None) -> BaseMessage:
      """
Deserialize bytes back into a message object.

**Arguments:**

* ``data``

  / *Condition*: required / *Type*: bytes /

  Serialized message data in bytes format.

* ``message_cls``

  / *Condition*: required / *Type*: Type[BaseMessage] /

  Class of the message to deserialize into.

**Returns:**

  / *Type*: str /

  Deserialized message object of type `message_cls`.

**Raises:**

* ``ValueError``
  If `message_cls` is not provided.

* ``TypeError``
  If `message_cls` does not implement `from_dict(data: dict)`.

* ``RuntimeError``
  If deserialization fails due to invalid data or other issues.
      """
      if not message_cls:
         raise ValueError("[JsonSerializer] message_cls must be provided for deserialization")

      if hasattr(message_cls, "from_dict") and callable(message_cls.from_dict):
         try:
            json_str = data.decode("utf-8")
            obj_dict = json.loads(json_str)
            return message_cls.from_data(data=obj_dict)
         except Exception as ex:
            raise RuntimeError(f"[JsonSerializer] Failed to deserialize: {ex}")
      else:
         raise TypeError("[JsonSerializer] message_cls must implement from_dict(data)")
