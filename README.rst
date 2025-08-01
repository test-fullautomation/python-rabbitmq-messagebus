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

RabbitMqMessagebus Package Description
======================================

EventBusClient is an event-driven messaging library for Python, designed to simplify distributed communication using
RabbitMQ as the message broker. It enables robust inter-process messaging, topic management, and coordination for scalable applications.

Table of Contents
-----------------

-  `Getting Started <#getting-started>`__
-  `Usage <#building-and-testing>`__
-  `Example <#example>`__
-  `Feedback <#feedback>`__
-  `Maintainers <#maintainers>`__
-  `Contributors <#contributors>`__
-  `3rd Party Licenses <#3rd-party-licenses>`__
-  `Used Encryption <#used-encryption>`__
-  `License <#license>`__

Getting Started
---------------

EventBusClient is available on PyPI. To install, run:

::

   pip install eventbusclient

Ensure RabbitMQ is installed and running. Configure your RabbitMQ server connection in your application settings as required.

Usage
-------

To use the EventBusClient in a real-world scenario with producer and consumer processes, see the example below:

.. code-block:: python

   import asyncio
   import logging
   import time
   from multiprocessing import Process
   from EventBusClient.event_bus_client import EventBusClient
   from EventBusClient.message.base_message import BaseMessage

   # Define a custom message class
   class TestMessage(BaseMessage):
       def __init__(self, content=None):
           super().__init__()
           self.content = content

   # Producer process: sends messages to the topic exchange
   async def producer_process(config_path):
       client = await EventBusClient.from_config(config_path)
       for i in range(5):
           msg = TestMessage(f"Message #{i} from producer")
           await client.send("test.topic", msg)
           await asyncio.sleep(1)
       await client.close()

   # Consumer process: receives messages from the topic
   async def consumer_process(config_path):
       client = await EventBusClient.from_config(config_path)
       async def message_handler(message):
           print(f"Received: {message.content}")
       await client.on("test.topic", TestMessage, message_handler)
       await asyncio.sleep(10)
       await client.close()

   # Helper to run async functions in a process
   def run_process(target_func, config_path):
       asyncio.run(target_func(config_path))

   # Main function to start producer and consumer processes
   def main():
       config_path = "../config/config.jsonp"
       consumer = Process(target=run_process, args=(consumer_process, config_path))
       consumer.start()
       time.sleep(2)
       producer = Process(target=run_process, args=(producer_process, config_path))
       producer.start()
       producer.join()
       consumer.join()

   if __name__ == "__main__":
       main()
..

Config File Construction
------------------------------

Create a configuration file (e\.g\. `config\.jsonp`) with your RabbitMQ and client settings\. Example:

.. code-block:: json

    {
      "plugins_path": "./plugins",           // Path to plugins directory
      "host": "localhost",                   // RabbitMQ server hostname
      "port": 5672,                          // RabbitMQ server port
      "serializer": "PickleSerializer",      // Message serialization method
      "exchange_handler": "TopicExchangeHandler", // Exchange handler type
      "message_class": "ListenerEventMsg",   // Default message class
      "threadsafe_publish": true,            // Enable thread-safe publishing
      "auto_reconnect": true,                // Automatically reconnect on failure
      "qos_prefetch": 10                     // Prefetch count for QoS
    }

**Parameter explanations:**

- ``plugins_path``: Directory for loading plugins.
- ``host``: RabbitMQ server address.
- ``port``: RabbitMQ server port.
- ``serializer``: Serialization method for messages.
- ``exchange_handler``: Handler for exchange type.
- ``message_class``: Class used for messages.
- ``threadsafe_publish``: If ``true``, enables thread-safe publishing.
- ``auto_reconnect``: If ``true``, client will auto-reconnect on connection loss.
- ``qos_prefetch``: Number of messages to prefetch for consumers.

Update the ``config_path`` in your code to point to this file.

Package Documentation
---------------------

A detailed documentation of the **RabbitMqMessagebus** package can be found here: `EventBusClient.pdf <https://github.com/test-fullautomation/python-rabbitmq-messagebus/blob/develop/EventBusClient/EventBusClient.pdf>`_

Feedback
--------

To give us a feedback, you can send an email to `Thomas Pollerspöck <mailto:Thomas.Pollerspoeck@de.bosch.com>`_

In case you want to report a bug or request any interesting feature, please don't hesitate to raise a ticket.

Maintainers
-----------

`Nguyen Huynh Tri Cuong <mailto:Cuong.NguyenHuynhTri@vn.bosch.com>`_

Contributors
------------

`Nguyen Huynh Tri Cuong <mailto:Cuong.NguyenHuynhTri@vn.bosch.com>`_

`Thomas Pollerspöck <mailto:Thomas.Pollerspoeck@de.bosch.com>`_


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

