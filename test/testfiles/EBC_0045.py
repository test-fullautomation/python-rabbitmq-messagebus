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
# EBC_0045.py
#
# Test case for EBC_0045: Headers exchange message ordering
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
    Test case EBC_0045: Headers exchange message ordering.

    This test verifies that messages sent through HeadersExchangeHandler
    are received in the same order they were sent.

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

        # Subscribe with binding_headers
        await oEventBusClient.on(
            routing_key="",
            message_cls=SimpleTestMessage,
            callback=message_callback,
            binding_headers={"type": "ordered"},
            match_all=True
        )

        # Wait for client to be connected before sending messages
        await wait_for_client_connected(oEventBusClient)

        # Send multiple messages in order
        expected_order = [1, 2, 3, 4, 5]
        for i in expected_order:
            test_message = SimpleTestMessage(i)
            await oEventBusClient.send(
                routing_key="",
                message=test_message,
                headers={"type": "ordered", "sequence": str(i)}
            )

        # Wait for all messages to be processed
        try:
            await wait_for_messages(received_messages, expected_count=5, timeout_seconds=10.0)

            # Verify order
            if received_messages == expected_order:
                result = f"Messages received in correct order: {received_messages}"
            else:
                result = f"Order mismatch: expected {expected_order}, got {received_messages}"
        except PollingTimeoutError:
            result = f"Timeout: only received {len(received_messages)} of 5 messages"

        return result, oEventBusClient

    except Exception as e:
        print(e)
        result = f"Error during message ordering test: {str(e)}"
        return result, oEventBusClient
