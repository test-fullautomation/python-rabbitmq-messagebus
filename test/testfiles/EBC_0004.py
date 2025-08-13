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
# EBC_0004.py
#
# Test case for EBC_0004: Validate multiple publishers can send to a single subscriber without conflict
#
# --------------------------------------------------------------------------------------------------------------

import asyncio
import os
import sys

# Add parent directory to path to access test modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from testutils.messages.simple_test_message import SimpleTestMessage
from testutils.polling_utils import wait_for_messages, PollingTimeoutError
from EventBusClient.event_bus_client import EventBusClient

async def test(config_folder_path):
    """
    Test case EBC_0004: Validate multiple publishers can send to a single subscriber without conflict.
    This test verifies that multiple publishers can send messages to a single subscriber and all messages are received correctly.

    Args:
        config_folder_path: Path to the folder containing config files

    Returns:
        tuple: (result_message, oEventBusClient) for proper cleanup
    """
    oEventBusClient = None
    received_messages = []
    routing_key = "test.multiple.publishers"
    publisher_count = 3
    test_message_contents = [f"Publisher {i} message" for i in range(1, publisher_count + 1)]

    async def message_callback(message):
        received_messages.append(message.get_value())

    try:
        # Create EventBusClient from config file
        config_file = os.path.join(config_folder_path, 'config.jsonp')
        oEventBusClient = await EventBusClient.from_config(config_file)

        await oEventBusClient.on(routing_key, SimpleTestMessage, message_callback)

        # Simulate multiple publishers sending messages
        for content in test_message_contents:
            test_message = SimpleTestMessage(content)
            await oEventBusClient.send(routing_key, test_message)
            await asyncio.sleep(0.05)

        try:
            await wait_for_messages(received_messages, expected_count=publisher_count, timeout_seconds=5.0)
        except PollingTimeoutError:
            result = f"Expected {publisher_count} messages, but only received {len(received_messages)} within timeout: {received_messages}"
            return result, oEventBusClient

        # Check that all expected message contents are present
        for expected_content in test_message_contents:
            if expected_content not in received_messages:
                result = f"Missing expected message: '{expected_content}'. Received: {received_messages}"
                return result, oEventBusClient

        # Check for unexpected messages
        for received_content in received_messages:
            if received_content not in test_message_contents:
                result = f"Received unexpected message: '{received_content}'. Expected only: {test_message_contents}"
                return result, oEventBusClient

        # All messages received correctly (regardless of order)
        result = f"All {publisher_count} messages received successfully: {sorted(received_messages)}"
        return result, oEventBusClient

    except Exception as e:
        result = f"Error during multiple publisher test: {str(e)}"
        return result, oEventBusClient
