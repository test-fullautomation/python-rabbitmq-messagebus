# **************************************************************************************************************
#
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
#
# **************************************************************************************************************
#
# EBC_0003.py
#
# Test case for EBC_0003: Test one publisher delivering messages to multiple subscribers using the same routing key
#
# --------------------------------------------------------------------------------------------------------------

import asyncio
import os
import sys

# Add parent directory to path to access test modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from testutils.messages.simple_test_message import SimpleTestMessage
from testutils.polling_utils import poll_until_condition, wait_for_client_connected, PollingTimeoutError
from EventBusClient.event_bus_client import EventBusClient

async def test(config_folder_path):
    """
    Test case EBC_0003: Test one publisher delivering messages to multiple subscribers using the same routing key.
    This test verifies that a single publisher can broadcast messages to multiple subscribers
    using the same routing key.

    Args:
        config_folder_path: Path to the folder containing config files

    Returns:
        tuple: (result_message, oEventBusClient) for proper cleanup
    """

    oEventBusClient = None
    # Track messages received by each subscriber
    subscriber1_messages = []
    subscriber2_messages = []
    subscriber3_messages = []

    test_message_content = "Hello, Multiple Subscribers!"
    routing_key = "test.broadcast.routing"
    expected_subscriber_count = 3

    async def subscriber1_callback(message, headers):
        """Callback function for subscriber 1."""
        subscriber1_messages.append(message.get_value())

    async def subscriber2_callback(message, headers):
        """Callback function for subscriber 2."""
        subscriber2_messages.append(message.get_value())

    async def subscriber3_callback(message, headers):
        """Callback function for subscriber 3."""
        subscriber3_messages.append(message.get_value())

    try:
        # Create EventBusClient from config file
        config_file = os.path.join(config_folder_path, 'config_topic.jsonp')
        oEventBusClient = await EventBusClient.from_config(config_file)

        await oEventBusClient.on(routing_key, SimpleTestMessage, subscriber1_callback)
        await oEventBusClient.on(routing_key, SimpleTestMessage, subscriber2_callback)
        await oEventBusClient.on(routing_key, SimpleTestMessage, subscriber3_callback)

        # Wait for client to be connected before sending message
        await wait_for_client_connected(oEventBusClient)

        test_message = SimpleTestMessage(test_message_content)
        await oEventBusClient.send(routing_key, test_message)

        # Wait for message to be processed by all subscribers using polling
        def all_subscribers_received():
            all_lists = [subscriber1_messages, subscriber2_messages, subscriber3_messages]
            return all(len(msgs) >= 1 for msgs in all_lists)

        try:
            await poll_until_condition(all_subscribers_received, timeout_seconds=5.0, poll_interval=0.1)
        except PollingTimeoutError:
            result = "Not all subscribers received the message within timeout"
            return result, oEventBusClient

        # Verify that all subscribers received the message
        all_messages = [subscriber1_messages, subscriber2_messages, subscriber3_messages]
        successful_subscribers = 0

        for i, messages in enumerate(all_messages, 1):
            if len(messages) == 1 and messages[0] == test_message_content:
                successful_subscribers += 1
            elif len(messages) == 0:
                result = f"Subscriber {i} did not receive any message"
                return result, oEventBusClient
            elif len(messages) > 1:
                result = f"Subscriber {i} received multiple messages: {messages}"
                return result, oEventBusClient
            else:
                result = f"Subscriber {i} received unexpected message: {messages[0]}"
                return result, oEventBusClient

        if successful_subscribers == expected_subscriber_count:
            result = f"All {expected_subscriber_count} subscribers received message: {test_message_content}"
        else:
            result = f"Only {successful_subscribers}/{expected_subscriber_count} subscribers received the message correctly"

        return result, oEventBusClient

    except Exception as e:
        result = f"Error during multiple subscriber test: {str(e)}"
        return result, oEventBusClient
