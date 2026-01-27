# ADR-007: StartupPolicy and Rendezvous for Coordinated Start

## Status

Accepted

## Date

2025-07-20

## Author

Nguyen Huynh Tri Cuong (MS/EMC51)

## Reviewer

- Nguyen Huynh Tri Cuong (MS/EMC51)

## History

| Date | Version | Description |
|------|---------|-------------|
| 2025-07-20 | 1.0 | Initial version |
| 2025-08-12 | 1.1 | Added PolicyChain and ConfigureUnroutablePolicy |

## Context

In multi-process test frameworks, processes often need to coordinate their startup:

- **Workers** should not start processing until the **Coordinator** is ready
- **Coordinator** should wait for a minimum number of **Workers** to be available
- Some processes need a fixed delay before starting
- Configuration (like unroutable policy) should be applied before exchange setup

Without coordination:
```
Worker1: starts, subscribes, waits for messages
Worker2: starts, subscribes, waits for messages
Coordinator: starts, publishes "begin" message
Problem: Message sent before workers subscribed = lost!
```

## Decision

Provide composable **StartupPolicy** implementations and a **Rendezvous** mechanism:

### StartupPolicy Protocol

```python
class StartupPolicy(Protocol):
    async def wait_until_ready(self, bus: EventBusClient) -> None: ...

    # Optional hooks
    async def before_setup(self, bus: EventBusClient) -> None: ...
    async def after_setup(self, bus: EventBusClient) -> None: ...
```

### Built-in Policies

1. **NoWait** - No delay, start immediately
2. **FixedDelay** - Wait N seconds before proceeding
3. **HandshakeBarrier** - Wait for N processes with specific roles
4. **GeneralCacheStartupPolicy** - Enable general cache on connect
5. **ConfigureUnroutablePolicy** - Configure unroutable handling before setup
6. **PolicyChain** - Compose multiple policies (sequential or parallel)
7. **PanelControlLegacyByAlias** - Legacy panel control mode

### PolicyChain for Composition

```python
policy = PolicyChain([
    ConfigureUnroutablePolicy(mode="return", on_unroutable="cache"),
    GeneralCacheStartupPolicy(routing_keys="general.*"),
    HandshakeBarrier({"worker": 2}, timeout=60)
], mode="sequential")
```

### Rendezvous Mechanism

```python
class Rendezvous:
    async def announce_ready(self, roles: list[str]) -> None:
        """Announce this process is ready with given roles."""

    async def wait_for(self, requirements: dict[str, int], timeout: float) -> bool:
        """Wait until required number of processes announce each role."""
```

### Usage Example

```python
# Worker process
client = await EventBusClient.from_config("config.jsonp")
await client.connect("localhost", 5672)
await client.announce_ready(["worker"])
await client.wait_until_ready({"coordinator": 1}, timeout=60)
# Now safe to start processing

# Coordinator process
client = await EventBusClient.from_config("config.jsonp")
await client.connect("localhost", 5672)
await client.wait_until_ready({"worker": 2}, timeout=60)
await client.announce_ready(["coordinator"])
# Now safe to send messages
```

## Consequences

### Positive

- Reliable multi-process coordination
- Composable policies for flexibility
- Prevents message loss from race conditions
- Configuration applied at correct lifecycle phase

### Negative

- Policies must be documented for correct usage
- Timeout handling adds complexity
- Rendezvous requires message exchange overhead

### Neutral

- Affects startup time based on policy choice
- Requires understanding of distributed coordination

## Alternatives Considered

### 1. External Coordination Service (Rejected)

Use external service like Redis or ZooKeeper for coordination.

Rejected because:
- Additional infrastructure dependency
- RabbitMQ already available for messaging
- Simpler to use same message bus

### 2. Fixed Sleep Delays (Rejected)

Just use `time.sleep(N)` to wait for other processes.

Rejected because:
- Unreliable timing
- Either too short (race) or too long (wasted time)
- Doesn't adapt to actual system state

## References

- [Barrier Synchronization Pattern](https://en.wikipedia.org/wiki/Barrier_(computer_science))
- [Rendezvous Pattern](https://en.wikipedia.org/wiki/Rendezvous_(Plan_9))
- Source: `EventBusClient/rendezvous.py`
- Source: `EventBusClient/startup_policy.py`
