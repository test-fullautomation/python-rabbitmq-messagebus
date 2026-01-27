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
# File: wait_mode_sample.py
#
# Initially created by Claude Code / January 2026.
#
# Description:
#
#   Demonstrates the use of wait_for_one and wait_for_many with different WaitMode
#   options for synchronizing message consumption.
#
# Usage:
#   Terminal 1: python wait_mode_sample.py consumer
#   Terminal 2: python wait_mode_sample.py producer
#
# *******************************************************************************
import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from EventBusClient.event_bus_client import EventBusClient
from EventBusClient.message.base_message import BaseMessage
from EventBusClient.wait_mode import WaitMode


class OrderMessage(BaseMessage):
    """Message representing an order with a sequence number."""
    def __init__(self, order_id: int = None, status: str = None):
        super().__init__()
        self.order_id = order_id
        self.status = status

    @classmethod
    def from_data(cls, data):
        return cls(order_id=data.get("order_id"), status=data.get("status"))

    def get_value(self):
        return self

    def __eq__(self, other):
        if isinstance(other, OrderMessage):
            return self.order_id == other.order_id and self.status == other.status
        return False

    def __repr__(self):
        return f"OrderMessage(order_id={self.order_id}, status={self.status!r})"


async def producer(config_path: str):
    """Send a sequence of order messages."""
    logging.info("Producer: Starting")
    client = await EventBusClient.from_config(config_path)

    # Send messages in a specific order
    orders = [
        OrderMessage(1, "created"),
        OrderMessage(2, "created"),
        OrderMessage(1, "processing"),
        OrderMessage(3, "created"),
        OrderMessage(2, "processing"),
        OrderMessage(1, "completed"),
        OrderMessage(2, "completed"),
        OrderMessage(3, "processing"),
        OrderMessage(3, "completed"),
    ]

    for order in orders:
        logging.info(f"Producer: Sending {order}")
        await client.send("orders.events", order)
        await asyncio.sleep(0.5)

    logging.info("Producer: Done sending messages")
    await client.close()


async def consumer_wait_for_one(config_path: str):
    """Demonstrate wait_for_one - wait for a specific message."""
    logging.info("Consumer: Starting wait_for_one demo")
    client = await EventBusClient.from_config(config_path)

    # Subscribe and get cache
    cache = await client.on("orders.events", OrderMessage, cache_size=100)
    logging.info("Consumer: Subscribed to orders.events")

    # Wait for a specific message
    target = OrderMessage(1, "completed")
    logging.info(f"Consumer: Waiting for {target}")

    try:
        found = cache.wait_for_one(target, timeout=30.0)
        if found:
            logging.info(f"Consumer: Found target message!")
        else:
            logging.info("Consumer: Target message not found within timeout")
    except TimeoutError:
        logging.info("Consumer: Timeout waiting for message")

    await client.close()


async def consumer_wait_for_many_ordered(config_path: str):
    """Demonstrate wait_for_many with ALL_IN_GIVEN_ORDER mode."""
    logging.info("Consumer: Starting wait_for_many (ordered) demo")
    client = await EventBusClient.from_config(config_path)

    cache = await client.on("orders.events", OrderMessage, cache_size=100)
    logging.info("Consumer: Subscribed to orders.events")

    # Wait for messages in specific order
    targets = [
        OrderMessage(1, "created"),
        OrderMessage(1, "processing"),
        OrderMessage(1, "completed"),
    ]
    logging.info(f"Consumer: Waiting for order 1 lifecycle in sequence...")

    try:
        result = cache.wait_for_many(targets, mode=WaitMode.ALL_IN_GIVEN_ORDER, timeout=30.0)
        logging.info(f"Consumer: Found messages at indices: {result}")
        if len(result) == len(targets):
            logging.info("Consumer: All messages found in correct order!")
        else:
            logging.info(f"Consumer: Only found {len(result)} of {len(targets)} messages")
    except TimeoutError:
        logging.info("Consumer: Timeout waiting for messages")

    await client.close()


async def consumer_wait_for_many_random(config_path: str):
    """Demonstrate wait_for_many with ALL_IN_RANDOM_ORDER mode."""
    logging.info("Consumer: Starting wait_for_many (random order) demo")
    client = await EventBusClient.from_config(config_path)

    cache = await client.on("orders.events", OrderMessage, cache_size=100)
    logging.info("Consumer: Subscribed to orders.events")

    # Wait for messages in any order
    targets = [
        OrderMessage(3, "completed"),
        OrderMessage(1, "completed"),
        OrderMessage(2, "completed"),
    ]
    logging.info(f"Consumer: Waiting for all completions (any order)...")

    try:
        result = cache.wait_for_many(targets, mode=WaitMode.ALL_IN_RANDOM_ORDER, timeout=30.0)
        logging.info(f"Consumer: Found messages at indices: {result}")
        if len(result) == len(targets):
            logging.info("Consumer: All completion messages found!")
    except TimeoutError:
        logging.info("Consumer: Timeout waiting for messages")

    await client.close()


async def consumer_wait_for_any(config_path: str):
    """Demonstrate wait_for_many with ANY_OF_GIVEN_MSGS mode."""
    logging.info("Consumer: Starting wait_for_many (any) demo")
    client = await EventBusClient.from_config(config_path)

    cache = await client.on("orders.events", OrderMessage, cache_size=100)
    logging.info("Consumer: Subscribed to orders.events")

    # Wait for any of these messages
    targets = [
        OrderMessage(1, "completed"),
        OrderMessage(2, "completed"),
        OrderMessage(3, "completed"),
    ]
    logging.info(f"Consumer: Waiting for ANY completion message...")

    try:
        result = cache.wait_for_many(targets, mode=WaitMode.ANY_OF_GIVEN_MSGS, timeout=30.0)
        logging.info(f"Consumer: Found first match at index: {result}")
        if result:
            logging.info(f"Consumer: First completion was order {targets[result[0]].order_id}")
    except TimeoutError:
        logging.info("Consumer: Timeout waiting for messages")

    await client.close()


def main():
    config_path = "../config/config.jsonp"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    if len(sys.argv) < 2:
        print("Usage: python wait_mode_sample.py <mode>")
        print("Modes:")
        print("  producer              - Send test messages")
        print("  wait_one              - Wait for a specific message")
        print("  wait_ordered          - Wait for messages in order")
        print("  wait_random           - Wait for messages in any order")
        print("  wait_any              - Wait for any matching message")
        sys.exit(1)

    mode = sys.argv[1]
    if mode == "producer":
        asyncio.run(producer(config_path))
    elif mode == "wait_one":
        asyncio.run(consumer_wait_for_one(config_path))
    elif mode == "wait_ordered":
        asyncio.run(consumer_wait_for_many_ordered(config_path))
    elif mode == "wait_random":
        asyncio.run(consumer_wait_for_many_random(config_path))
    elif mode == "wait_any":
        asyncio.run(consumer_wait_for_any(config_path))
    else:
        print(f"Unknown mode: {mode}")
        sys.exit(1)


if __name__ == "__main__":
    main()
