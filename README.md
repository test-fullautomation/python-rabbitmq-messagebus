# RabbitMqMessagebus Package Description

## Getting Started

TODO

## How to install

TODO

## Package Documentation (Temporary)
# 🚀 EventBusClient

EventBusClient is a modular, pluggable messaging library built on top of RabbitMQ.  
It simplifies publishing and subscribing to events and supports dynamic loading of project-specific serializers, exchange handlers, and message classes.

---

## 📂 Project structure

```
project/
├── event_bus/
│   ├── client.py
│   ├── connection.py
│   ├── serializer/
│   ├── exchange_handler/
│   ├── message/
├── plugins/
│   ├── mcpi/
│   │   ├── serialize/
│   │   ├── message/
│   │   └── exchange/
├── config/
│   └── config.jsonp
└── app.py
```

---

## 📜 Configuration: `config/config.jsonp`

```json
{
  "plugins_path": "./plugins",
  "host": "localhost",
  "port": 5672,
  "serializer": "PickleSerializer",
  "exchange_handler": "XRTopicExchangeHandler",
  "message_class": "ListenerEventMsg",
  "threadsafe_publish": true,
  "auto_reconnect": true,
  "qos_prefetch": 10
}
```

### 🔥 Explanation of fields

| Field               | Description                                         |
|---------------------|-----------------------------------------------------|
| `plugins_path`      | Path to your custom plugins folder                  |
| `host`              | RabbitMQ server hostname                            |
| `port`              | RabbitMQ server port                                |
| `serializer`        | Class name of the serializer to use                |
| `exchange_handler`  | Class name of the exchange handler to use           |
| `message_class`     | Default message class for publishing/subscribing    |
| `threadsafe_publish`| Enable thread-safe publishing                       |
| `auto_reconnect`    | Automatically reconnect on connection loss          |
| `qos_prefetch`      | Prefetch count for consumers                        |

---

## 🚀 Quick Start

### ✅ Install dependencies
```bash
pip install -r requirements.txt
```

### ✅ Send a message
```python
import asyncio
from event_bus.client import EventBusClient
from plugins.mcpi.message.listener_event_msg import ListenerEventMsg

async def main():
    client = await EventBusClient.from_config("./config/config.jsonp")

    msg = ListenerEventMsg(event="start_cycle", timestamp=1234567890)
    await client.send("zone1.topic.start", msg)

    await client.close()

asyncio.run(main())
```

---

### ✅ Subscribe to messages
```python
async def on_message(msg: ListenerEventMsg):
    print(f"Received: {msg.event} at {msg.timestamp}")

await client.on("zone1.#", ListenerEventMsg, on_message)
```

---

## 🔒 Security note
Avoid using `PickleSerializer` in untrusted environments.  
For production, prefer `JsonSerializer` or `ProtobufSerializer` for secure and cross-language serialization.

---

## 📦 Requirements

See `requirements.txt` for dependencies.

---

## 📌 Features

- 🪝 Pluggable architecture: load serializers, handlers, messages dynamically
- 🔁 Automatic reconnect (if enabled)
- 🧵 Thread-safe publishing for multi-threaded apps
- 🔒 Secure JSON/Protobuf serializers

A detailed documentation of the **RabbitMqMessagebus** package can be
found here: [RabbitMqMessagebus.pdf](TODO)

## Feedback

To give us a feedback, you can send an email to [Thomas
Pollerspöck](mailto:Thomas.Pollerspoeck@de.bosch.com)

In case you want to report a bug or request any interesting feature,
please don\'t hesitate to raise a ticket.

## Maintainers

[Thomas Pollerspöck](mailto:Thomas.Pollerspoeck@de.bosch.com)

## Contributors

TODO

## License

Copyright 2020-2025 Robert Bosch GmbH

Licensed under the Apache License, Version 2.0 (the \"License\"); you
may not use this file except in compliance with the License. You may
obtain a copy of the License at

> [![License: Apache
> v2](https://img.shields.io/pypi/l/robotframework.svg)](http://www.apache.org/licenses/LICENSE-2.0.html)

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an \"AS IS\" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
