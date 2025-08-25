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
# File: basic_sync_producer_consumer_sample.py
#
# Initially created by Nguyen Huynh Tri Cuong (MS/EMC51) / August 2025.
#
# Description:
#
#   This script demonstrates a basic synchronous producer-consumer pattern using the EventBusClient library.
#
# History:
#
# 12.08.2025 / V 1.0.0 / Nguyen Huynh Tri Cuong
# - Initialize
#
# *******************************************************************************
import logging
import sys
import time
from multiprocessing import Process

from EventBusClient.event_bus_client import EventBusClient
from EventBusClient.message.base_message import BaseMessage

# Simple message class for our test
class TestMessage(BaseMessage):
    def __init__(self, content=None):
        super().__init__()
        self.content = content

    @classmethod
    def from_data(cls, data):
        # Depending on your serializer, this may not be needed
        return cls(content=data.get("content"))

    def get_value(self):
        return self


# Producer process (SYNC)
def producer_process(config_path: str):
    logging.info("Producer: Starting up")
    # Create client from config (initialize configuration). Connect in sync mode.
    client = EventBusClient.from_config_sync(config_path, start_connection=False)
    client.connect_sync()  # host/port/exchange are loaded from config if desired

    # Send 5 messages (blocking)
    for i in range(5):
        msg = TestMessage(f"Message #{i} from producer")
        logging.info(f"Producer: Sending {msg.content}")
        client.send_sync("test.topic", msg)
        time.sleep(1)

    logging.info("Producer: Shutting down")
    client.close_sync()


# Consumer process (SYNC)
def consumer_process(config_path: str):
    logging.info("Consumer: Starting up")
    client = EventBusClient.from_config_sync(config_path, start_connection=False)
    client.connect_sync()

    # Subscribe (blocking) -> receive cache for synchronous reading
    cache = client.on_sync("ipc.test.topic.test_zone.test_alias", TestMessage, cache_size=200)
    logging.info("Consumer: Subscribed to test.topic")

    received = 0
    try:
        end_time = time.time() + 15
        while received < 5 and time.time() < end_time:
            try:
                msg = cache.get(timeout=3.0)
                logging.info(f"Consumer: Received {msg.content}")
                received += 1
            except TimeoutError:
                logging.info("Consumer: waiting...")
    finally:
        logging.info("Consumer: Shutting down")
        client.close_sync()

def main():
    config_path = "../config/config.jsonp"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(process)d - %(levelname)s - %(message)s"
    )

    # Start the consumer process
    consumer = Process(target=consumer_process, args=(config_path,))
    consumer.start()

    # Give consumer time to connect and set up subscription
    time.sleep(2)

    # Start the producer process
    producer = Process(target=producer_process, args=(config_path,))
    producer.start()

    # Wait for both processes to finish
    producer.join()
    consumer.join()


if __name__ == "__main__":
    # Allow running as producer or consumer individually
    if len(sys.argv) > 1:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(process)d - %(levelname)s - %(message)s")
        if sys.argv[1] == "producer":
            producer_process("../config/config.jsonp")
        elif sys.argv[1] == "consumer":
            consumer_process("../config/config.jsonp")
        else:
            print("Usage: script.py [producer|consumer]")
    else:
        # Run both processes
        main()
