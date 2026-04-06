#  Copyright 2020-2025 Robert Bosch GmbH
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
# *******************************************************************************
#
# File: alternate_exchange_sample.py
#
# Initially created by Claude Code / January 2026.
#
# Description:
#
#   Demonstrates the different unroutable message handling policies:
#   - drop: Silently discard unroutable messages
#   - log: Log unroutable messages as warnings
#   - return: Use mandatory flag and handle basic.return
#   - alternate-exchange: Route unroutable messages to an alternate exchange
#
# Note: These options affect what happens when a message cannot be routed
# to any queue (no matching subscribers).
#
# Usage:
#   python alternate_exchange_sample.py <policy>
#   where <policy> is one of: drop, log, return, alternate, cache, callback
#
# *******************************************************************************
import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from EventBusClient.event_bus_client import EventBusClient
from EventBusClient.message.base_message import BaseMessage
from EventBusClient.exchange_handler.topic_handler import TopicExchangeHandler
from EventBusClient.serializer.pickle_serializer import PickleSerializer


class TestMessage(BaseMessage):
    """Simple test message."""
    def __init__(self, content: str = None):
        super().__init__()
        self.content = content

    @classmethod
    def from_data(cls, data):
        return cls(content=data.get("content"))

    def get_value(self):
        return self

    def __repr__(self):
        return f"TestMessage({self.content!r})"


# =============================================================================
# Policy 1: DROP - Silently discard unroutable messages
# =============================================================================

async def demo_drop_policy(config_path: str):
    """
    DROP policy: Unroutable messages are silently discarded.
    This is the default behavior in RabbitMQ.
    """
    logging.info("\n=== Policy: DROP ===")
    logging.info("Unroutable messages will be silently discarded.")

    # Create client with drop policy
    serializer = PickleSerializer()
    handler = TopicExchangeHandler(name="demo.drop", serializer=serializer)
    handler.configure_unroutable(
        policy="drop",
        alternate_exchange=None,
        on_unroutable="log",  # This won't be triggered with drop
        unroutable_sink=None,
        on_unroutable_callback=None
    )

    client = EventBusClient(
        exchange_handler=handler,
        serializer=serializer,
        host="localhost",
        port=5672
    )
    client.start_background_loop()
    client.connect_sync()

    # Send message to topic with no subscribers
    msg = TestMessage("This message will be dropped")
    logging.info(f"Sending to unsubscribed topic: {msg}")
    client.send_sync("unsubscribed.topic.drop", msg)

    logging.info("Message sent - no error, but it was discarded")

    await asyncio.sleep(1)
    client.close_sync()


# =============================================================================
# Policy 2: LOG - Log unroutable messages
# =============================================================================

async def demo_log_policy(config_path: str):
    """
    LOG policy: Unroutable messages are logged as warnings.
    Requires 'return' policy to receive the notification.
    """
    logging.info("\n=== Policy: LOG ===")
    logging.info("Unroutable messages will be logged.")

    serializer = PickleSerializer()
    handler = TopicExchangeHandler(name="demo.log", serializer=serializer)
    handler.configure_unroutable(
        policy="return",  # Need return to get notifications
        alternate_exchange=None,
        on_unroutable="log",  # Action when unroutable detected
        unroutable_sink=None,
        on_unroutable_callback=None
    )

    client = EventBusClient(
        exchange_handler=handler,
        serializer=serializer,
        host="localhost",
        port=5672
    )
    client.start_background_loop()
    client.connect_sync()

    msg = TestMessage("This message will be logged as unroutable")
    logging.info(f"Sending to unsubscribed topic: {msg}")

    # Note: The publisher needs to use mandatory=True for returns to work
    # This is handled internally when policy="return"
    client.send_sync("unsubscribed.topic.log", msg)

    await asyncio.sleep(2)  # Wait for return callback
    client.close_sync()


# =============================================================================
# Policy 3: CACHE - Store unroutable messages in a list
# =============================================================================

