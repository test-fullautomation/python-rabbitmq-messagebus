.. Copyright 2020-2025 Robert Bosch GmbH

.. Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

.. http://www.apache.org/licenses/LICENSE-2.0

.. Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

EventBusClient - RabbitMQ Message Bus Library
=============================================

|License: Apache v2|

EventBusClient is an event-driven messaging library for Python, designed to simplify distributed communication using
RabbitMQ as the message broker. It provides a clean, pluggable architecture for robust inter-process messaging,
topic management, and coordination in scalable applications.

Why EventBusClient?
-------------------

The Problem
~~~~~~~~~~~

Building distributed systems with message queues typically involves:

- Writing boilerplate code for connection management, serialization, and error handling
- Implementing retry logic, reconnection, and graceful shutdown
- Coordinating startup order across multiple processes
- Handling different environments (dev, test, production) with different configurations
- Supporting both async and sync codebases

The Solution
~~~~~~~~~~~~

EventBusClient abstracts away the complexity of RabbitMQ while remaining flexible:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Challenge
     - EventBusClient Solution
   * - Boilerplate code
     - Clean ``send()`` / ``on()`` API with automatic setup
   * - Connection management
     - Auto-reconnection, robust lifecycle handling
   * - Multi-process coordination
     - Built-in Rendezvous pattern for startup synchronization
   * - Environment configuration
     - JSONP config files with environment variable support
   * - Async vs Sync
     - Async-first API with sync wrappers for legacy code
   * - Extensibility
     - Pluggable serializers, exchange handlers, and policies

When to Use EventBusClient
--------------------------

**Ideal for:**

- **Test Automation Systems** - Coordinate multiple test runners, controllers, and reporters
- **Multi-Process Applications** - Decouple processes that need to communicate asynchronously
- **Microservices** - Event-driven communication between services
- **Data Pipelines** - Stream data between producers and consumers
- **Distributed Systems** - Any system requiring reliable message passing

**Consider alternatives if:**

