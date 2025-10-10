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
from typing import Protocol, Optional, Dict, Iterable, Union, Sequence, Any, Type
from importlib import import_module
import pydoc
from .message.base_message import BaseMessage

# pylint: disable=W0611
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
    """
A startup policy can delay or block the completion of EventBusClient.start()
until certain conditions are met.
This can be used to implement rendezvous patterns, fixed delays, or
other custom logic.
    """
    async def wait_until_ready(self, bus: "EventBusClient") -> None: ...

class NoWait:
    """
No waiting, start immediately.
    """
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

def _locate(path: str) -> Any | None:
    # pydoc.locate handles many dotted-path cases
    obj = pydoc.locate(path)
    if obj is not None:
        return obj
    if "." not in path:
        return None
    mod, _, attr = path.rpartition(".")
    try:
        m = import_module(mod)
        return getattr(m, attr, None)
    except Exception:
        return None

def resolve_message_cls(
    value: str | type | None,
    *,
    base_cls: type,
    registry: dict[str, type] | None = None,
    extra_modules: list[str] | None = None,
    default: type | None = None,
) -> type:
    """
    Turn a JSON 'class' string into an actual class object.
    Accepts a dotted path ('pkg.mod.Class') or a short name via registry.
    """
    if isinstance(value, type):
        if issubclass(value, base_cls):
            return value
        raise TypeError(f"{value!r} is not a subclass of {base_cls.__name__}")

    if value is None:
        if default is None:
            raise ValueError("No message class provided and no default specified.")
        return default

    if registry and value in registry:
        cls = registry[value]
        if issubclass(cls, base_cls):
            return cls
        raise TypeError(f"Registry entry '{value}' is not a subclass of {base_cls.__name__}")

    # Try dotted path
    obj = _locate(value)
    if isinstance(obj, type) and issubclass(obj, base_cls):
        return obj

    # Try short name inside extra modules
    if extra_modules:
        for mod in extra_modules:
            try:
                m = import_module(mod)
                if hasattr(m, value):
                    cls = getattr(m, value)
                    if isinstance(cls, type) and issubclass(cls, base_cls):
                        return cls
            except Exception:  # pylint: disable=broad-except
                pass

    raise ValueError(
        f"Cannot resolve message class '{value}'. "
        "Use a full dotted path or register the short name."
    )

class GeneralCacheStartupPolicy:
    """
    Example startup policy that decides whether to start a 'general cache'
    at connect-time, and with which routing keys / message class.
    Can be alias-aware.
    """
    def __init__(
        self,
        *,
        routing_keys: Union[str, Sequence[str]] = ("general",),
        message_cls: Union[str, type] = "BasicMessage",   # dotted path or short name
        only_for_alias: Optional[str] = None,             # e.g. "controller", or None = any
    ) -> None:
        self._routing_keys = routing_keys
        self._message_cls = message_cls
        self._only_for_alias = only_for_alias

    async def wait_until_ready(self, client: "EventBusClient") -> None:
        # If alias-constrained, skip when not matching
        if self._only_for_alias and getattr(client, "alias", None) != self._only_for_alias:
            return

        # Resolve message class string → actual type
        msg_cls = resolve_message_cls(
            self._message_cls,
            base_cls=BaseMessage,
            registry=None,
            extra_modules=[
                "EventBusClient.message.basic_message",
                "EventBusClient.message.string_msg",
                "EventBusClient.message.dict_msg"
            ],
            default=None,  # force explicit resolve so config errors are loud
        )

        # Start the general listener now so it captures messages from the beginning
        await client.enable_general_cache(
            routing_keys=self._routing_keys,
            message_cls=msg_cls,
        )

class PolicyChain(StartupPolicy):
    """
Apply multiple policies either sequentially or in parallel.
- mode="sequential": run in order; if fail_fast=True, stop on first exception.
- mode="parallel": run concurrently; if fail_fast=True, propagate first exception (gather(..., return_exceptions=False)).
    """
    def __init__(self, policies: list[StartupPolicy],
                 mode: str = "sequential",
                 fail_fast: bool = True) -> None:
        self.policies = list(policies)
        self.mode = mode
        self.fail_fast = fail_fast

    async def wait_until_ready(self, bus: "EventBusClient") -> None:
        if not self.policies:
            return

        if self.mode == "parallel":
            if self.fail_fast:
                await asyncio.gather(*(p.wait_until_ready(bus) for p in self.policies))
            else:
                results = await asyncio.gather(*(p.wait_until_ready(bus) for p in self.policies),
                                               return_exceptions=True)
                # Log but don’t raise
                for r in results:
                    if isinstance(r, Exception) and hasattr(bus, "logger"):
                        bus.logger.error("[policy:parallel] %s", r)
            return

        # sequential
        for p in self.policies:
            try:
                await p.wait_until_ready(bus)
            except Exception:
                if self.fail_fast:
                    raise
                if hasattr(bus, "logger"):
                    bus.logger.exception("[policy:sequential] policy %s failed (continuing)", p.__class__.__name__)

def build_policy_from_item(item: dict) -> StartupPolicy:
    """
    item = {
        "class": "pkg.PolicyClass",
        "args": { ... },                 # optional
        "wrap": [                        # optional, outermost first
            {"class": "pkg.WithTimeout", "args": {"seconds": 10, "swallow": true}},
            {"class": "pkg.WithLogging"}
        ]
    }
    """
    cls = _locate(item["class"])
    if cls is None:
        raise ValueError(f"Cannot locate policy class {item['class']}")
    base = cls(**item.get("args", {}))

    for wrap in item.get("wrap", []):
        wcls = _locate(wrap["class"])
        if wcls is None:
            raise ValueError(f"Cannot locate wrapper class {wrap['class']}")
        base = wcls(base, **wrap.get("args", {}))
    return base


def build_policy_from_config(cfg: dict) -> Optional[StartupPolicy]:
    """
    Supports both legacy and new formats.

    Legacy:
      "startup_policy": "pkg.PolicyClass"
      "startup_policy_args": { ... }

    New multi:
      "startup_policies_mode": "sequential" | "parallel"
      "startup_policies_fail_fast": true|false
      "startup_policies": [
        {"class": "pkg.PolicyA", "args": {...}},
        {"class": "pkg.PolicyB", "args": {...}, "wrap": [{"class":"pkg.WithTimeout", "args":{"seconds":5}}]}
      ]
    """
    # New multi
    items = cfg.get("startup_policies")
    if items:
        policies = [build_policy_from_item(it) for it in items]
        mode = cfg.get("startup_policies_mode", "sequential")
        fail_fast = bool(cfg.get("startup_policies_fail_fast", True))
        return PolicyChain(policies, mode=mode, fail_fast=fail_fast)

    # Legacy single
    sp = cfg.get("startup_policy")
    if sp:
        cls = _locate(sp)
        if cls is None:
            raise ValueError(f"Cannot locate policy class {sp}")
        base = cls(**cfg.get("startup_policy_args", {}))
        return base

    return None