async def demo_cache_policy(config_path: str):
    """
CACHE policy: Store unroutable messages in a list for later inspection.
    """
    logging.info("\n=== Policy: CACHE ===")
    logging.info("Unroutable messages will be cached.")

    serializer = PickleSerializer()
    handler = TopicExchangeHandler(name="demo.cache", serializer=serializer)

    # Use the client's unroutable_cache
    unroutable_list = []

    handler.configure_unroutable(
        policy="return",
        alternate_exchange=None,
        on_unroutable="cache",
        unroutable_sink=unroutable_list,  # Messages stored here
        on_unroutable_callback=None
    )

    client = EventBusClient(
        exchange_handler=handler,
        serializer=serializer,
        host="localhost",
        port=5672
    )
    client.start_background_loop()
    client.connect_sync()

    # Send multiple unroutable messages
    for i in range(3):
        msg = TestMessage(f"Unroutable message #{i}")
        logging.info(f"Sending: {msg}")
        client.send_sync(f"unsubscribed.topic.cache.{i}", msg)

    await asyncio.sleep(2)

    logging.info(f"Cached unroutable messages: {len(unroutable_list)}")
    for item in unroutable_list:
        logging.info(f"  - Routing key: {item.get('routing_key')}")

    client.close_sync()


# =============================================================================
# Policy 4: CALLBACK - Call custom function for unroutable messages
# =============================================================================

async def demo_callback_policy(config_path: str):
    """
CALLBACK policy: Call a custom function when message is unroutable.
    """
    logging.info("\n=== Policy: CALLBACK ===")
    logging.info("Custom callback will be invoked for unroutable messages.")

    serializer = PickleSerializer()
    handler = TopicExchangeHandler(name="demo.callback", serializer=serializer)

    unroutable_count = [0]  # Use list for mutable counter

    def on_unroutable(info: dict):
        """Custom callback for unroutable messages."""
        unroutable_count[0] += 1
        logging.warning(f"[CALLBACK] Unroutable message detected!")
        logging.warning(f"  Routing key: {info.get('routing_key')}")
        logging.warning(f"  Exchange: {info.get('exchange')}")
        logging.warning(f"  Reply code: {info.get('reply_code')}")
        logging.warning(f"  Reply text: {info.get('reply_text')}")
        # Could send to dead letter queue, alert, etc.

    handler.configure_unroutable(
        policy="return",
        alternate_exchange=None,
        on_unroutable="callback",
        unroutable_sink=None,
        on_unroutable_callback=on_unroutable
    )

    client = EventBusClient(
        exchange_handler=handler,
        serializer=serializer,
        host="localhost",
        port=5672
    )
    client.start_background_loop()
    client.connect_sync()

    msg = TestMessage("This will trigger callback")
    logging.info(f"Sending: {msg}")
    client.send_sync("unsubscribed.topic.callback", msg)

    await asyncio.sleep(2)
    logging.info(f"Total unroutable messages handled: {unroutable_count[0]}")

    client.close_sync()


# =============================================================================
# Policy 5: ALTERNATE-EXCHANGE - Route to alternate exchange
# =============================================================================

async def demo_alternate_exchange(config_path: str):
    """
    ALTERNATE-EXCHANGE policy: Route unroutable messages to an alternate exchange.:

    This creates:
    1. Main exchange with alternate-exchange argument
    2. Alternate exchange (fanout type)
    3. Durable queue bound to alternate exchange

    Unroutable messages go to the alternate exchange -> queue for later processing.
    """
    logging.info("\n=== Policy: ALTERNATE-EXCHANGE ===")
    logging.info("Unroutable messages will be routed to alternate exchange.")

    serializer = PickleSerializer()
    handler = TopicExchangeHandler(name="demo.main", serializer=serializer)

    handler.configure_unroutable(
        policy="alternate-exchange",
        alternate_exchange="demo.main.ae",  # Alternate exchange name
        on_unroutable="log",  # Also log when detected
        unroutable_sink=None,
        on_unroutable_callback=None
    )

    client = EventBusClient(
        exchange_handler=handler,
        serializer=serializer,
        host="localhost",
        port=5672
    )
    client.start_background_loop()
    client.connect_sync()

    # The setup creates:
    # - demo.main (topic exchange) with alternate-exchange=demo.main.ae
    # - demo.main.ae (fanout exchange)
    # - demo.main.unroutable (queue bound to demo.main.ae)

    logging.info("Exchange configured with alternate exchange.")
    logging.info("Unroutable messages will go to queue: demo.main.unroutable")

    # Send unroutable message
    msg = TestMessage("This goes to alternate exchange")
    logging.info(f"Sending to unsubscribed topic: {msg}")
    client.send_sync("unsubscribed.topic.ae", msg)

    logging.info("Message sent to alternate exchange queue")
    logging.info("Check RabbitMQ Management UI: Queues -> demo.main.unroutable")

    await asyncio.sleep(1)
    client.close_sync()


