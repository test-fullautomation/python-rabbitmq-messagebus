
from __future__ import annotations
from dataclasses import dataclass, field
import time
import uuid
from EventBusClient.message.base_message import BaseMessage

@dataclass
class ControlMessage(BaseMessage):
    kind: str
    roles: list[str] = field(default_factory=list)
    instance_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    ts: float = field(default_factory=lambda: time.time())

    def get_value(self):
        # For serializers that inspect value, but our transports pickle the object itself.
        return {
            "kind": self.kind,
            "roles": list(self.roles),
            "instance_id": self.instance_id,
            "ts": self.ts,
        }

    @classmethod
    def from_data(cls, data):
        # For serializers that inspect value, but our transports pickle the object itself.
        return cls(
            kind=data.get("kind", ""),
            roles=data.get("roles", []),
            instance_id=data.get("instance_id", uuid.uuid4().hex),
            ts=data.get("ts", time.time())
        )

