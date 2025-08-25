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
# File: rendezvous.py
#
# Initially created by Nguyen Huynh Tri Cuong (MS/EMC51) / July 2025.
#
# Description:
#
#   Rendezvous: Manages readiness announcements for distributed components.
#
# History:
#
# 12.08.2025 / V 1.0.0 / Nguyen Huynh Tri Cuong
# - Initialize
#
# *******************************************************************************
from __future__ import annotations
import asyncio
from typing import Dict, List, Set
from fnmatch import fnmatch
from EventBusClient.message.control_message import ControlMessage

class Rendezvous:
    READY_TOPIC = "sys.rendezvous.ready"

    def __init__(self, bus: "EventBusClient") -> None:
        """
Initialize the Rendezvous manager with the given EventBusClient instance.

**Arguments:**

* ``bus``

  / *Condition*: required / *Type*: EventBusClient /

  The EventBusClient instance used for communication.
        """
        self._bus = bus
        # Track our own instance id for announce_ready convenience
        self._instance_id = None

    async def announce_ready(self, roles: List[str]) -> None:
        """
Broadcast that this process is ready to consume for the given roles.
Call this once after you have subscribed/initialized consumers.

**Arguments:**

* ``roles``

  / *Condition*: required / *Type*: List[str] /

  A list of roles or topic patterns that this instance is ready to handle.
        """
        if self._instance_id is None:
            # create a stable id per process
            import uuid
            self._instance_id = uuid.uuid4().hex
        msg = ControlMessage(kind="ready", roles=list(roles), instance_id=self._instance_id)
        await self._bus.send(self.READY_TOPIC, msg)

    async def wait_for(self, requirements: Dict[str, int], timeout: float = 5.0) -> bool:
        """
Wait until we have observed readiness announcements satisfying the requirements.
`requirements` maps a role/topic pattern -> minimum unique instance count.
Returns True if satisfied before timeout, False otherwise.

**Arguments:**

* ``requirements``

  / *Condition*: required / *Type*: Dict[str, int] /

  A dictionary mapping role or topic patterns to the minimum number of unique instances required.

* ``timeout``

  / *Condition*: optional / *Type*: float /

  The maximum time to wait for the requirements to be satisfied, in seconds. Defaults to 5.0 seconds.
        """
        remaining = dict(requirements)
        # Normalize counts
        for k, v in list(remaining.items()):
            remaining[k] = int(v) if int(v) > 0 else 1

        # Track which instance ids have satisfied which patterns
        satisfied: Dict[str, Set[str]] = {pat: set() for pat in remaining}

        done = asyncio.Event()

        async def _on_ready(msg: ControlMessage):
            if not isinstance(msg, ControlMessage) or msg.kind != "ready":
                return
            inst = msg.instance_id
            for pat in remaining:
                # If any of msg.roles matches the pattern, count this instance
                if any(fnmatch(role, pat) for role in msg.roles):
                    satisfied[pat].add(inst)
            # Check global condition
            if all(len(satisfied[pat]) >= remaining[pat] for pat in remaining):
                done.set()

        # Subscribe and set a timeout race
        await self._bus.on(self.READY_TOPIC, ControlMessage, _on_ready)
        try:
            try:
                await asyncio.wait_for(done.wait(), timeout=timeout)
                return True
            except asyncio.TimeoutError:
                return False
        finally:
            await self._bus.off(self.READY_TOPIC)
