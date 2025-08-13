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
# EBC_0002.py
#
# Test case for EBC_0002: Ensure messages arrive in same order they are sent
#
# --------------------------------------------------------------------------------------------------------------

import asyncio
import sys
import os

# Add parent directory to path to access test modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from testutils.messages.simple_test_message import SimpleTestMessage
from testutils.polling_utils import wait_for_message_sequence, wait_for_client_connected, PollingTimeoutError
from EventBusClient.event_bus_client import EventBusClient

async def test(config_folder_path):
    """
    Test case EBC_0002: Ensure messages arrive in same order they are sent.
    This test verifies message sequencing guarantee where applicable.

    Args:
        config_folder_path: Path to the folder containing config files

    Returns:
        tuple: (result_message, oEventBusClient) for proper cleanup
    """

    oEventBusClient = None
    received_messages = []
    routing_key = "test.ordering.messages"
    test_message_count = 5

    async def message_callback(message):
        """Callback function to handle received messages and track order."""
        received_messages.append(message.get_value())

    try:
        # Create EventBusClient from config file
        config_file = os.path.join(config_folder_path, 'config.jsonp')
        oEventBusClient = await EventBusClient.from_config(config_file)

        await oEventBusClient.on(routing_key, SimpleTestMessage, message_callback)

        # Wait for client to be connected before sending messages
        await wait_for_client_connected(oEventBusClient)

        # Send multiple messages in sequence
        expected_order = []
        for i in range(1, test_message_count + 1):
            test_message = SimpleTestMessage(i)
            await oEventBusClient.send(routing_key, test_message)
            expected_order.append(i)
            await asyncio.sleep(0.01)

        # Wait for messages to be received in correct sequence using polling utility
        try:
            await wait_for_message_sequence(received_messages, expected_order, timeout_seconds=5.0)
            result = f"Messages received in correct order: {received_messages}"
        except PollingTimeoutError as e:
            if len(received_messages) != test_message_count:
                result = f"Expected {test_message_count} messages, but received {len(received_messages)}: {received_messages}"
            else:
                result = f"Messages received in wrong order. Expected: {expected_order}, Got: {received_messages}"

        return result, oEventBusClient

    except Exception as e:
        result = f"Error during message ordering test: {str(e)}"
        return result, oEventBusClient