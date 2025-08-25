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
# File: protobuf_serializer.py
#
# Initially created by Nguyen Huynh Tri Cuong (MS/EMC51) / July 2025.
#
# Description:
#
#    ProtobufSerializer: Serializer using Protocol Buffers.
#
# History:
#
# 17.07.2025 / V 1.0.0 / Nguyen Huynh Tri Cuong
# - Initialize
#
# *******************************************************************************
from google.protobuf.message import Message
from EventBusClient.serializer.base_serializer import Serializer

class ProtobufSerializer(Serializer):
    """
ProtobufSerializer: Serializer using Protocol Buffers.

Requires protobuf message classes generated from .proto files.
    """

    def serialize(self, msg: Message) -> bytes:
        """
Serialize a protobuf message object to bytes.

**Arguments:**

* ``msg``

  / *Condition*: required / *Type*: Message /

  Protobuf message object to be serialized.
        """
        try:
            return msg.SerializeToString()
        except Exception as ex:
            raise RuntimeError(f"[ProtobufSerializer] Failed to serialize: {ex}")

    def deserialize(self, data: bytes, message_cls) -> Message:
        """
Deserialize bytes back into a protobuf message object.

**Arguments:**

* ``data``

  / *Condition*: required / *Type*: bytes /

  Serialized protobuf message data to be deserialized.

* ``message_cls``

  / *Condition*: required / *Type*: type /

  Protobuf message class to instantiate.
        """
        try:
            msg = message_cls()
            msg.ParseFromString(data)
            return msg
        except Exception as ex:
            raise RuntimeError(f"[ProtobufSerializer] Failed to deserialize: {ex}")