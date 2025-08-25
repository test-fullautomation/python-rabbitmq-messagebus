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
# File: startup_policy.py
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
from typing import Protocol, Optional, Dict, Iterable, Union

if False:  # type checking helpers
    from .event_bus_client import EventBusClient

ControllerAlias = Union[str, Iterable[str]]
SYSTEM_UP_WAIT_TIME = 60

def _is_controller_alias(alias: Optional[str], controller_alias: ControllerAlias) -> bool:
    if alias is None:
        return False
    a = alias.strip().lower()
    if isinstance(controller_alias, str):
        return a == controller_alias.strip().lower()
    return any(a == x.strip().lower() for x in controller_alias)

class StartupPolicy(Protocol):
    async def wait_until_ready(self, bus: "EventBusClient") -> None: ...

class NoWait:
    async def wait_until_ready(self, bus: "EventBusClient") -> None:
        # Never block startup
        return

class FixedDelay:
    def __init__(self, seconds: float) -> None:
        self.seconds = seconds
    async def wait_until_ready(self, bus: "EventBusClient") -> None:
        await asyncio.sleep(self.seconds)

class HandshakeBarrier:
    """
    Wait until at least N consumers announce ready for the given roles/topics.
    Example:
        HandshakeBarrier({"telemetry.*": 1, "orders.created": 2}, timeout=5.0)
    """
    def __init__(self, requirements: Dict[str, int], timeout: float = 5.0) -> None:
        self.requirements = dict(requirements)
        self.timeout = timeout

    async def wait_until_ready(self, bus: "EventBusClient") -> None:
        await bus.rendezvous.wait_for(self.requirements, timeout=self.timeout)


class PanelControlLegacyByAlias:
    """Legacy start() behavior but role is inferred from alias."""
    def __init__(self, panel_control: bool, wait_time: float =SYSTEM_UP_WAIT_TIME,
                 controller_alias: ControllerAlias = "controller") -> None:
        self.panel_control = panel_control
        self.wait_time = wait_time
        self.controller_alias = controller_alias

    async def wait_until_ready(self, bus: "EventBusClient") -> None:
        is_controller = _is_controller_alias(getattr(bus, "alias", None), self.controller_alias)
        system_up = bool(getattr(bus, "system_up", False))

        if self.panel_control and not (system_up or is_controller):
            return  # GUI path: return immediately

        if not is_controller:
            await asyncio.sleep(self.wait_time)
            if hasattr(bus, "system_up") and getattr(bus, "system_up") is False:
                setattr(bus, "system_up", True)
