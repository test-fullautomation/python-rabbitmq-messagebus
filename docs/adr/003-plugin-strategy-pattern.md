# ADR-003: Plugin-based Strategy Pattern

## Status

Accepted

## Date

2025-07-10

## Author

Nguyen Huynh Tri Cuong (MS/EMC51)

## Reviewer

- Nguyen Huynh Tri Cuong (MS/EMC51)

## History

| Date | Version | Description |
|------|---------|-------------|
| 2025-07-10 | 1.0 | Initial version |
| 2025-07-17 | 1.1 | Added StartupPolicy to extensible interfaces |

## Context

Different projects have varying requirements for:
- **Serialization**: Some need Pickle for Python objects, others need JSON for interoperability, some need Protobuf for performance
- **Exchange Types**: Some use Topic exchanges for routing patterns, others need Fanout for broadcast, some require x-rtopic plugin
- **Message Types**: Each domain has its own message structures and validation rules
- **Startup Behavior**: Different coordination patterns (rendezvous, delays, configuration)

Hardcoding these choices would require forking the library for each project or adding complex conditional logic.

```python
# Without plugin system - inflexible
if project == "A":
    serializer = PickleSerializer()
elif project == "B":
    serializer = JsonSerializer()
# ... grows unbounded
```

## Decision

Use **Strategy Pattern** combined with **dynamic discovery** via PluginLoader:

### Extensible Interfaces

1. **ExchangeHandler** - Strategy for exchange types
   - TopicExchangeHandler
   - FanoutExchangeHandler
   - XRTopicExchangeHandler
   - Custom implementations

2. **Serializer** - Strategy for serialization
   - PickleSerializer
   - JsonSerializer
   - ProtobufSerializer
   - Custom implementations

3. **BaseMessage** - Base class for message types
   - BasicMessage
   - ControlMessage
   - DictMessage
   - Custom domain messages

4. **StartupPolicy** - Strategy for startup behavior
   - NoWait
   - FixedDelay
   - HandshakeBarrier
   - PolicyChain
   - Custom policies

### PluginLoader

Dynamically discovers and registers implementations:

```python
class PluginLoader:
    def __init__(self, base_path=None):
        self.serializer_dict: Dict[str, Type[Serializer]] = {}
        self.exchange_handler_dict: Dict[str, Type[ExchangeHandler]] = {}
        self.message_dict: Dict[str, Type[BaseMessage]] = {}
        self._load_all_modules()
        self._register_classes()

    def get_serializer(self, name: str) -> Type[Serializer]
    def get_exchange_handler(self, name: str) -> Type[ExchangeHandler]
    def get_message(self, name: str) -> Type[BaseMessage]
```

### Configuration-Driven Selection

```json
{
    "serializer": "JsonSerializer",
    "exchange_handler": "TopicExchangeHandler",
    "plugins_path": "./custom_plugins"
}
```

## Consequences

### Positive

- Supports cross-project variability without forking core code
- New plugins can be added without modifying library
- Configuration-driven selection simplifies deployment
- Clear extension points for customization

### Negative

- Requires extension guidelines and documentation
- Plugin contract tests needed to ensure compatibility
- Runtime discovery adds startup complexity
- Type safety reduced compared to static imports

### Neutral

- Plugin governance required to maintain quality
- Version compatibility between plugins and core library

## Alternatives Considered

### 1. Subclassing EventBusClient (Rejected)

Each project subclasses EventBusClient to customize behavior.

Rejected because:
- Leads to fragmented implementations
- Difficult to compose multiple customizations
- Breaks encapsulation

### 2. Configuration Flags (Rejected)

Use extensive configuration flags to control behavior.

Rejected because:
- Combinatorial explosion of options
- Hard to add new behaviors
- Complex conditional logic in core

### 3. Dependency Injection Framework (Deferred)

Use a full DI framework like dependency-injector.

Deferred because:
- Additional dependency
- Overkill for current requirements
- May reconsider if complexity grows

## References

- [Strategy Pattern](https://refactoring.guru/design-patterns/strategy)
- [Plugin Architecture](https://python-patterns.guide/gang-of-four/composition-over-inheritance/)
- Source: `EventBusClient/plugin_loader.py`
- Source: `EventBusClient/serializer/base_serializer.py`
- Source: `EventBusClient/exchange_handler/base.py`
