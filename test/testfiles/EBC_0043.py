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
# EBC_0043.py
#
# Test case for EBC_0043: Headers exchange with match_all=False (OR logic)
#
# --------------------------------------------------------------------------------------------------------------

import asyncio
import os
import sys

# Add parent directory to path to access test modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from testutils.messages.simple_test_message import SimpleTestMessage
from testutils.polling_utils import wait_for_messages, wait_for_client_connected, PollingTimeoutError
from EventBusClient.event_bus_client import EventBusClient

async def test(config_folder_path):
    """
    Test case EBC_0043: Headers exchange with match_all=False (OR logic).

    This test verifies that when using HeadersExchangeHandler with match_all=False,
    messages are delivered to subscribers when ANY of the specified headers match.

    Args:
        config_folder_path: Path to the folder containing config files

    Returns:
        tuple: (result_message, oEventBusClient) for proper cleanup
    """

    oEventBusClient = None
    received_messages = []
    test_message_content = "Hello, OR Logic!"

    async def message_callback(message, headers):
        """Callback function to handle received messages."""
        received_messages.append(message.get_value())

    try:
        # Create EventBusClient from config file
        config_file = os.path.join(config_folder_path, 'config_headers.jsonp')
        oEventBusClient = await EventBusClient.from_config(config_file)

        # Subscribe with binding_headers using match_all=False (OR logic)
        # Message needs to have EITHER format=pdf OR priority=high to be received
        await oEventBusClient.on(
            routing_key="",  # Ignored in headers exchange
            message_cls=SimpleTestMessage,
            callback=message_callback,
            binding_headers={"format": "pdf", "priority": "high"},
            match_all=False
        )

        # Wait for client to be connected before sending message
        await wait_for_client_connected(oEventBusClient)

        # Send message with only one matching header (priority=high, no format=pdf)
        # This should still be received due to OR logic
        test_message = SimpleTestMessage(test_message_content)
        await oEventBusClient.send(
            routing_key="",
            message=test_message,
            headers={"format": "docx", "department": "marketing", "priority": "high"}
        )

        # Wait for message to be processed using polling utility
        try:
            await wait_for_messages(received_messages, expected_count=1, timeout_seconds=5.0)
            result = f"Message received with OR logic: {received_messages[0]}"
        except PollingTimeoutError:
            result = "No message received within timeout"

        return result, oEventBusClient

    except Exception as e:
        print(e)
        result = f"Error during headers exchange OR logic test: {str(e)}"
        return result, oEventBusClient
