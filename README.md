# EventBusClient - RabbitMQ Message Bus Library

[![License: Apache v2](https://img.shields.io/pypi/l/robotframework.svg)](http://www.apache.org/licenses/LICENSE-2.0.html)

EventBusClient is an event-driven messaging library for Python, designed to simplify distributed communication using RabbitMQ as the message broker. It provides a clean, pluggable architecture for robust inter-process messaging, topic management, and coordination in scalable applications.

## Why EventBusClient?

### The Problem

Building distributed systems with message queues typically involves:
- Writing boilerplate code for connection management, serialization, and error handling
- Implementing retry logic, reconnection, and graceful shutdown
- Coordinating startup order across multiple processes
- Handling different environments (dev, test, production) with different configurations
- Supporting both async and sync codebases

### The Solution

EventBusClient abstracts away the complexity of RabbitMQ while remaining flexible:

| Challenge | EventBusClient Solution |
|-----------|------------------------|
| Boilerplate code | Clean `send()` / `on()` API with automatic setup |
| Connection management | Auto-reconnection, robust lifecycle handling |
| Multi-process coordination | Built-in Rendezvous pattern for startup synchronization |
| Environment configuration | JSONP config files with environment variable support |
| Async vs Sync | Async-first API with sync wrappers for legacy code |
| Extensibility | Pluggable serializers, exchange handlers, and policies |

## When to Use EventBusClient

**Ideal for:**

- **Test Automation Systems** - Coordinate multiple test runners, controllers, and reporters
- **Multi-Process Applications** - Decouple processes that need to communicate asynchronously
- **Microservices** - Event-driven communication between services
- **Data Pipelines** - Stream data between producers and consumers
- **Distributed Systems** - Any system requiring reliable message passing

**Consider alternatives if:**

- You need simple in-process pub/sub (use Python's built-in `queue` module)
- You're building a single monolithic application with no IPC needs
- You need guaranteed exactly-once delivery (RabbitMQ provides at-least-once)

## Key Features

- **Async-First API** - Native async/await support with sync wrappers for legacy code
- **Pluggable Architecture** - Extensible serializers, exchange handlers, message types, and startup policies
- **Configuration-Driven** - JSONP-based configuration with environment variable support
- **Multiple Exchange Types** - Topic, Fanout, and X-RTopic exchange handlers
- **Coordinated Startup** - Rendezvous pattern for multi-process synchronization
- **Unroutable Message Handling** - Configurable policies (drop, return, alternate-exchange)
- **Thread-Safe Operations** - Safe publishing from multiple threads
- **Auto-Reconnection** - Robust connection management with automatic recovery

## Table of Contents

- [Getting Started](#getting-started)
- [Real-World Scenarios](#real-world-scenarios)
- [Main APIs](#main-apis)
- [Configuration Reference](#configuration-reference)
- [Architecture](#architecture)
- [Examples](#examples)
- [Documentation](#documentation)
- [Feedback](#feedback)
- [License](#license)

## Getting Started

### Installation

```bash
pip install eventbusclient
```

### Prerequisites

- Python 3.8+
- RabbitMQ server running (default: localhost:5672)

### Quick Start

**1. Create a configuration file (`config.jsonp`):**

```jsonp
{
  "host": "localhost",
  "port": 5672,
  "serializer": "JsonSerializer",
  "exchange_handler": "TopicExchangeHandler",
  "auto_reconnect": true
}
```

**2. Create a producer:**

```python
import asyncio
from EventBusClient import EventBusClient
from EventBusClient.message.base_message import BaseMessage

class MyMessage(BaseMessage):
    def __init__(self, content=None):
        self.content = content

async def main():
    client = await EventBusClient.from_config("config.jsonp")
    await client.send("my.topic", MyMessage("Hello, World!"))
    await client.close()

asyncio.run(main())
```

**3. Create a consumer:**

```python
import asyncio
from EventBusClient import EventBusClient

async def main():
    client = await EventBusClient.from_config("config.jsonp")

    async def handler(message, headers):
        print(f"Received: {message.content}")

    await client.on("my.topic", MyMessage, handler)
    await asyncio.sleep(60)  # Keep listening
    await client.close()

asyncio.run(main())
```

## Real-World Scenarios

### 1. Test Automation Framework

Coordinate multiple test processes (Robot Framework, pytest) with a central controller:

```python
# Controller process
client = await EventBusClient.from_config("config.jsonp")
await client.wait_until_ready({"worker": 3}, timeout=30)  # Wait for 3 workers
await client.send("test.start", StartTestMessage(suite="regression"))

# Worker process
client = await EventBusClient.from_config("config.jsonp")
await client.announce_ready(["worker"])
await client.on("test.start", StartTestMessage, run_tests)
```

### 2. Microservices Communication

Decouple services with topic-based messaging:

```python
# Order Service - publishes order events
await client.send("orders.created", OrderCreatedMessage(order_id=123))
await client.send("orders.shipped", OrderShippedMessage(order_id=123))

# Notification Service - subscribes to order events
await client.on("orders.*", OrderMessage, send_notification)

# Inventory Service - subscribes to specific events
await client.on("orders.created", OrderCreatedMessage, update_inventory)
```

### 3. Sensor Data Pipeline

Stream sensor data from multiple sources:

```python
# Sensor Publisher
while True:
    reading = sensor.read()
    await client.send(f"sensor.{sensor_id}.temperature", SensorMessage(reading))
    await asyncio.sleep(1)

# Data Aggregator - subscribes to all sensors
await client.on("sensor.*.temperature", SensorMessage, aggregate_data)
```

### 4. Request-Reply Pattern (RPC)

Implement synchronous-style RPC over async messaging:

```python
# Server
async def handle_request(request, headers):
    result = process(request)
    reply_to = headers.get("reply_to")
    correlation_id = headers.get("correlation_id")
    await client.send(reply_to, ResultMessage(result),
                      headers={"correlation_id": correlation_id})

await client.on("rpc.requests", RequestMessage, handle_request)

# Client
reply_queue = f"rpc.replies.{uuid4()}"
cache = await client.on(reply_queue, ResultMessage, lambda m, h: None)
await client.send("rpc.requests", request,
                  headers={"reply_to": reply_queue, "correlation_id": "123"})
result = cache.wait_for_one(lambda m, h: h.get("correlation_id") == "123", timeout=10)
```

## Main APIs

### Async API (Primary)

```python
# Factory methods
client = await EventBusClient.from_config(config_path)

# Connection
await client.connect(host, port, prefetch_count=10)
await client.close()
is_connected = client.is_connected()

# Publish/Subscribe
await client.send(routing_key, message, headers=None)
cache = await client.on(routing_key, message_cls, callback)
await client.off(routing_key, callback)

# Coordination (Rendezvous)
await client.announce_ready(roles=["worker"])
success = await client.wait_until_ready(requirements={"worker": 2}, timeout=30)

# Unroutable messages
unroutables = client.pop_unroutables()
```

### Sync API (Legacy Support)

```python
# Factory methods
client = EventBusClient.from_config_sync(config_path)

# Connection
client.connect_sync(host, port, prefetch_count=10)
client.close_sync()

# Publish/Subscribe
client.send_sync(routing_key, message, headers=None)
cache = client.on_sync(routing_key, message_cls, callback)
client.off_sync(routing_key, callback)
```

### SubscriptionCache API

```python
# Get messages from cache
message = cache.get(timeout=5.0)           # Block until message or timeout
message = cache.pop(timeout=5.0)           # Get and remove
message = cache.peek(timeout=5.0)          # Get without removing

# Wait for specific messages
found = cache.wait_for_one(target_msg, timeout=10)
indices = cache.wait_for_many(
    targets=[msg1, msg2, msg3],
    mode=WaitMode.ALL_IN_GIVEN_ORDER,      # or ALL_IN_RANDOM_ORDER, ANY_OF_GIVEN_MSGS
    timeout=30
)

# Drain all messages
messages = cache.drain(max_items=100)
```

## Configuration Reference

Create a configuration file (`config.jsonp`) based on the template at `EventBusClient/config/config.jsonp.template`:

```jsonp
{
  // ============== Connection Settings ==============
  // RabbitMQ server hostname or IP address
  "host": "localhost",

  // RabbitMQ server port (default: 5672)
  "port": 5672,

  // Automatically reconnect if connection is lost
  "auto_reconnect": true,

  // Number of messages to prefetch (QoS)
  "qos_prefetch": 10,

  // ============== Plugin Selection ==============
  // Serializer: "PickleSerializer", "JsonSerializer", "ProtobufSerializer"
  "serializer": "PickleSerializer",

  // Exchange handler: "TopicExchangeHandler", "FanoutExchangeHandler", "XRTopicExchangeHandler"
  "exchange_handler": "TopicExchangeHandler",

  // Custom exchange name (optional)
  "exchange_name": "my_exchange",

  // Path to custom plugins directory
  "plugins_path": "./plugins",

  // ============== General Cache Settings ==============
  // Cache policy: "off", "on_connect", "on_demand"
  "general_cache_policy": "off",

  // Routing keys for general cache
  "general_routing_keys": "general.*",

  // Message class for general cache
  "general_message_cls": "BaseMessage",

  // ============== Logging Settings ==============
  // Logger instance name
  "logger_name": "event_bus_client",

  // Log file path (use "console" for stdout, or path like "./logs/app.log")
  "logfile": "console",

  // Log level: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
  "loglevel": "INFO",

  // Log file mode: "w" (overwrite) or "a" (append)
  "logger_mode": "a"
}
```

### Configuration Options Table

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `host` | str | No | "localhost" | RabbitMQ server hostname |
| `port` | int | No | 5672 | RabbitMQ server port |
| `serializer` | str | **Yes** | - | Serializer class name |
| `exchange_handler` | str | **Yes** | - | Exchange handler class name |
| `exchange_name` | str | No | auto | Custom exchange name |
| `auto_reconnect` | bool | No | true | Enable auto-reconnection |
| `qos_prefetch` | int | No | 10 | Prefetch count for QoS |
| `plugins_path` | str | No | "./plugins" | Custom plugins directory |
| `general_cache_policy` | str | No | "off" | General cache policy |
| `general_routing_keys` | str | No | "general" | Routing keys for cache |
| `general_message_cls` | str | No | "BaseMessage" | Message class for cache |
| `logger_name` | str | No | "event_bus_client" | Logger name |
| `logfile` | str | No | None | Log file path |
| `loglevel` | str | No | "INFO" | Log level |
| `logger_mode` | str | No | "a" | Log file mode |

### JSONP Features

The configuration uses [JsonPreprocessor](https://github.com/test-fullautomation/python-jsonpreprocessor) which supports:

```jsonp
{
  // Environment variable substitution
  "host": "${RABBITMQ_HOST}",
  "port": ${RABBITMQ_PORT:-5672},      // With default value

  // Include other files
  ${include: "./env/${ENVIRONMENT}.jsonp"}
}
```

## Architecture

EventBusClient follows a **pluggable strategy pattern** with four extensible interfaces:

```
+------------------+     +-------------------+
|   User App       |---->|  Public APIs      |
+------------------+     | - Async API       |
                         | - Sync API        |
                         | - Factory API     |
                         | - Rendezvous API  |
                         +--------+----------+
                                  |
                         +--------v----------+
                         |  EventBusClient   |
                         |  (Core)           |
                         +--------+----------+
                                  |
              +-------------------+-------------------+
              |                   |                   |
    +---------v-------+  +--------v--------+  +------v--------+
    | ExchangeHandler |  |   Serializer    |  | StartupPolicy |
    | (Interface)     |  |   (Interface)   |  | (Interface)   |
    +-----------------+  +-----------------+  +---------------+
    | TopicExchange   |  | PickleSerializer|  | NoWait        |
    | FanoutExchange  |  | JsonSerializer  |  | FixedDelay    |
    | XRTopicExchange |  | ProtobufSerial. |  | HandshakeBar. |
    | [Your Handler]  |  | [Your Serial.]  |  | PolicyChain   |
    +-----------------+  +-----------------+  +---------------+
```

### Key Components

| Component | Description |
|-----------|-------------|
| **EventBusClient** | Main facade providing async/sync APIs |
| **ConnectionManager** | Manages AMQP connection lifecycle |
| **ExchangeHandler** | Handles exchange declaration, publish, subscribe |
| **AsyncPublisher** | Publishes messages to exchange |
| **AsyncSubscriber** | Consumes messages from queues |
| **SubscriptionCache** | Thread-safe buffer for sync consumers |
| **PluginLoader** | Dynamically loads plugins from config |
| **Rendezvous** | Coordinates multi-process startup |

## Examples

The `EventBusClient/examples/` folder contains comprehensive examples:

| Example | Description |
|---------|-------------|
| [basic_sample.py](EventBusClient/examples/basic_sample.py) | Basic publish/subscribe |
| [sync_sample.py](EventBusClient/examples/sync_sample.py) | Synchronous API usage |
| [wait_mode_sample.py](EventBusClient/examples/wait_mode_sample.py) | WaitMode options |
| [rendezvous_sample.py](EventBusClient/examples/rendezvous_sample.py) | Multi-process coordination |
| [request_reply_sample.py](EventBusClient/examples/request_reply_sample.py) | RPC pattern |
| [multiple_subscriptions_sample.py](EventBusClient/examples/multiple_subscriptions_sample.py) | Multiple topics |
| [custom_message_sample.py](EventBusClient/examples/custom_message_sample.py) | Custom message types |
| [error_handling_sample.py](EventBusClient/examples/error_handling_sample.py) | Error handling patterns |
| [alternate_exchange_sample.py](EventBusClient/examples/alternate_exchange_sample.py) | Unroutable handling |

See [EventBusClient/examples/README.md](EventBusClient/examples/README.md) for detailed documentation.

## Documentation

### Architecture Decision Records (ADRs)

The `docs/adr/` folder contains ADRs documenting key design decisions:

| ADR | Title |
|-----|-------|
| [ADR-001](docs/adr/001-standardize-ipc-api.md) | Standardize IPC / Message Bus API |
| [ADR-002](docs/adr/002-async-first-api.md) | Async-First Public API with Sync Wrappers |
| [ADR-003](docs/adr/003-plugin-strategy-pattern.md) | Plugin-based Strategy Pattern |
| [ADR-004](docs/adr/004-configuration-driven-setup.md) | Configuration-Driven Library Setup |
| [ADR-005](docs/adr/005-connection-manager.md) | Central ConnectionManager |
| [ADR-006](docs/adr/006-exchange-types.md) | Multiple Exchange Types via Handlers |
| [ADR-007](docs/adr/007-startup-policy-rendezvous.md) | StartupPolicy and Rendezvous |
| [ADR-008](docs/adr/008-subscription-cache.md) | SubscriptionCache for Sync Access |
| [ADR-009](docs/adr/009-unroutable-message-handling.md) | Configurable Unroutable Handling |

### Diagrams

The `docs/diagrams/` folder contains PlantUML diagrams:

| Diagram | Description |
|---------|-------------|
| [overview.puml](docs/diagrams/overview.puml) | Plugin strategy overview |
| [architecture.puml](docs/diagrams/architecture.puml) | Package structure |
| [component.puml](docs/diagrams/component.puml) | Component interfaces |
| [class.puml](docs/diagrams/class.puml) | Full class diagram |
| [sequence-lifecycle.puml](docs/diagrams/sequence-lifecycle.puml) | End-to-end lifecycle |

### API Documentation

Detailed API documentation: [EventBusClient.pdf](https://github.com/test-fullautomation/python-rabbitmq-messagebus/blob/develop/EventBusClient/EventBusClient.pdf)

## Feedback

To give us feedback, you can send an email to [Thomas Pollerspöck](mailto:Thomas.Pollerspoeck@de.bosch.com)

To report bugs or request features, please raise a ticket on GitHub.

## Maintainers

[Nguyen Huynh Tri Cuong](mailto:Cuong.NguyenHuynhTri@vn.bosch.com)

## Contributors

- [Nguyen Huynh Tri Cuong](mailto:Cuong.NguyenHuynhTri@vn.bosch.com)
- [Thomas Pollerspöck](mailto:Thomas.Pollerspoeck@de.bosch.com)

## License

Copyright 2020-2025 Robert Bosch GmbH

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
