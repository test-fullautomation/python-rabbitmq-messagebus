# ADR-001: Standardize IPC / Message Bus API Across Projects

## Status

Accepted

## Date

2025-07-01

## Author

Nguyen Huynh Tri Cuong (MS/EMC51)

## Reviewer

- Nguyen Huynh Tri Cuong (MS/EMC51)

## History

| Date | Version | Description |
|------|---------|-------------|
| 2025-07-01 | 1.0 | Initial version |

## Context

Multiple internal projects required Inter-Process Communication (IPC) between processes inside the test framework. RabbitMQ was adopted as the message broker, but each project created its own wrapper implementation:

- Inconsistent API surface and semantics across projects
- Duplicated bug fixes applied independently in each project
- Poor maintainability and troubleshooting due to fragmentation
- No standardized patterns for common operations (publish/subscribe, connection management)

Example of fragmented implementations:
```python
# Project A
client_a.publish("topic", data)

# Project B
bus_b.send_message("topic", payload, headers={})

# Project C
mq_c.emit("topic", message_obj)
```

## Decision

Create and maintain a shared library (**EventBusClient**) that provides:

1. **Minimal, consistent publish/subscribe API**
   - `send(routing_key, message)` for publishing
   - `on(routing_key, message_cls, callback)` for subscribing
   - `off(routing_key, callback)` for unsubscribing

2. **Robust connection and lifecycle management**
   - Centralized ConnectionManager with auto-reconnect
   - Proper resource cleanup on close

3. **Configuration-driven plugin selection**
   - Support for different serializers (Pickle, JSON, Protobuf)
   - Support for different exchange types (Topic, Fanout, XRTopic)
   - Extensible message types

4. **Dual API support**
   - Async API for modern async/await code
   - Sync wrappers for legacy synchronous callers

## Consequences

### Positive

- Single source of truth for IPC implementation
- Consistent API across all projects
- Bug fixes applied once, benefit all projects
- Easier onboarding for new developers
- Centralized documentation and testing

### Negative

- Library versioning and compatibility become important
- Breaking changes require coordination across projects
- Additional governance overhead for plugin management

### Neutral

- Projects must migrate from custom implementations
- Need to establish contribution guidelines

## Alternatives Considered

### 1. Keep Per-Project Wrappers (Rejected)

Each project maintains its own RabbitMQ wrapper.

Rejected because:
- Long-term maintenance cost multiplied by number of projects
- Inconsistent behavior leads to integration issues
- Knowledge silos per project

### 2. Use Other IPC Technologies (Rejected)

Consider alternatives like gRPC, ZeroMQ, or multiprocessing pipes/shared memory.

Rejected because:
- Higher migration cost from existing RabbitMQ infrastructure
- RabbitMQ already operationally available and understood
- Routing patterns (topic, fanout) are valuable for our use cases
- Existing tooling and monitoring for RabbitMQ

## References

- [RabbitMQ Documentation](https://www.rabbitmq.com/documentation.html)
- [aio-pika Library](https://aio-pika.readthedocs.io/)
- Source: `EventBusClient/event_bus_client.py`
