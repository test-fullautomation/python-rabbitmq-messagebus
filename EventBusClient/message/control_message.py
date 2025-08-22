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
# File: control_message.py
#
# Initially created by Nguyen Huynh Tri Cuong (MS/EMC51) / August 2025.
#
# Description:
#
#   ControlMessage: Represents a control message for distributed components.
#
# History:
#
# 12.08.2025 / V 1.0.0 / Nguyen Huynh Tri Cuong
# - Initialize
#
# *******************************************************************************
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

