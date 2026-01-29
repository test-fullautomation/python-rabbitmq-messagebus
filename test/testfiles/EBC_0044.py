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
# EBC_0044.py
#
# Test case for EBC_0044: Headers exchange with multiple subscribers
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
    Test case EBC_0044: Headers exchange with multiple subscribers.

    This test verifies that HeadersExchangeHandler correctly delivers messages
    to multiple subscribers based on their individual header binding criteria.

    Args:
        config_folder_path: Path to the folder containing config files

    Returns:
        tuple: (result_message, oEventBusClient) for proper cleanup
    """

    oEventBusClient = None
    subscriber1_messages = []  # format=pdf AND department=engineering
    subscriber2_messages = []  # format=pdf OR priority=high

    async def subscriber1_callback(message, headers):
        """Callback for subscriber 1 (AND logic)."""
        subscriber1_messages.append(message.get_value())

    async def subscriber2_callback(message, headers):
        """Callback for subscriber 2 (OR logic)."""
        subscriber2_messages.append(message.get_value())

    try:
        # Create EventBusClient from config file
        config_file = os.path.join(config_folder_path, 'config_headers.jsonp')
        oEventBusClient = await EventBusClient.from_config(config_file)

        # Subscriber 1: match_all=True (AND logic)
        await oEventBusClient.on(
            routing_key="",
            message_cls=SimpleTestMessage,
            callback=subscriber1_callback,
            binding_headers={"format": "pdf", "department": "engineering"},
            match_all=True
        )

        # Subscriber 2: match_all=False (OR logic)
        await oEventBusClient.on(
            routing_key="",
            message_cls=SimpleTestMessage,
            callback=subscriber2_callback,
            binding_headers={"format": "pdf", "priority": "high"},
            match_all=False
        )

        # Wait for client to be connected before sending messages
        await wait_for_client_connected(oEventBusClient)

        # Send message that matches BOTH subscribers
        # (has format=pdf AND department=engineering, also matches format=pdf in OR)
        msg1 = SimpleTestMessage("Engineering PDF")
        await oEventBusClient.send(
            routing_key="",
            message=msg1,
            headers={"format": "pdf", "department": "engineering"}
        )

        # Small delay to ensure message is processed
        await asyncio.sleep(0.5)

        # Send message that matches ONLY subscriber 2 (has priority=high, but not format=pdf+dept=engineering)
        msg2 = SimpleTestMessage("High Priority Doc")
        await oEventBusClient.send(
            routing_key="",
            message=msg2,
            headers={"format": "docx", "department": "marketing", "priority": "high"}
        )

        # Wait for messages to be processed
        try:
            await wait_for_messages(subscriber1_messages, expected_count=1, timeout_seconds=5.0)
            await wait_for_messages(subscriber2_messages, expected_count=2, timeout_seconds=5.0)
            result = f"Multiple subscribers test passed: Subscriber1={len(subscriber1_messages)} msgs, Subscriber2={len(subscriber2_messages)} msgs"
        except PollingTimeoutError:
            result = f"Partial delivery: Subscriber1={len(subscriber1_messages)} msgs, Subscriber2={len(subscriber2_messages)} msgs"

        return result, oEventBusClient

    except Exception as e:
        print(e)
        result = f"Error during multiple subscribers test: {str(e)}"
        return result, oEventBusClient
