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
# File: error_handling_sample.py
#
# Initially created by Claude Code / January 2026.
#
# Description:
#
#   Demonstrates error handling patterns including connection errors,
#   message handling errors, and graceful recovery.
#
# Usage:
#   python error_handling_sample.py
#
# *******************************************************************************
import asyncio
import logging
import sys
import os
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from EventBusClient.event_bus_client import EventBusClient
from EventBusClient.message.base_message import BaseMessage


class TaskMessage(BaseMessage):
    """Simple task message."""
    def __init__(self, task_id: str = None, should_fail: bool = False):
        super().__init__()
        self.task_id = task_id
        self.should_fail = should_fail

    @classmethod
    def from_data(cls, data):
        return cls(
            task_id=data.get("task_id"),
            should_fail=data.get("should_fail", False)
        )

    def get_value(self):
        return self

    def __repr__(self):
        return f"Task({self.task_id}, fail={self.should_fail})"


# =============================================================================
# Example 1: Connection error handling
# =============================================================================

async def demo_connection_errors():
    """Demonstrate handling connection errors."""
    logging.info("\n=== Demo 1: Connection Error Handling ===")

    # Try connecting to invalid host
    logging.info("Attempting to connect to invalid host...")
    try:
        client = await EventBusClient.from_config(
            config_source={
                "exchange_handler": "TopicExchangeHandler",
                "serializer": "PickleSerializer",
                "host": "invalid-host.local",
                "port": 5672,
            }
        )
    except Exception as e:
        logging.error(f"Connection failed (expected): {type(e).__name__}: {e}")

    # Try connecting to wrong port
    logging.info("\nAttempting to connect to wrong port...")
    try:
        client = await EventBusClient.from_config(
            config_source={
                "exchange_handler": "TopicExchangeHandler",
                "serializer": "PickleSerializer",
                "host": "localhost",
                "port": 9999,
            }
        )
    except Exception as e:
        logging.error(f"Connection failed (expected): {type(e).__name__}: {e}")


# =============================================================================
# Example 2: Handler error isolation
# =============================================================================

async def demo_handler_errors(config_path: str):
    """Demonstrate that handler errors don't crash the client."""
    logging.info("\n=== Demo 2: Handler Error Isolation ===")

    client = await EventBusClient.from_config(config_path)
    processed = []
    errors = []

    async def faulty_handler(msg: TaskMessage, headers: dict):
        """Handler that may raise exceptions."""
        if msg.should_fail:
            errors.append(msg.task_id)
            raise RuntimeError(f"Intentional failure for task {msg.task_id}")

        processed.append(msg.task_id)
        logging.info(f"Successfully processed: {msg}")

    await client.on("tasks.test", TaskMessage, faulty_handler)

    # Send mix of good and bad tasks
    tasks = [
        TaskMessage("task-1", should_fail=False),
        TaskMessage("task-2", should_fail=True),   # This will fail
        TaskMessage("task-3", should_fail=False),
        TaskMessage("task-4", should_fail=True),   # This will fail
        TaskMessage("task-5", should_fail=False),
    ]

    for task in tasks:
        await client.send("tasks.test", task)
        await asyncio.sleep(0.2)

    await asyncio.sleep(2)

    logging.info(f"Processed successfully: {processed}")
    logging.info(f"Failed (but client still running): {errors}")

    await client.close()


# =============================================================================
# Example 3: Graceful shutdown
# =============================================================================

async def demo_graceful_shutdown(config_path: str):
    """Demonstrate graceful shutdown with pending operations."""
    logging.info("\n=== Demo 3: Graceful Shutdown ===")

    client = await EventBusClient.from_config(config_path)
    pending_tasks = []

    async def slow_handler(msg: TaskMessage, headers: dict):
        """Handler that takes time to process."""
        logging.info(f"Starting to process {msg}")
        pending_tasks.append(msg.task_id)
        await asyncio.sleep(2)  # Simulate work
        pending_tasks.remove(msg.task_id)
        logging.info(f"Finished processing {msg}")

    await client.on("tasks.slow", TaskMessage, slow_handler)

    # Send tasks
    for i in range(3):
        task = TaskMessage(f"slow-task-{i}")
        await client.send("tasks.slow", task)

    # Wait a bit then start shutdown
    await asyncio.sleep(1)
    logging.info(f"Starting shutdown with {len(pending_tasks)} pending tasks...")

    # Graceful close
    await client.close()
    logging.info("Client closed")


# =============================================================================
# Example 4: Retry pattern
# =============================================================================

class RetryableClient:
    """Wrapper that adds retry logic to EventBusClient operations."""

    def __init__(self, client: EventBusClient, max_retries: int = 3, retry_delay: float = 1.0):
        self.client = client
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    async def send_with_retry(self, routing_key: str, message: BaseMessage, headers: dict = None):
        """Send message with automatic retry on failure."""
        last_error = None

        for attempt in range(self.max_retries):
            try:
                await self.client.send(routing_key, message, headers)
                logging.debug(f"Sent successfully on attempt {attempt + 1}")
                return True
            except Exception as e:
                last_error = e
                logging.warning(f"Send failed (attempt {attempt + 1}/{self.max_retries}): {e}")

                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))

        logging.error(f"All {self.max_retries} attempts failed: {last_error}")
        return False