# =============================================================================
# Policy 6: RAISE - Raise exception for unroutable messages
# =============================================================================

async def demo_raise_policy(config_path: str):
    """
RAISE policy: Raise an exception when message is unroutable.
Use with caution - can disrupt message flow.
    """
    logging.info("\n=== Policy: RAISE ===")
    logging.info("Exception will be raised for unroutable messages.")

    serializer = PickleSerializer()
    handler = TopicExchangeHandler(name="demo.raise", serializer=serializer)

    handler.configure_unroutable(
        policy="return",
        alternate_exchange=None,
        on_unroutable="raise",  # Will raise RuntimeError
        unroutable_sink=None,
        on_unroutable_callback=None
    )

    client = EventBusClient(
        exchange_handler=handler,
        serializer=serializer,
        host="localhost",
        port=5672
    )
    client.start_background_loop()
    client.connect_sync()

    msg = TestMessage("This will raise an exception")
    logging.info(f"Sending: {msg}")

    try:
        client.send_sync("unsubscribed.topic.raise", msg)
        await asyncio.sleep(2)  # Wait for return
    except RuntimeError as e:
        logging.error(f"Exception raised (expected): {e}")

    client.close_sync()


# =============================================================================
# Demo: Using client's built-in unroutable cache
# =============================================================================

async def demo_client_unroutable_cache(config_path: str):
    """
Demonstrate using the EventBusClient's built-in unroutable cache.
    """
    logging.info("\n=== Using Client's Unroutable Cache ===")

    client = await EventBusClient.from_config(config_path)

    # Configure exchange handler to cache unroutables
    client.exchange_handler.configure_unroutable(
        policy="return",
        alternate_exchange=None,
        on_unroutable="cache",
        unroutable_sink=client._unroutable_cache,  # Use client's cache
        on_unroutable_callback=None
    )

    # Send unroutable messages
    for i in range(3):
        msg = TestMessage(f"Unroutable #{i}")
        await client.send(f"no.subscribers.{i}", msg)

    await asyncio.sleep(2)

    # Check cached unroutables
    unroutables = client.pop_unroutables()
    logging.info(f"Retrieved {len(unroutables)} unroutable messages:")
    for item in unroutables:
        logging.info(f"  - {item.get('routing_key')}")

    await client.close()


# =============================================================================
# Main
# =============================================================================

def main():
    config_path = "./config.jsonp"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    policies = {
        "drop": demo_drop_policy,
        "log": demo_log_policy,
        "cache": demo_cache_policy,
        "callback": demo_callback_policy,
        "alternate": demo_alternate_exchange,
        "raise": demo_raise_policy,
        "client-cache": demo_client_unroutable_cache,
    }

    if len(sys.argv) < 2:
        print("Alternate Exchange / Unroutable Message Handling Demo")
        print()
        print("Usage: python alternate_exchange_sample.py <policy>")
        print()
        print("Available policies:")
        print("  drop       - Silently discard unroutable messages (default RabbitMQ)")
        print("  log        - Log unroutable messages as warnings")
        print("  cache      - Store unroutable messages in a list")
        print("  callback   - Call custom function for each unroutable message")
        print("  alternate  - Route to alternate exchange (dead letter pattern)")
        print("  raise      - Raise exception for unroutable messages")
        print("  client-cache - Use EventBusClient's built-in cache")
        print()
        print("Example: python alternate_exchange_sample.py alternate")
        sys.exit(1)

    policy = sys.argv[1]

    if policy not in policies:
        print(f"Unknown policy: {policy}")
        print(f"Available: {list(policies.keys())}")
        sys.exit(1)

    asyncio.run(policies[policy](config_path))


if __name__ == "__main__":
    main()
