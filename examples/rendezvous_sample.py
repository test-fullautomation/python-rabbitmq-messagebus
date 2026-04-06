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
# File: rendezvous_sample.py
#
# Initially created by Claude Code / January 2026.
#
# Description:
#
#   Demonstrates the rendezvous pattern for coordinating multiple clients.
#   Uses wait_until_ready and announce_ready for synchronization.
#
# Usage:
#   Run in separate terminals:
#   Terminal 1: python rendezvous_sample.py coordinator
#   Terminal 2: python rendezvous_sample.py worker worker1
#   Terminal 3: python rendezvous_sample.py worker worker2
#
# *******************************************************************************
import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from EventBusClient.event_bus_client import EventBusClient
from EventBusClient.message.base_message import BaseMessage


class TaskMessage(BaseMessage):
    """Message representing a task to be processed."""
    def __init__(self, task_id: str = None, data: str = None):
        super().__init__()
        self.task_id = task_id
        self.data = data

    @classmethod
    def from_data(cls, data):
        return cls(task_id=data.get("task_id"), data=data.get("data"))

    def get_value(self):
        return self

    def __repr__(self):
        return f"TaskMessage(task_id={self.task_id!r}, data={self.data!r})"


class ResultMessage(BaseMessage):
    """Message representing a task result."""
    def __init__(self, task_id: str = None, result: str = None, worker: str = None):
        super().__init__()
        self.task_id = task_id
        self.result = result
        self.worker = worker

    @classmethod
    def from_data(cls, data):
        return cls(
            task_id=data.get("task_id"),
            result=data.get("result"),
            worker=data.get("worker")
        )

    def get_value(self):
        return self

    def __repr__(self):
        return f"ResultMessage(task_id={self.task_id!r}, worker={self.worker!r})"


async def coordinator(config_path: str):
    """
    Coordinator waits for workers to be ready, then distributes tasks.
    """
    logging.info("Coordinator: Starting")
    client = await EventBusClient.from_config(config_path)

    # Subscribe to results
    results_cache = await client.on("tasks.results", ResultMessage, cache_size=100)

    # Wait for 2 workers to be ready
    logging.info("Coordinator: Waiting for 2 workers to be ready...")
    requirements = {"worker": 2}

    ready = await client.wait_until_ready(requirements, timeout=60.0)
    if ready:
        logging.info("Coordinator: All workers are ready!")
    else:
        logging.error("Coordinator: Timeout waiting for workers")
        await client.close()
        return

    # Announce that coordinator is ready
    await client.announce_ready(["coordinator"])

    # Distribute tasks
    tasks = [
        TaskMessage("task-001", "Process item A"),
        TaskMessage("task-002", "Process item B"),
        TaskMessage("task-003", "Process item C"),
        TaskMessage("task-004", "Process item D"),
    ]

    logging.info("Coordinator: Distributing tasks...")
    for task in tasks:
        await client.send("tasks.queue", task)
        logging.info(f"Coordinator: Sent {task}")
        await asyncio.sleep(0.2)

    # Collect results
    logging.info("Coordinator: Waiting for results...")
    received = 0
    try:
        while received < len(tasks):
            result = results_cache.get(timeout=30.0)
            logging.info(f"Coordinator: Got result - {result}")
            received += 1
    except TimeoutError:
        logging.warning(f"Coordinator: Timeout, received {received}/{len(tasks)} results")

    logging.info("Coordinator: Done")
    await client.close()


async def worker(config_path: str, worker_name: str):
    """
    Worker announces readiness, waits for coordinator, then processes tasks.
    """
    logging.info(f"Worker [{worker_name}]: Starting")
    client = await EventBusClient.from_config(config_path)

    # Subscribe to task queue
    task_cache = await client.on("tasks.queue", TaskMessage, cache_size=100)

    # Announce that this worker is ready
    logging.info(f"Worker [{worker_name}]: Announcing ready")
    await client.announce_ready(["worker"])

    # Wait for coordinator to be ready
    logging.info(f"Worker [{worker_name}]: Waiting for coordinator...")
    requirements = {"coordinator": 1}
    ready = await client.wait_until_ready(requirements, timeout=60.0)

    if not ready:
        logging.error(f"Worker [{worker_name}]: Timeout waiting for coordinator")
        await client.close()
        return

    logging.info(f"Worker [{worker_name}]: Coordinator is ready, starting work")

    # Process tasks
    try:
        while True:
            try:
                task = task_cache.get(timeout=5.0)
                logging.info(f"Worker [{worker_name}]: Processing {task}")

                # Simulate work
                await asyncio.sleep(1.0)

                # Send result
                result = ResultMessage(
                    task_id=task.task_id,
                    result=f"Processed: {task.data}",
                    worker=worker_name
                )
                await client.send("tasks.results", result)
                logging.info(f"Worker [{worker_name}]: Sent result for {task.task_id}")

            except TimeoutError:
                logging.info(f"Worker [{worker_name}]: No more tasks, exiting")
                break
    finally:
        await client.close()


async def worker_sync(config_path: str, worker_name: str):
    """
    Synchronous worker example using sync API.
    """
    logging.info(f"Worker [{worker_name}]: Starting (sync mode)")
    client = EventBusClient.from_config_sync(config_path)
    client.connect_sync()

    # Subscribe to task queue
    task_cache = client.on_sync("tasks.queue", TaskMessage, cache_size=100)

    # Announce ready
    logging.info(f"Worker [{worker_name}]: Announcing ready")
    client.announce_ready_sync(["worker"])

    # Wait for coordinator
    logging.info(f"Worker [{worker_name}]: Waiting for coordinator...")
    ready = client.wait_until_ready_sync({"coordinator": 1}, timeout=60.0)

    if not ready:
        logging.error(f"Worker [{worker_name}]: Timeout waiting for coordinator")
        client.close_sync()
        return

    logging.info(f"Worker [{worker_name}]: Starting work")

    # Process tasks
    import time
    try:
        while True:
            try:
                task = task_cache.get(timeout=5.0)
                logging.info(f"Worker [{worker_name}]: Processing {task}")
                time.sleep(1.0)

                result = ResultMessage(
                    task_id=task.task_id,
                    result=f"Processed: {task.data}",
                    worker=worker_name
                )
                client.send_sync("tasks.results", result)
                logging.info(f"Worker [{worker_name}]: Sent result for {task.task_id}")
            except TimeoutError:
                logging.info(f"Worker [{worker_name}]: No more tasks, exiting")
                break
    finally:
        client.close_sync()


def main():
    config_path = "./config.jsonp"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python rendezvous_sample.py coordinator")
        print("  python rendezvous_sample.py worker <worker_name>")
        print("  python rendezvous_sample.py worker_sync <worker_name>")
        print()
        print("Example (run in separate terminals):")
        print("  Terminal 1: python rendezvous_sample.py coordinator")
        print("  Terminal 2: python rendezvous_sample.py worker worker1")
        print("  Terminal 3: python rendezvous_sample.py worker worker2")
        sys.exit(1)

    role = sys.argv[1]

    if role == "coordinator":
        asyncio.run(coordinator(config_path))
    elif role == "worker":
        worker_name = sys.argv[2] if len(sys.argv) > 2 else "worker-default"
        asyncio.run(worker(config_path, worker_name))
    elif role == "worker_sync":
        worker_name = sys.argv[2] if len(sys.argv) > 2 else "worker-default"
        worker_sync(config_path, worker_name)
    else:
        print(f"Unknown role: {role}")
        sys.exit(1)


if __name__ == "__main__":
    main()
