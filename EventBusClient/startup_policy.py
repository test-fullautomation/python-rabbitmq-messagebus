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
# from .message.base_message import BaseMessage

# pylint: disable=W0611
if False:  # type checking helpers
    from .event_bus_client import EventBusClient

ControllerAlias = Union[str, Iterable[str]]
SYSTEM_UP_WAIT_TIME = 60

def _is_controller_alias(alias: Optional[str], controller_alias: ControllerAlias) -> bool:
    """
Check if the given alias matches the controller alias(es).

**Arguments:**

* ``alias``

  / *Condition*: required / *Type*: Optional[str] /

  The alias to check.

* ``controller_alias``

  / *Condition*: required / *Type*: ControllerAlias /

  The controller alias or list of aliases to match against.

**Returns:**

  / *Type*: bool /

  True if the alias matches the controller alias(es), False otherwise.
    """
    if alias is None:
        return False
    a = alias.strip().lower()
    if isinstance(controller_alias, str):
        return a == controller_alias.strip().lower()
    return any(a == x.strip().lower() for x in controller_alias)

def _maybe_has(obj, name: str) -> bool:
    return hasattr(obj, name) and callable(getattr(obj, name))

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
        """
Wait until ready - no wait.

**Arguments:**

* ``bus``

  / *Condition*: required / *Type*: EventBusClient /

  The EventBusClient instance.

**Returns:**

  / *Type*: None /

  None
        """
        # Never block startup
        return

class FixedDelay:
    def __init__(self, seconds: float) -> None:
        """
Initialize a FixedDelay startup policy.

**Arguments:**

* ``seconds``

  / *Condition*: required / *Type*: float /

  The fixed delay in seconds before proceeding.
        """
        self.seconds = seconds

    async def wait_until_ready(self, bus: "EventBusClient") -> None:
        """
Wait for a fixed delay before proceeding.

**Arguments:**

* ``bus``

  / *Condition*: required / *Type*: EventBusClient /

  The EventBusClient instance.
        """
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
    """
Legacy startup policy for panel control mode based on controller alias.
    """
    def __init__(self, panel_control: bool, wait_time: float =SYSTEM_UP_WAIT_TIME,
                 controller_alias: ControllerAlias = "controller") -> None:
        """
Initialize the PanelControlLegacyByAlias startup policy.

**Arguments:**

* ``panel_control``

  / *Condition*: required / *Type*: bool /

  Whether the system is in panel control mode.

* ``wait_time``

  / *Condition*: optional / *Type*: float / *Default*: SYSTEM_UP_WAIT_TIME /

  The wait time in seconds before marking the system as up.

* ``controller_alias``

  / *Condition*: optional / *Type*: ControllerAlias / *Default*: "controller" /

  The controller alias or list of aliases.
        """
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
    """
Locate and return an object by its dotted path.

**Arguments:**

* ``path``

  / *Condition*: required / *Type*: str /

  The dotted path to locate.

**Returns:**

  / *Type*: Any /

  The located object, or None if not found.
    """
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

**Arguments:**

* ``value``

  / *Condition*: required / *Type*: str or type or None /

  The class to resolve. Can be a dotted path, a short name, or a type.

* ``base_cls``

  / *Condition*: required / *Type*: type /

  The base class that the resolved class must inherit from.

* ``registry``

  / *Condition*: optional / *Type*: dict[str, type] / *Default*: None /

  Optional registry mapping short names to classes.

* ``extra_modules``

  / *Condition*: optional / *Type*: list[str] / *Default*: None /

  List of module names to search for the class by short name.

* ``default``

  / *Condition*: optional / *Type*: type / *Default*: None /

  Default class to use if value is None.

**Returns:**

  / *Type*: type /

  The resolved class object inheriting from base_cls.
    """
    if isinstance(value, type):
        if base_cls is not None and not issubclass(value, base_cls):
            raise TypeError(f"{value!r} is not a subclass of {base_cls.__name__}")
        return value

    if value is None:
        if default is None:
            raise ValueError("No message class provided and no default specified.")
        return default

    if registry and value in registry:
        cls = registry[value]
        if base_cls is not None and not issubclass(cls, base_cls):
            raise TypeError(f"Registry entry '{value}' is not a subclass of {base_cls.__name__}")
        return cls

    # Try dotted path
    obj = _locate(value)
    if isinstance(obj, type) and (base_cls is None or issubclass(obj, base_cls)):
        return obj

    # Try short name inside extra modules
    if extra_modules:
        for mod in extra_modules:
            try:
                m = import_module(mod)
                if hasattr(m, value):
                    cls = getattr(m, value)
                    if isinstance(cls, type) and (base_cls is None or issubclass(cls, base_cls)):
                        return cls
            except Exception:  # pylint: disable=broad-except
                pass

    raise ValueError(
        f"Cannot resolve message class '{value}'. "
        "Use a full dotted path or register the short name."
    )

class GeneralCacheStartupPolicy(StartupPolicy):
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
        """
Initialize the GeneralCacheStartupPolicy.

**Arguments:**

* ``routing_keys``

  / *Condition*: optional / *Type*: str or Sequence[str] / *Default*: ("general")

  The routing keys to listen on for the general cache.

* ``message_cls``

  / *Condition*: optional / *Type*: str or type / *Default*: "BasicMessage"

  The message class to use for the general cache.

* ``only_for_alias``

  / *Condition*: optional / *Type*: str or None / *Default*: None

  If set, only enable the general cache if the client's alias matches this value.
        """
        self._routing_keys = routing_keys
        self._message_cls = message_cls
        self._only_for_alias = only_for_alias

    async def wait_until_ready(self, client: "EventBusClient") -> None:
        """
