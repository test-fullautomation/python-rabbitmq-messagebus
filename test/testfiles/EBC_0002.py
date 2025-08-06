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

from testutils.messages.simple_test_message import SimpleTestMessage

async def test(oEventBusClient):
    """
    Test case EBC_0002: Ensure messages arrive in same order they are sent.
    This test verifies message sequencing guarantee where applicable.

    Args:
        oEventBusClient: The EventBusClient instance to test

    Returns:
        str: Result message indicating success or failure with message order verification
    """

    received_messages = []
    routing_key = "test.ordering.messages"
    test_message_count = 5

    async def message_callback(message):
        """Callback function to handle received messages and track order."""
        received_messages.append(message.get_value())

    try:
        await oEventBusClient.on(routing_key, SimpleTestMessage, message_callback)

        # Give subscriber a moment to be ready
        await asyncio.sleep(0.1)

        # Send multiple messages in sequence
        for i in range(1, test_message_count + 1):
            test_message = SimpleTestMessage(i)
            await oEventBusClient.send(routing_key, test_message)
            await asyncio.sleep(0.01)

        # Wait for all messages to be processed
        await asyncio.sleep(1.0)

        # Check if all messages were received in the correct order
        expected_order = list(range(1, test_message_count + 1))

        if len(received_messages) != test_message_count:
            return f"Expected {test_message_count} messages, but received {len(received_messages)}: {received_messages}"

        if received_messages == expected_order:
            return f"Messages received in correct order: {received_messages}"
        else:
            return f"Messages received in wrong order. Expected: {expected_order}, Got: {received_messages}"

    except Exception as e:
        return f"Error during message ordering test: {str(e)}"