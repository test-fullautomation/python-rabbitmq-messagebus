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
# File: basic_async_producer_consumer_sample.py
#
# Initially created by Nguyen Huynh Tri Cuong (MS/EMC51) / August 2025.
#
# Description:
#
#   Basic example of an asynchronous producer and consumer using EventBusClient.
#   This script demonstrates how to set up a producer that sends messages
#   and a consumer that receives them using multiprocessing.
#
# History:
#
# 12.08.2025 / V 1.0.0 / Nguyen Huynh Tri Cuong
# - Initialize
#
# *******************************************************************************
import asyncio
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
        pass

    def get_value(self):
        return self


# Producer process function
async def producer_process(config_path):
    logging.info("Producer: Starting up")
    client = await EventBusClient.from_config(config_path)

    # Send 5 messages
    for i in range(5):
        msg = TestMessage(f"Message #{i} from producer")
        logging.info(f"Producer: Sending {msg.content}")
        await client.send("test.topic", msg)
        await asyncio.sleep(1)

    logging.info("Producer: Shutting down")
    await client.close()


# Consumer process function
async def consumer_process(config_path):
    logging.info("Consumer: Starting up")
    client = await EventBusClient.from_config(config_path)

    async def message_handler(message):
        logging.info(f"Consumer: Received {message.content}")

    # Subscribe to the test topic
    await client.on("test.topic", TestMessage, message_handler)
    logging.info("Consumer: Subscribed to test.topic")

    # Keep running to receive messages
    try:
        # Run for 10 seconds to receive all messages
        await asyncio.sleep(1000)
    except asyncio.CancelledError:
        logging.info("Consumer: CancelledError caught, shutting down")
    except Exception as e:
        logging.error(f"Consumer: Exception occurred - {e}")
        await client.close()
        raise e
    finally:
        logging.info("Consumer: Shutting down")
        await client.close()


def run_process(target_func, config_path):
    """Helper function to run an async function in a process"""
    asyncio.run(target_func(config_path))


def main():
    config_path = "../config/config.jsonp"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(process)d - %(levelname)s - %(message)s'
    )

    # Start the consumer process
    consumer = Process(target=run_process, args=(consumer_process, config_path))
    consumer.start()

    # Give consumer time to connect and set up subscription
    time.sleep(2)

    # Start the producer process
    producer = Process(target=run_process, args=(producer_process, config_path))
    producer.start()

    # Wait for both processes to finish
    producer.join()
    consumer.join()


if __name__ == "__main__":
    # Allow running as producer or consumer individually
    if len(sys.argv) > 1:
        if sys.argv[1] == "producer":
            logging.basicConfig(level=logging.INFO)
            asyncio.run(producer_process("../config/config.jsonp"))
        elif sys.argv[1] == "consumer":
            logging.basicConfig(level=logging.INFO)
            asyncio.run(consumer_process("../config/config.jsonp"))
    else:
        print("USAGE: python basic_async_producer_consumer_sample.py [producer|consumer]", file=sys.stderr)
        sys.exit(1)