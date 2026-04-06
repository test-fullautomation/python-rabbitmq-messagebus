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
# EBC_0047.py
#
# Test case for EBC_0047: Headers exchange partial match with AND logic should not deliver
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
    Test case EBC_0047: Headers exchange partial match with AND logic should not deliver.

    This test verifies that when using HeadersExchangeHandler with match_all=True,
    messages with only partial header matches are NOT delivered to subscribers.

    Args:
        config_folder_path: Path to the folder containing config files

    Returns:
        tuple: (result_message, oEventBusClient) for proper cleanup
    """

    oEventBusClient = None
    received_messages = []

    async def message_callback(message, headers):
        """Callback function to handle received messages."""
        received_messages.append(message.get_value())

    try:
        # Create EventBusClient from config file
        config_file = os.path.join(config_folder_path, 'config_headers.jsonp')
        oEventBusClient = await EventBusClient.from_config(config_file)

        # Subscribe with binding_headers using AND logic
        # Requires BOTH format=pdf AND department=engineering
        await oEventBusClient.on(
            routing_key="",
            message_cls=SimpleTestMessage,
            callback=message_callback,
            binding_headers={"format": "pdf", "department": "engineering"},
            match_all=True
        )

        # Wait for client to be connected before sending messages
        await wait_for_client_connected(oEventBusClient)

        # Send message with only ONE matching header (partial match)
        # Has format=pdf but department=marketing (not engineering)
        # This should NOT be delivered because AND logic requires ALL headers to match
        test_message = SimpleTestMessage("This should not be received due to partial match")
        await oEventBusClient.send(
            routing_key="",
            message=test_message,
            headers={"format": "pdf", "department": "marketing"}
        )

        # Wait a short time to ensure message would have been delivered if it matched
        try:
            await wait_for_messages(received_messages, expected_count=1, timeout_seconds=2.0)
            # If we get here, message was unexpectedly received
            result = f"Unexpected message received with partial match: {received_messages[0]}"
        except PollingTimeoutError:
            # This is the expected behavior - partial match should not deliver with AND logic
            result = "Partial match correctly not delivered with AND logic"

        return result, oEventBusClient

    except Exception as e:
        print(e)
        result = f"Error during partial match test: {str(e)}"
        return result, oEventBusClient
