# Diagrams

This folder contains architecture diagrams, sequence diagrams, and other visual documentation for the EventBusClient project.

## Diagram Index

| File | Type | Description |
|------|------|-------------|
| [overview.puml](overview.puml) | System Overview | High-level system context |
| [architecture.puml](architecture.puml) | Architecture | Package and dependency structure |
| [component.puml](component.puml) | Component | Component ports and interfaces |
| [class.puml](class.puml) | Class | Class relationships and methods |
| [sequence-publish.puml](sequence-publish.puml) | Sequence | Message publish flow |
| [sequence-subscribe.puml](sequence-subscribe.puml) | Sequence | Subscribe and receive flow |
| [sequence-connection.puml](sequence-connection.puml) | Sequence | Connection lifecycle |
| [sequence-rendezvous.puml](sequence-rendezvous.puml) | Sequence | Multi-client coordination |
| [sequence-unroutable.puml](sequence-unroutable.puml) | Sequence | Unroutable message handling |
| [sequence-lifecycle.puml](sequence-lifecycle.puml) | Sequence | Full end-to-end lifecycle |

## Viewing PlantUML Diagrams

### VS Code

Install the **PlantUML** extension:
1. Install extension: `jebbs.plantuml`
2. Open `.puml` file
3. Press `Alt+D` to preview

### Online

Use the PlantUML online server:
- https://www.plantuml.com/plantuml/uml/

### Command Line

```bash
# Install PlantUML
# macOS
brew install plantuml

# Ubuntu/Debian
sudo apt install plantuml

# Generate PNG
plantuml diagram.puml

# Generate SVG
plantuml -tsvg diagram.puml

# Generate all diagrams
plantuml *.puml
```

### IntelliJ IDEA / PyCharm

Install the **PlantUML Integration** plugin from the marketplace.

## Diagram Descriptions

### overview.puml
High-level view highlighting the **pluggable strategy pattern** of the library:
- Public APIs: Async, Sync, Factory, and Rendezvous APIs
- Core: EventBusClient, ConnectionManager, Rendezvous
- Plugin System: PluginLoader with extensible interfaces
- Extensible Interfaces: ExchangeHandler, Serializer, BaseMessage, StartupPolicy
- Built-in Plugins: Topic/XRTopic/Fanout handlers, JSON/Pickle/Protobuf serializers, etc.
- Custom Plugins: Shows how users can extend each interface

### architecture.puml
Package diagram showing all components organized by responsibility:
- Core: EventBusClient, ConnectionManager, Rendezvous
- Exchange Handlers: Topic, XRTopic, Fanout
- Messaging: Publisher, Subscriber, Cache
- Serialization: Pickle, JSON, Protobuf serializers
- Messages: BaseMessage, BasicMessage, ControlMessage, DictMessage
- Startup Policies: NoWait, FixedDelay, HandshakeBarrier, PolicyChain, etc.
- Plugin/Loader: PluginLoader, ConfigValidator
- Utilities: QLogger, Utils, WaitMode

### component.puml
Component diagram with ports showing the interfaces:
- EventBusClient facade methods
- ConnectionManager connection handling
- ExchangeHandler publish/subscribe operations
- SubscriptionCache synchronous access methods
- PluginLoader dynamic loading
- StartupPolicy lifecycle hooks
- QLogger and Utils utilities

### class.puml
Full class diagram showing:
- All classes with attributes and methods
- Inheritance relationships (ExchangeHandler, Serializer, BaseMessage, StartupPolicy)
- Composition and aggregation
- Dependencies between components
- PluginLoader and ConfigValidator
- QLogger singleton and Utils static methods
- All startup policy implementations

### sequence-publish.puml
Sequence diagram for publishing messages:
- Async publish flow
- Sync publish wrapper
- Serialization step
- RabbitMQ interaction

### sequence-subscribe.puml
Sequence diagram for subscribing and receiving:
- Subscription setup (queue declaration, binding)
- Message receive callback flow
- SubscriptionCache population
- Sync receive using cache

### sequence-connection.puml
Sequence diagram for connection lifecycle:
- Connect with startup policies
- Exchange setup
- Graceful close with teardown

### sequence-rendezvous.puml
Sequence diagram for multi-client coordination:
- Workers announcing ready
- Coordinator waiting for workers
- Bidirectional synchronization

### sequence-unroutable.puml
Sequence diagram for unroutable message handling:
- Publishing with mandatory flag
- RabbitMQ basic.return callback
- Different handling strategies (log, cache, callback, raise)
- Pop unroutables from cache

### sequence-lifecycle.puml
Complete end-to-end sequence diagram showing:
- Configuration phase with PluginLoader
- Connection establishment
- Subscription setup
- Message publishing and delivery
- Cleanup and close

## PlantUML Reference

- [PlantUML Guide](https://plantuml.com/guide)
- [Sequence Diagrams](https://plantuml.com/sequence-diagram)
- [Class Diagrams](https://plantuml.com/class-diagram)
- [Component Diagrams](https://plantuml.com/component-diagram)
