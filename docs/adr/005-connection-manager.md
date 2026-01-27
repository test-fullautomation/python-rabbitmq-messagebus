# ADR-005: Central ConnectionManager for Robust AMQP Lifecycle

## Status

Accepted

## Date

2025-07-12

## Author

Nguyen Huynh Tri Cuong (MS/EMC51)

## Reviewer

- Nguyen Huynh Tri Cuong (MS/EMC51)

## History

| Date | Version | Description |
|------|---------|-------------|
| 2025-07-12 | 1.0 | Initial version |
| 2025-08-15 | 1.1 | Added auto_reconnect and resource cleanup |

## Context

AMQP connections require careful lifecycle management:
- Connections can drop due to network issues or broker restarts
- Channels need to be recreated after connection recovery
- Multiple exchange handlers may share a single connection
- Resources (channels, queues) must be properly cleaned up

Without centralized management:
```python
# Scattered connection handling - error-prone
class Handler1:
    def __init__(self):
        self.connection = connect()  # Who closes this?

class Handler2:
    def __init__(self):
        self.connection = connect()  # Duplicate connection?
```

## Decision

Centralize all connection, channel, and reconnection management in a dedicated **ConnectionManager** class:

```python
class ConnectionManager:
    def __init__(self, auto_reconnect: bool = True):
        self._connection: AbstractRobustConnection = None
        self._channel: AbstractChannel = None
        self._exchange_handlers: list = []
        self._auto_reconnect = auto_reconnect

    async def connect(self, host, port, prefetch_count):
        """Establish connection and channel."""
        self._connection = await aio_pika.connect_robust(...)
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count)

    async def get_channel(self) -> AbstractChannel:
        """Get the shared channel for operations."""
        return self._channel

    def register_exchange_handler(self, handler):
        """Register handler for reconnection callbacks."""
        self._exchange_handlers.append(handler)

    async def close(self):
        """Close channel and connection, cleanup resources."""
        if self._channel:
            await self._channel.close()
        if self._connection:
            await self._connection.close()

    def is_connected(self) -> bool:
        """Check connection health."""
        return self._connection and not self._connection.is_closed
```

### Responsibilities

1. **Connection Establishment**: Single point for creating robust connections
2. **Channel Management**: Shared channel with proper QoS settings
3. **Auto-Reconnection**: Leverages aio-pika's robust connection
4. **Handler Registry**: Notifies exchange handlers on reconnection
5. **Resource Cleanup**: Ensures proper teardown on close

## Consequences

### Positive

- Single source of truth for connection state
- Consistent reconnection behavior
- Proper resource cleanup prevents leaks
- Exchange handlers don't manage connections

### Negative

- ConnectionManager becomes critical component
- Requires integration tests with broker restart scenarios
- Single channel may be bottleneck (mitigated by prefetch)

### Neutral

- All exchange handlers depend on ConnectionManager
- Connection events need to propagate to handlers

## Alternatives Considered

### 1. Per-Handler Connections (Rejected)

Each ExchangeHandler manages its own connection.

Rejected because:
- Resource waste (multiple connections)
- Inconsistent reconnection behavior
- Harder to coordinate shutdown

### 2. Global Connection Singleton (Rejected)

Single global connection shared via module-level variable.

Rejected because:
- Hard to test
- No support for multiple EventBusClient instances
- Implicit dependencies

## References

- [aio-pika Robust Connection](https://aio-pika.readthedocs.io/en/latest/quick-start.html#robust-connection)
- [AMQP Connection Model](https://www.rabbitmq.com/connections.html)
- Source: `EventBusClient/connection.py`
