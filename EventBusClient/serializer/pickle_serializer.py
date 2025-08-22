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
# File: pickle_serializer.py
#
# Initially created by Nguyen Huynh Tri Cuong (MS/EMC51) / July 2025.
#
# Description:
#   PickleSerializer: Built-in serializer using Python pickle.
#
# History:
#
# 17.07.2025 / V 1.0.0 / Nguyen Huynh Tri Cuong
# - Initialize
#
# *******************************************************************************
import pickle
from typing import Any
from EventBusClient.serializer.base_serializer import Serializer


class PickleSerializer(Serializer):
   """
PickleSerializer: Built-in serializer using Python pickle.

WARNING: Pickle is not secure against untrusted data.
Only use in trusted environments.
   """

   def serialize(self, msg: Any) -> bytes:
      """
Serialize a message object to bytes using pickle.

**Arguments:**

* ``msg``

  / *Condition*: required / *Type*: Any /

  Message object to be serialized.
      """
      try:
         return pickle.dumps(msg, protocol=pickle.HIGHEST_PROTOCOL)
      except Exception as ex:
         raise RuntimeError(f"[PickleSerializer] Failed to serialize: {ex}")

   def deserialize(self, data: bytes) -> Any:
      """
Deserialize bytes back into a message object using pickle.

**Arguments:**

* ``data``

  / *Condition*: required / *Type*: bytes /

  Serialized message data to be deserialized.
      """
      try:
         return pickle.loads(data)
      except Exception as ex:
         raise RuntimeError(f"[PickleSerializer] Failed to deserialize: {ex}")
