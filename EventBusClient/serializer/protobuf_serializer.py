
# EventBusClient/serializer/protobuf_serializer.py

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