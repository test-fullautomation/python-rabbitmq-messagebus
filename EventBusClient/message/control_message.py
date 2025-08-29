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

    @staticmethod
    def _validate_list_field(value, field_name="roles"):
        """Validate that a field is a list[str] or None."""
        if value is not None and not isinstance(value, list):
            raise TypeError(f"{field_name} must be a list[str] or None, got {type(value).__name__}")

        # Validate that all elements in the list are strings (if value is not None)
        if value is not None:
            for i, item in enumerate(value):
                if not isinstance(item, str):
                    raise TypeError(f"{field_name}[{i}] must be a string, got {type(item).__name__}")

    @staticmethod
    def _validate_string_field(value, field_name):
        """Validate that a field is a string or None."""
        if value is not None and not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string or None, got {type(value).__name__}")

    @staticmethod
    def _validate_numeric_field(value, field_name):
        """Validate that a field is a number (int or float) or None."""
        if value is not None and not isinstance(value, (int, float)):
            raise TypeError(f"{field_name} must be a number (int or float) or None, got {type(value).__name__}")

    def _validate_all_fields(self):
        """Validate all fields of the ControlMessage."""
        self._validate_list_field(self.roles, "roles")
        self._validate_string_field(self.kind, "kind")
        self._validate_string_field(self.instance_id, "instance_id")
        self._validate_numeric_field(self.ts, "ts")

    def __post_init__(self):
        """Validate the data types after object initialization."""
        # Note: We allow None for other fields to preserve existing behavior
        self._validate_all_fields()

    def get_value(self):
        # For serializers that inspect value, but our transports pickle the object itself.
        return {
            "kind": self.kind,
            "roles": list(self.roles) if self.roles is not None else None,
            "instance_id": self.instance_id,
            "ts": self.ts,
        }

    @classmethod
    def from_data(cls, data):
        # For serializers that inspect value, but our transports pickle the object itself.
        # Validate input data before creating the object
        if not isinstance(data, dict):
            raise TypeError(f"data must be a dictionary, got {type(data).__name__}")

        # Extract fields from data
        kind = data.get("kind", "")
        roles = data.get("roles", [])
        instance_id = data.get("instance_id", uuid.uuid4().hex)
        ts = data.get("ts", time.time())

        # Validate all fields using the helper methods
        cls._validate_list_field(roles, "data['roles']")
        cls._validate_string_field(kind, "data['kind']")
        cls._validate_string_field(instance_id, "data['instance_id']")
        cls._validate_numeric_field(ts, "data['ts']")

        return cls(
            kind=kind,
            roles=roles,
            instance_id=instance_id,
            ts=ts
        )

