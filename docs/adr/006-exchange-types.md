# ADR-006: Multiple Exchange Types via Dedicated Handlers

## Status

Accepted

## Date

2025-07-15

## Author

Nguyen Huynh Tri Cuong (MS/EMC51)

## Reviewer

- Nguyen Huynh Tri Cuong (MS/EMC51)

## History

| Date | Version | Description |
|------|---------|-------------|
| 2025-07-15 | 1.0 | Initial version |
| 2025-07-17 | 1.1 | Added XRTopicExchangeHandler |

## Context

RabbitMQ supports multiple exchange types with different routing semantics:

| Exchange Type | Routing Behavior | Use Case |
|--------------|------------------|----------|
| **topic** | Pattern matching on routing key | Selective routing (e.g., `sensor.*.temperature`) |
| **fanout** | Broadcast to all bound queues | Notifications, events |
| **direct** | Exact routing key match | Point-to-point |
| **x-rtopic** | Reverse topic matching (plugin) | Flexible subscriptions |

Different projects need different exchange types. A generic handler would require complex conditional logic.

## Decision

Provide separate **ExchangeHandler** implementations for each exchange type:

### Abstract Base Class

```python
class ExchangeHandler(ABC):
    @property
    @abstractmethod
    def exchange_type(self) -> str: ...

    @abstractmethod
    async def setup(self, connection_manager): ...

    @abstractmethod
    async def publish(self, message, routing_key, headers): ...

    @abstractmethod
    async def subscribe(self, routing_key, message_cls, callback): ...

    async def teardown(self): ...
    def configure_unroutable(self, policy, ...): ...
```

### Concrete Implementations

1. **TopicExchangeHandler** (`exchange_type = "topic"`)
   - Pattern-based routing with `*` and `#` wildcards
   - Most common for IPC scenarios

2. **FanoutExchangeHandler** (`exchange_type = "fanout"`)
   - Ignores routing key, broadcasts to all
   - Used for system-wide notifications

3. **XRTopicExchangeHandler** (`exchange_type = "x-rtopic"`)
   - Reverse topic matching (requires broker plugin)
   - Publisher specifies pattern, subscriber specifies exact key

### Selection via Configuration

```json
{
    "exchange_handler": "TopicExchangeHandler",
    "exchange_name": "my_exchange"
}
```

Or programmatically:
```python
from EventBusClient.exchange_handler import TopicExchangeHandler

handler = TopicExchangeHandler(name="my_exchange", serializer=JsonSerializer())
client = EventBusClient(exchange_handler=handler, ...)
```

## Consequences

### Positive

- Clear separation of concerns per exchange type
- Each handler optimized for its semantics
- Easy to add new exchange types
- Type-safe handler selection

### Negative

- Multiple classes to maintain
- Documentation must clarify when to use each type
- x-rtopic requires broker plugin installation

### Neutral

- Test coverage needed for each handler
- Handler selection happens at configuration time

## Alternatives Considered

### 1. Single Generic Handler with Type Parameter (Rejected)

One ExchangeHandler class with exchange_type as constructor parameter.

Rejected because:
- Different exchange types have different publish/subscribe semantics
- Would require conditional logic throughout
- Less type safety

### 2. Mixin-based Composition (Deferred)

Use mixins for shared behavior (e.g., UnroutableMixin).

Deferred because:
- Current inheritance is sufficient
- May add if handler complexity grows

## References

- [RabbitMQ Exchange Types](https://www.rabbitmq.com/tutorials/amqp-concepts.html#exchanges)
- [x-rtopic Plugin](https://github.com/rabbitmq/rabbitmq-rtopic-exchange)
- Source: `EventBusClient/exchange_handler/base.py`
- Source: `EventBusClient/exchange_handler/topic_handler.py`
- Source: `EventBusClient/exchange_handler/fanout_handler.py`
- Source: `EventBusClient/exchange_handler/x_rtopic_handler.py`