Enable the general cache listener on the client if applicable.

**Arguments:**

* ``client``

  / *Condition*: required / *Type*: EventBusClient /

  The EventBusClient instance to apply the policy on.
        """
        # If alias-constrained, skip when not matching
        if self._only_for_alias and getattr(client, "alias", None) != self._only_for_alias:
            return

        # Resolve message class string → actual type
        msg_cls = resolve_message_cls(
            self._message_cls,
            base_cls=None,
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


class ConfigureUnroutablePolicy(StartupPolicy):
    """
Configure unroutable behavior BEFORE exchange setup.
mode: "drop" | "alternate-exchange" | "return"
on_unroutable: "log" | "raise" | "cache" | "callback"
    """
    def __init__(self,
                 mode: str = "drop",
                 alternate_exchange: str | None = None,
                 on_unroutable: str = "log",
                 on_unroutable_callback: Optional[Any] = None) -> None:
        """
Initialize the ConfigureUnroutablePolicy.

**Arguments:**

* ``mode``

  / *Condition*: optional / *Type*: str / *Default*: "drop" /

  The unroutable message handling mode: "drop", "alternate-exchange", or "return".

* ``alternate_exchange``

  / *Condition*: optional / *Type*: str or None / *Default*: None /

  The name of the alternate exchange to use if mode is "alternate-exchange".

* ``on_unroutable``

  / *Condition*: optional / *Type*: str / *Default*: "log" /

  The action to take on unroutable messages: "log", "raise", "cache", or "callback".

* ``on_unroutable_callback``

  / *Condition*: optional / *Type*: Optional[Any] / *Default*: None /

  Optional callback function to invoke on unroutable messages if on_unroutable is "callback".
        """
        self.mode = mode
        self.alternate_exchange = alternate_exchange
        self.on_unroutable = on_unroutable
        self.on_unroutable_callback = on_unroutable_callback

    async def before_setup(self, bus: "EventBusClient") -> None:
        """
Configure unroutable message handling on the EventBusClient.

**Arguments:**

* ``bus``

  / *Condition*: required / *Type*: EventBusClient /

  The EventBusClient instance to configure.
        """
        bus.exchange_handler.configure_unroutable(
            policy=self.mode,
            alternate_exchange=self.alternate_exchange,
            on_unroutable=self.on_unroutable,
            unroutable_sink=getattr(bus, "_unroutable_cache", None),
            on_unroutable_callback=self.on_unroutable_callback,
        )

    async def wait_until_ready(self, bus: "EventBusClient") -> None:
        return


class PolicyChain(StartupPolicy):
    """
Apply multiple policies either sequentially or in parallel.

- mode="sequential": run in order; if fail_fast=True, stop on first exception.

- mode="parallel": run concurrently; if fail_fast=True, propagate first exception (gather(..., return_exceptions=False)).
    """
    def __init__(self, policies: list[StartupPolicy],
                 mode: str = "sequential",
                 fail_fast: bool = True) -> None:
        """
Initialize a PolicyChain to apply multiple startup policies.

**Arguments:**

* ``policies``

  / *Condition*: required / *Type*: list[StartupPolicy] /

  The list of startup policies to apply.

* ``mode``

  / *Condition*: optional / *Type*: str /

  The execution mode: "sequential" or "parallel".

* ``fail_fast``

   / *Condition*: optional / *Type*: bool /

   If True, stop on the first exception; otherwise, continue.
        """
        self.policies = list(policies)
        self.mode = mode
        self.fail_fast = fail_fast

    async def wait_until_ready(self, bus: "EventBusClient") -> None:
        """
Apply all policies according to the configured mode.

**Arguments:**

* ``bus``

  / *Condition*: required / *Type*: EventBusClient /

  The EventBusClient instance to apply the policies on.

**Returns:**

  / *Type*: None /

  None
        """
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

    async def before_setup(self, bus: "EventBusClient") -> None:
        if not self.policies: return
        if self.mode == "parallel":
            await asyncio.gather(*(p.before_setup(bus) for p in self.policies if _maybe_has(p, "before_setup")))
            return
        for p in self.policies:
            if _maybe_has(p, "before_setup"):
                await p.before_setup(bus)

    async def after_setup(self, bus: "EventBusClient") -> None:
        if not self.policies: return
        if self.mode == "parallel":
            await asyncio.gather(*(p.after_setup(bus) for p in self.policies if _maybe_has(p, "after_setup")))
            return
        for p in self.policies:
            if _maybe_has(p, "after_setup"):
                await p.after_setup(bus)

def build_policy_from_item(item: dict) -> StartupPolicy:
    """
Build a StartupPolicy from a configuration item.

**Arguments:**

* ``item``

  / *Condition*: required / *Type*: dict /

  The configuration item with keys:

  - "class": str - dotted path to the policy class

  - "args": dict - optional arguments for the policy class

  - "wrap": list - optional list of wrappers, each with "class" and "args"

**Returns:**

  / *Type*: StartupPolicy /

  The constructed StartupPolicy instance.
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
Build a StartupPolicy from a configuration dictionary.

**Arguments:**

* ``cfg``

  / *Condition*: required / *Type*: dict /

  The configuration dictionary. Supports either:

  - Legacy single policy:

      - "startup_policy": str - dotted path to the policy class

      - "startup_policy_args": dict - optional arguments for the policy class

  - New multi-policy:

      - "startup_policies": list - list of policy items (see build_policy_from_item)

      - "startup_policies_mode": str - optional mode ("sequential" or "parallel")

      - "startup_policies_fail_fast": bool - optional fail-fast flag (default True)

**Returns:**

  / *Type*: Optional[StartupPolicy] /

  The constructed StartupPolicy instance, or None if no policy is configured.
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