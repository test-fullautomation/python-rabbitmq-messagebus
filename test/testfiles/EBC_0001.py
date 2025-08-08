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
# EBC_0001.py
#
# Test case for EBC_0001: Send message from one publisher to one specific subscriber and confirm receipt
#
# --------------------------------------------------------------------------------------------------------------

import asyncio
import os
import sys

# Add parent directory to path to access test modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from testutils.messages.simple_test_message import SimpleTestMessage
from EventBusClient.event_bus_client import EventBusClient

async def test(config_folder_path):
    """
    Test case EBC_0001: Send message from one publisher to one specific subscriber and confirm receipt.
    This test verifies point-to-point message flow functions as expected.

    Args:
        config_folder_path: Path to the folder containing config files

    Returns:
        tuple: (result_message, oEventBusClient) for proper cleanup
    """

    oEventBusClient = None
    received_messages = []
    test_message_content = "Hello, World!"
    routing_key = "test.message.routing"

    async def message_callback(message):
        """Callback function to handle received messages."""
        received_messages.append(message.get_value())

    try:
        # Create EventBusClient from config file
        config_file = os.path.join(config_folder_path, 'config.jsonp')
        oEventBusClient = await EventBusClient.from_config(config_file)
        await oEventBusClient.on(routing_key, SimpleTestMessage, message_callback)

        # Give subscriber a moment to be ready
        await asyncio.sleep(0.1)

        test_message = SimpleTestMessage(test_message_content)
        await oEventBusClient.send(routing_key, test_message)

        # Wait for message to be processed
        await asyncio.sleep(0.5)

        # Check if message was received
        if len(received_messages) == 1 and received_messages[0] == test_message_content:
            result = f"Message received: {received_messages[0]}"
        elif len(received_messages) == 0:
            result = "No message received"
        else:
            result = f"Unexpected message received: {received_messages}"

        return result, oEventBusClient

    except Exception as e:
        print(e)
        result = f"Error during message flow test: {str(e)}"
        return result, oEventBusClient