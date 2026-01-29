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
# EBC_0046.py
#
# Test case for EBC_0046: Headers exchange with non-matching headers
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
    Test case EBC_0046: Headers exchange with non-matching headers.

    This test verifies that when using HeadersExchangeHandler, messages
    with non-matching headers are NOT delivered to subscribers.

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

        # Subscribe with binding_headers (format=pdf AND department=engineering)
        await oEventBusClient.on(
            routing_key="",
            message_cls=SimpleTestMessage,
            callback=message_callback,
            binding_headers={"format": "pdf", "department": "engineering"},
            match_all=True
        )

        # Wait for client to be connected before sending messages
        await wait_for_client_connected(oEventBusClient)

        # Send message with completely non-matching headers
        # This should NOT be delivered to the subscriber
        test_message = SimpleTestMessage("This should not be received")
        await oEventBusClient.send(
            routing_key="",
            message=test_message,
            headers={"format": "docx", "department": "marketing", "priority": "low"}
        )

        # Wait a short time to ensure message would have been delivered if it matched
        try:
            await wait_for_messages(received_messages, expected_count=1, timeout_seconds=2.0)
            # If we get here, message was unexpectedly received
            result = f"Unexpected message received: {received_messages[0]}"
        except PollingTimeoutError:
            # This is the expected behavior - no message should be received
            result = "Non-matching message correctly not delivered"

        return result, oEventBusClient

    except Exception as e:
        print(e)
        result = f"Error during non-matching headers test: {str(e)}"
        return result, oEventBusClient