async def demo_retry_pattern(config_path: str):
    """Demonstrate retry pattern for resilient messaging."""
    logging.info("\n=== Demo 4: Retry Pattern ===")

    client = await EventBusClient.from_config(config_path)
    retryable = RetryableClient(client, max_retries=3, retry_delay=0.5)

    # Normal send
    task = TaskMessage("retry-task-1")
    success = await retryable.send_with_retry("tasks.retry", task)
    logging.info(f"Send result: {success}")

    await client.close()


# =============================================================================
# Example 5: Dead letter handling
# =============================================================================

async def demo_dead_letter(config_path: str):
    """Demonstrate dead letter handling for failed messages."""
    logging.info("\n=== Demo 5: Dead Letter Pattern ===")

    client = await EventBusClient.from_config(config_path)
    dead_letters = []

    async def main_handler(msg: TaskMessage, headers: dict):
        """Main handler that may fail."""
        if msg.should_fail:
            raise RuntimeError(f"Processing failed for {msg.task_id}")
        logging.info(f"Processed: {msg}")

    async def dead_letter_handler(msg: TaskMessage, headers: dict):
        """Handler for failed messages."""
        dead_letters.append(msg)
        logging.warning(f"Dead letter received: {msg}")
        # Could store in database, send alert, etc.

    # Subscribe to main queue and dead letter queue
    await client.on("tasks.main", TaskMessage, main_handler)
    await client.on("tasks.deadletter", TaskMessage, dead_letter_handler)

    # Process with dead letter forwarding
    async def process_with_dlq(msg: TaskMessage):
        """Send to main queue, forward to DLQ on failure."""
        try:
            await client.send("tasks.main", msg)
        except Exception as e:
            logging.error(f"Failed to process, forwarding to DLQ: {e}")
            await client.send("tasks.deadletter", msg)

    # Send some tasks
    tasks = [
        TaskMessage("dlq-1", should_fail=False),
        TaskMessage("dlq-2", should_fail=True),
        TaskMessage("dlq-3", should_fail=False),
    ]

    for task in tasks:
        await process_with_dlq(task)
        await asyncio.sleep(0.3)

    await asyncio.sleep(2)
    logging.info(f"Dead letters collected: {[dl.task_id for dl in dead_letters]}")

    await client.close()


# =============================================================================
# Example 6: Timeout handling
# =============================================================================

async def demo_timeout_handling(config_path: str):
    """Demonstrate timeout handling in wait operations."""
    logging.info("\n=== Demo 6: Timeout Handling ===")

    client = await EventBusClient.from_config(config_path)

    cache = await client.on("tasks.timeout", TaskMessage, cache_size=100)

    # Try to wait for a message that never comes
    logging.info("Waiting for message with 3 second timeout...")
    start = asyncio.get_event_loop().time()

    try:
        msg = cache.get(timeout=3.0)
        logging.info(f"Got message: {msg}")
    except TimeoutError:
        elapsed = asyncio.get_event_loop().time() - start
        logging.info(f"Timeout after {elapsed:.1f}s (expected)")

    # With wait_for_one
    target = TaskMessage("nonexistent")
    logging.info(f"Waiting for specific message with 2 second timeout...")

    found = cache.wait_for_one(target, timeout=2.0)
    logging.info(f"wait_for_one returned: {found}")

    await client.close()


# =============================================================================
# Main
# =============================================================================

async def main(config_path: str):
    """Run all error handling demos."""

    # Demo 1: Connection errors
    await demo_connection_errors()

    # Demo 2: Handler error isolation
    await demo_handler_errors(config_path)

    # Demo 3: Graceful shutdown
    await demo_graceful_shutdown(config_path)

    # Demo 4: Retry pattern
    await demo_retry_pattern(config_path)

    # Demo 5: Dead letter handling
    await demo_dead_letter(config_path)

    # Demo 6: Timeout handling
    await demo_timeout_handling(config_path)

    logging.info("\n=== All demos complete ===")


if __name__ == "__main__":
    config_path = "../config/config.jsonp"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    if len(sys.argv) > 1:
        demo_name = sys.argv[1]
        demos = {
            "connection": demo_connection_errors,
            "handler": lambda: demo_handler_errors(config_path),
            "shutdown": lambda: demo_graceful_shutdown(config_path),
            "retry": lambda: demo_retry_pattern(config_path),
            "deadletter": lambda: demo_dead_letter(config_path),
            "timeout": lambda: demo_timeout_handling(config_path),
        }

        if demo_name in demos:
            asyncio.run(demos[demo_name]())
        else:
            print(f"Unknown demo: {demo_name}")
            print(f"Available: {list(demos.keys())}")
    else:
        asyncio.run(main(config_path))
