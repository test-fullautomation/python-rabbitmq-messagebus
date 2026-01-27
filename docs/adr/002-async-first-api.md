# ADR-002: Async-First Public API with Sync Wrappers

## Status

Accepted

## Date

2025-07-05

## Author

Nguyen Huynh Tri Cuong (MS/EMC51)

## Reviewer

- Nguyen Huynh Tri Cuong (MS/EMC51)

## History

| Date | Version | Description |
|------|---------|-------------|
| 2025-07-05 | 1.0 | Initial version |

## Context

EventBusClient operations are IO-bound and event-driven:
- Connect/reconnect and channel operations
- Consume loops and callback dispatch
- Startup coordination (rendezvous)

The library is used in multi-process systems, and within a single process it can run multiple subscribers concurrently. The underlying aio-pika library is async-native.

However, some existing codebases are synchronous (Robot Framework keywords, legacy scripts) and cannot easily adopt async/await patterns.

```python
# Async code (modern)
async def main():
    client = await EventBusClient.from_config("config.jsonp")
    await client.connect("localhost", 5672)
    await client.send("topic", message)

# Sync code (legacy) - needs support too
def legacy_function():
    client = EventBusClient.from_config_sync("config.jsonp")
    client.connect_sync("localhost", 5672)
    client.send_sync("topic", message)
```

## Decision

Expose an **async-first** public API for core operations and implement internal components in async style:

### Async API (Primary)
```python
await client.connect(host, port, prefetch_count)
await client.send(routing_key, message, headers)
cache = await client.on(routing_key, message_cls, callback)
await client.off(routing_key, callback)
await client.close()
```

### Sync Wrappers (Secondary)
```python
client.connect_sync(host, port, prefetch_count)
client.send_sync(routing_key, message, headers)
cache = client.on_sync(routing_key, message_cls, callback)
client.off_sync(routing_key, callback)
client.close_sync()
```

### Implementation Strategy
- Sync wrappers run async operations in a managed event loop
- Use `asyncio.run_coroutine_threadsafe()` for thread-safe publish
- SubscriptionCache provides blocking `get()` for sync consumers

## Consequences

### Positive

- Aligns with AMQP IO model and aio-pika library
- Enables concurrent subscribers without thread overhead
- Supports both modern async and legacy sync callers
- Clean separation between async core and sync convenience layer

### Negative

- Sync wrappers must remain thin and well-tested
- Potential complexity in event loop management
- Two API surfaces to document and maintain

### Neutral

- Documentation must explain when to use async vs sync
- Tests should cover both API surfaces

## Alternatives Considered

### 1. Sync-Only API (Rejected)

Implement everything synchronously with blocking calls.

Rejected because:
- Blocking behavior doesn't match AMQP's event-driven nature
- Would require thread workarounds for concurrency
- Mismatch with underlying aio-pika async client

### 2. Async-Only API (Rejected)

Only provide async API, require all callers to use async/await.

Rejected because:
- High adoption friction for synchronous environments
- Robot Framework and legacy scripts would need significant refactoring
- Some test environments don't support async easily

## References

- [Python asyncio Documentation](https://docs.python.org/3/library/asyncio.html)
- [aio-pika Library](https://aio-pika.readthedocs.io/)
- Source: `EventBusClient/event_bus_client.py`
