# EventBusClient Examples

This directory contains example scripts demonstrating various features and patterns of the EventBusClient library.

## Prerequisites

1. RabbitMQ server running on `localhost:5672`
2. Configuration file at `./config.jsonp` (included in this folder)
3. Python dependencies installed

## Examples Overview

| Example | Description |
|---------|-------------|
| [basic_async_producer_consumer_sample.py](#basic-async-producer-consumer) | Basic async producer/consumer pattern |
| [basic_sync_producer_consumer_sample.py](#basic-sync-producer-consumer) | Basic sync producer/consumer pattern |
| [wait_mode_sample.py](#wait-modes) | Wait operations with different modes |
| [rendezvous_sample.py](#rendezvous-coordination) | Multi-client coordination |
| [request_reply_sample.py](#request-reply-rpc) | RPC pattern implementation |
| [multiple_subscriptions_sample.py](#multiple-subscriptions) | Multiple topics and message types |
| [custom_message_sample.py](#custom-messages) | Creating custom message classes |
| [error_handling_sample.py](#error-handling) | Error handling patterns |
| [alternate_exchange_sample.py](#alternate-exchange) | Unroutable message handling |
| [headers_exchange_sample.py](#headers-exchange) | Header-based message routing |

---

## Basic Async Producer Consumer

**File:** `basic_async_producer_consumer_sample.py`

Demonstrates the basic asynchronous producer-consumer pattern using `asyncio`.

```bash
# Terminal 1: Start consumer
python basic_async_producer_consumer_sample.py consumer

# Terminal 2: Start producer
python basic_async_producer_consumer_sample.py producer
```

---

## Basic Sync Producer Consumer

**File:** `basic_sync_producer_consumer_sample.py`

Demonstrates the synchronous API with `from_config_sync()`, `connect_sync()`, `send_sync()`, and `on_sync()`.

```bash
# Terminal 1: Start consumer
python basic_sync_producer_consumer_sample.py consumer

# Terminal 2: Start producer
python basic_sync_producer_consumer_sample.py producer
```

---

## Wait Modes

**File:** `wait_mode_sample.py`

Demonstrates `wait_for_one` and `wait_for_many` with different `WaitMode` options:

- **ALL_IN_GIVEN_ORDER**: Wait for messages in exact sequence
- **ALL_IN_RANDOM_ORDER**: Wait for all messages in any order
- **ANY_OF_GIVEN_MSGS**: Wait for any one of the specified messages

```bash
# Terminal 1: Start one of the consumers
python wait_mode_sample.py wait_one        # Wait for specific message
python wait_mode_sample.py wait_ordered    # Wait for messages in order
python wait_mode_sample.py wait_random     # Wait for messages in any order
python wait_mode_sample.py wait_any        # Wait for any matching message

# Terminal 2: Start producer
python wait_mode_sample.py producer
```

**Key concepts:**
- Messages need `__eq__` method for matching
- `wait_for_one` returns `True`/`False`
- `wait_for_many` returns list of matched indices

---

## Rendezvous Coordination

**File:** `rendezvous_sample.py`

Demonstrates multi-client coordination using `wait_until_ready` and `announce_ready`.

```bash
# Terminal 1: Start coordinator (waits for 2 workers)
python rendezvous_sample.py coordinator

# Terminal 2: Start first worker
python rendezvous_sample.py worker worker1

# Terminal 3: Start second worker
python rendezvous_sample.py worker worker2
```

**Flow:**
1. Workers announce they are ready with role `"worker"`
2. Coordinator waits for 2 workers: `{"worker": 2}`
3. Coordinator announces ready with role `"coordinator"`
4. Workers wait for coordinator: `{"coordinator": 1}`
5. All parties proceed with synchronized work

---

## Request-Reply (RPC)

**File:** `request_reply_sample.py`

Implements a request-reply pattern with:
- Correlation IDs for matching requests to responses
- Unique reply topics per client
- Timeout handling

```bash
# Terminal 1: Start RPC server
python request_reply_sample.py server

# Terminal 2: Run client demo
python request_reply_sample.py client
```

**Available RPC methods:**
- `add(a, b)` - Add two numbers
- `multiply(a, b)` - Multiply two numbers
- `echo(message)` - Echo a message
- `slow_operation(duration)` - Simulated slow operation

---

## Multiple Subscriptions

**File:** `multiple_subscriptions_sample.py`

Demonstrates:
- Subscribing to multiple topics
- Different message types per topic
- Statistics tracking
- Unsubscribe functionality

```bash
# Terminal 1: Start consumer
python multiple_subscriptions_sample.py consumer

# Terminal 2: Start producer
python multiple_subscriptions_sample.py producer

# Demo unsubscribe
python multiple_subscriptions_sample.py unsub
```

**Topics used:**
- `sensors.temperature` - Temperature readings
- `sensors.humidity` - Humidity readings
- `sensors.pressure` - Pressure readings
- `alerts.system` - System alerts
- `system.status` - Status updates

---

## Custom Messages

**File:** `custom_message_sample.py`

Demonstrates creating custom message classes with:
- Field validation
- Enum status fields
- Computed properties
- Nested message objects
- Equality for wait operations

```bash
python custom_message_sample.py
```

**Message classes demonstrated:**
- `UserMessage` - Basic validation
- `OrderMessage` - Enum status, computed properties
- `ShipmentMessage` - Nested `AddressMessage` objects
- `EventMessage` - Custom `__eq__` and `__hash__` for wait operations

---

## Error Handling

**File:** `error_handling_sample.py`

Demonstrates error handling patterns:

```bash
# Run all demos
python error_handling_sample.py

# Run specific demo
python error_handling_sample.py connection   # Connection errors
python error_handling_sample.py handler      # Handler error isolation
python error_handling_sample.py shutdown     # Graceful shutdown
python error_handling_sample.py retry        # Retry pattern
python error_handling_sample.py deadletter   # Dead letter handling
python error_handling_sample.py timeout      # Timeout handling
```

**Patterns covered:**
1. **Connection errors** - Handling invalid host/port
2. **Handler isolation** - Errors in handlers don't crash client
3. **Graceful shutdown** - Clean shutdown with pending operations
4. **Retry pattern** - Automatic retry with backoff
5. **Dead letter** - Forwarding failed messages to DLQ
6. **Timeout handling** - Handling `cache.get()` timeouts

---

## Alternate Exchange

**File:** `alternate_exchange_sample.py`

Demonstrates unroutable message handling policies:

```bash
python alternate_exchange_sample.py drop         # Silently discard
python alternate_exchange_sample.py log          # Log as warning
python alternate_exchange_sample.py cache        # Store in list
python alternate_exchange_sample.py callback     # Custom callback
python alternate_exchange_sample.py alternate    # Route to alternate exchange
python alternate_exchange_sample.py raise        # Raise exception
python alternate_exchange_sample.py client-cache # Use client's built-in cache
```

**Policies:**

| Policy | Description |
|--------|-------------|
| `drop` | Silently discard (default RabbitMQ behavior) |
| `log` | Log unroutable messages as warnings |
| `cache` | Store in a list for later inspection |
| `callback` | Call custom function |
| `alternate-exchange` | Route to alternate exchange/queue |
| `raise` | Raise `RuntimeError` |

**Alternate Exchange setup:**
- Creates main exchange with `alternate-exchange` argument
- Creates fanout alternate exchange
- Creates durable queue for unroutable messages

---

## Headers Exchange

**File:** `headers_exchange_sample.py`

Demonstrates the `HeadersExchangeHandler` for routing messages based on header attributes instead of routing keys.

```bash
python headers_exchange_sample.py
```

**Key concepts:**

| Match Mode | x-match | Description |
|------------|---------|-------------|
| `match_all=True` | `all` | ALL specified headers must match (AND logic) |
| `match_all=False` | `any` | At least ONE header must match (OR logic) |

**Example subscription:**

```python
from EventBusClient import EventBusClient
from EventBusClient.exchange_handler.headers_handler import HeadersExchangeHandler
from EventBusClient.serializer.json_serializer import JsonSerializer

# Create client with HeadersExchangeHandler
handler = HeadersExchangeHandler(name="documents_exchange", serializer=JsonSerializer())
client = EventBusClient(exchange_handler=handler, host="localhost", port=5672)
await client.connect()

# Subscribe with x-match=all (AND logic)
async def handle_docs(msg, headers):
    print(f"Received: {msg} with headers {headers}")

await client.on(
    routing_key="",  # Ignored in headers exchange
    message_cls=DocumentMessage,
    callback=handle_docs,
    binding_headers={"format": "pdf", "department": "engineering"},
    match_all=True  # Both headers must match
)

# Publish with headers
await client.send(
    routing_key="",  # Ignored in headers exchange
    message=DocumentMessage(title="Q4 Report"),
    headers={"format": "pdf", "department": "engineering", "author": "john"}
)
```

**Scenarios demonstrated:**

1. **ALL match subscriber** - Only receives messages where ALL binding headers match
2. **ANY match subscriber** - Receives messages where ANY binding header matches
3. **Various publish scenarios** showing which subscribers receive which messages

---

## Configuration

Examples use the `config.jsonp` file in this folder:

```json
{
    "exchange_handler": "TopicExchangeHandler",
    "serializer": "PickleSerializer",
    "host": "localhost",
    "port": 5672,
    "exchange_name": "event_bus",
    "auto_reconnect": true,
    "qos_prefetch": 10,
    "loglevel": "INFO"
}
```

---

## Common Patterns

### Creating a Message Class

```python
from EventBusClient.message.base_message import BaseMessage

class MyMessage(BaseMessage):
    def __init__(self, data=None):
        super().__init__()
        self.data = data

    @classmethod
    def from_data(cls, data):
        return cls(data=data.get("data"))

    def get_value(self):
        return self

    # Optional: for wait_for operations
    def __eq__(self, other):
        if isinstance(other, MyMessage):
            return self.data == other.data
        return False
```

### Async Pattern

```python
async def main():
    client = await EventBusClient.from_config("config.jsonp")

    async def handler(msg, headers):
        print(f"Received: {msg}")

    await client.on("my.topic", MyMessage, handler)
    await client.send("my.topic", MyMessage("hello"))
    await client.close()

asyncio.run(main())
```

### Sync Pattern

```python
def main():
    client = EventBusClient.from_config_sync("config.jsonp")
    client.connect_sync()

    cache = client.on_sync("my.topic", MyMessage)
    client.send_sync("my.topic", MyMessage("hello"))

    msg = cache.get(timeout=5.0)
    print(f"Received: {msg}")

    client.close_sync()
```