- You need simple in-process pub/sub (use Python's built-in ``queue`` module)
- You're building a single monolithic application with no IPC needs
- You need guaranteed exactly-once delivery (RabbitMQ provides at-least-once)

Key Features
------------

- **Async-First API** - Native async/await support with sync wrappers for legacy code
- **Pluggable Architecture** - Extensible serializers, exchange handlers, message types, and startup policies
- **Configuration-Driven** - JSONP-based configuration with environment variable support
- **Multiple Exchange Types** - Topic, Fanout, and X-RTopic exchange handlers
- **Coordinated Startup** - Rendezvous pattern for multi-process synchronization
- **Unroutable Message Handling** - Configurable policies (drop, return, alternate-exchange)
- **Thread-Safe Operations** - Safe publishing from multiple threads
- **Auto-Reconnection** - Robust connection management with automatic recovery

Table of Contents
-----------------

- `Getting Started <#getting-started>`__
- `Quick Start <#quick-start>`__
- `Main APIs <#main-apis>`__
- `Configuration Reference <#configuration-reference>`__
- `Examples <#examples>`__
- `Documentation <#documentation>`__
- `Feedback <#feedback>`__
- `License <#license>`__

Getting Started
---------------

Installation
~~~~~~~~~~~~

::

   pip install eventbusclient

Prerequisites
~~~~~~~~~~~~~

- Python 3.8+
- RabbitMQ server running (default: localhost:5672)

Quick Start
-----------

**1. Create a configuration file (config.jsonp):**

.. code-block:: json

   {
     "host": "localhost",
     "port": 5672,
     "serializer": "JsonSerializer",
     "exchange_handler": "TopicExchangeHandler",
     "auto_reconnect": true
   }

**2. Create a producer:**

.. code-block:: python

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

**3. Create a consumer:**

.. code-block:: python

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

Main APIs
---------

Async API (Primary)
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Factory methods
   client = await EventBusClient.from_config(config_path)

   # Connection
   await client.connect(host, port, prefetch_count=10)
   await client.close()
   is_connected = client.is_connected()

   # Publish/Subscribe (routing key based)
   await client.send(routing_key, message, headers=None)
   cache = await client.on(routing_key, message_cls, callback)
   await client.off(routing_key, callback)

   # Publish/Subscribe (headers based - for HeadersExchangeHandler)
   cache = await client.on(
       routing_key="",  # Ignored in headers exchange
       message_cls=DocumentMessage,
       callback=handler,
       binding_headers={"format": "pdf", "type": "report"},
       match_all=True  # AND logic (x-match=all)
   )

   # Coordination (Rendezvous)
   await client.announce_ready(roles=["worker"])
   success = await client.wait_until_ready(requirements={"worker": 2}, timeout=30)

   # Unroutable messages
   unroutables = client.pop_unroutables()

Sync API (Legacy Support)
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Factory methods
   client = EventBusClient.from_config_sync(config_path)

   # Connection
   client.connect_sync(host, port, prefetch_count=10)
   client.close_sync()

   # Publish/Subscribe (routing key based)
   client.send_sync(routing_key, message, headers=None)
   cache = client.on_sync(routing_key, message_cls, callback)
   client.off_sync(routing_key, callback)

   # Publish/Subscribe (headers based - for HeadersExchangeHandler)
   cache = client.on_sync(
       routing_key="",  # Ignored in headers exchange
       message_cls=DocumentMessage,
       callback=handler,
       binding_headers={"format": "pdf", "type": "report"},
       match_all=True  # AND logic (x-match=all)
   )

SubscriptionCache API
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Get messages from cache
   message = cache.get(timeout=5.0)           # Block until message or timeout
   message = cache.pop(timeout=5.0)           # Get and remove
   message = cache.peek(timeout=5.0)          # Get without removing

   # Wait for specific messages
   found = cache.wait_for_one(target_msg, timeout=10)
   indices = cache.wait_for_many(
       targets=[msg1, msg2, msg3],
       mode=WaitMode.ALL_IN_GIVEN_ORDER,
       timeout=30
   )

   # Drain all messages
   messages = cache.drain(max_items=100)

Configuration Reference
-----------------------

Create a configuration file (``config.jsonp``) based on the template at ``EventBusClient/config/config.jsonp.template``:

.. list-table::
   :header-rows: 1
   :widths: 20 10 10 15 45

   * - Option
     - Type
     - Required
     - Default
     - Description
   * - ``host``
     - str
     - No
     - "localhost"
     - RabbitMQ server hostname
   * - ``port``
     - int
     - No
     - 5672
     - RabbitMQ server port
   * - ``serializer``
     - str
     - **Yes**
     - \-
     - Serializer class name (PickleSerializer, JsonSerializer, ProtobufSerializer)
   * - ``exchange_handler``
     - str
     - **Yes**
     - \-
     - Exchange handler class name (TopicExchangeHandler, FanoutExchangeHandler, XRTopicExchangeHandler)
   * - ``exchange_name``
     - str
     - No
     - auto
     - Custom exchange name
   * - ``auto_reconnect``
     - bool
     - No
     - true
     - Enable auto-reconnection
   * - ``qos_prefetch``
     - int
     - No
     - 10
     - Prefetch count for QoS
   * - ``plugins_path``
     - str
     - No
     - "./plugins"
     - Custom plugins directory
   * - ``general_cache_policy``
     - str
     - No
     - "off"
     - General cache policy (off, on_connect, on_demand)
   * - ``logger_name``
     - str
     - No
     - "event_bus_client"
     - Logger name
   * - ``logfile``
     - str
     - No
     - None
     - Log file path ("console" for stdout)
   * - ``loglevel``
     - str
     - No
     - "INFO"
     - Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
   * - ``logger_mode``
     - str
     - No
     - "a"
     - Log file mode ("w" for overwrite, "a" for append)

Exchange Handlers
~~~~~~~~~~~~~~~~~

The ``exchange_handler`` configuration determines the RabbitMQ exchange type used for message routing:

.. list-table::
   :header-rows: 1
   :widths: 25 15 30 30

   * - Handler Class
     - Exchange Type
     - Routing Behavior
     - Use Case
   * - ``TopicExchangeHandler``
     - topic
     - Pattern matching with ``*`` (one word) and ``#`` (zero or more)
     - Most common - selective routing
   * - ``FanoutExchangeHandler``
     - fanout
     - Broadcasts to all bound queues
     - Notifications, system-wide events
   * - ``HeadersExchangeHandler``
     - headers
     - Routes based on message header attributes
     - Complex routing with multiple attributes
   * - ``XRTopicExchangeHandler``
     - x-rtopic
     - Reverse topic matching (requires broker plugin)
     - Advanced use cases

**When to use which handler:**

- **TopicExchangeHandler** (recommended default) - When you need flexible routing with patterns
- **FanoutExchangeHandler** - When all subscribers should receive all messages
- **HeadersExchangeHandler** - When routing depends on multiple message attributes (AND/OR logic)
- **XRTopicExchangeHandler** - Advanced use cases requiring reverse matching

Serializers
~~~~~~~~~~~

The ``serializer`` configuration determines how messages are encoded/decoded:

.. list-table::
   :header-rows: 1
   :widths: 25 15 30 30

   * - Serializer Class
     - Format
     - Pros
     - Use Case
   * - ``PickleSerializer``
     - Python Pickle
     - Fast, supports any Python object
     - Internal Python-to-Python communication
   * - ``JsonSerializer``
     - JSON
     - Human-readable, cross-language
     - Interoperability, debugging
   * - ``ProtobufSerializer``
     - Protocol Buffers
     - Compact, fast, schema-enforced
     - High-performance production systems

**Recommendation:**

- Use ``PickleSerializer`` for pure Python systems (fastest, most flexible)
- Use ``JsonSerializer`` for debugging or multi-language systems
- Use ``ProtobufSerializer`` for high-performance production systems

Examples
--------

The ``examples/`` folder contains comprehensive examples:

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Example
     - Description
   * - ``basic_sample.py``
     - Basic publish/subscribe
   * - ``sync_sample.py``
     - Synchronous API usage
   * - ``wait_mode_sample.py``
     - WaitMode options
   * - ``rendezvous_sample.py``
     - Multi-process coordination
   * - ``request_reply_sample.py``
     - RPC pattern
   * - ``multiple_subscriptions_sample.py``
     - Multiple topics
   * - ``custom_message_sample.py``
     - Custom message types
   * - ``error_handling_sample.py``
     - Error handling patterns
   * - ``alternate_exchange_sample.py``
     - Unroutable handling
   * - ``headers_exchange_sample.py``
     - Header-based message routing

See ``examples/README.md`` for detailed documentation.

Documentation
-------------

Architecture Decision Records (ADRs)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``docs/adr/`` folder contains ADRs documenting key design decisions:

.. list-table::
   :header-rows: 1
   :widths: 15 85

   * - ADR
     - Title
   * - ADR-001
     - Standardize IPC / Message Bus API
   * - ADR-002
     - Async-First Public API with Sync Wrappers
   * - ADR-003
     - Plugin-based Strategy Pattern
   * - ADR-004
     - Configuration-Driven Library Setup
   * - ADR-005
     - Central ConnectionManager
   * - ADR-006
     - Multiple Exchange Types via Handlers
   * - ADR-007
     - StartupPolicy and Rendezvous
   * - ADR-008
     - SubscriptionCache for Sync Access
   * - ADR-009
     - Configurable Unroutable Handling

Diagrams
~~~~~~~~

The ``docs/diagrams/`` folder contains PlantUML diagrams:

- ``overview.puml`` - Plugin strategy overview
- ``architecture.puml`` - Package structure
- ``component.puml`` - Component interfaces
- ``class.puml`` - Full class diagram
- ``sequence-lifecycle.puml`` - End-to-end lifecycle

API Documentation
~~~~~~~~~~~~~~~~~

Detailed API documentation: `EventBusClient.pdf <https://github.com/test-fullautomation/python-rabbitmq-messagebus/blob/develop/EventBusClient/EventBusClient.pdf>`_

Feedback
--------

To give us feedback, you can send an email to `Thomas Pollerspöck <mailto:Thomas.Pollerspoeck@de.bosch.com>`_

To report bugs or request features, please raise a ticket on GitHub.

Maintainers
-----------

`Nguyen Huynh Tri Cuong <mailto:Cuong.NguyenHuynhTri@vn.bosch.com>`_

Contributors
------------

- `Nguyen Huynh Tri Cuong <mailto:Cuong.NguyenHuynhTri@vn.bosch.com>`_
- `Thomas Pollerspöck <mailto:Thomas.Pollerspoeck@de.bosch.com>`_

License
-------

Copyright 2020-2025 Robert Bosch GmbH

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    |License: Apache v2|

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


.. |License: Apache v2| image:: https://img.shields.io/pypi/l/robotframework.svg
   :target: http://www.apache.org/licenses/LICENSE-2.0.html
