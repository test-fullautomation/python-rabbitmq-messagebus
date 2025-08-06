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

from testutils.messages.simple_test_message import SimpleTestMessage

async def test(oEventBusClient):
    """
    Test case EBC_0004: Validate multiple publishers can send to a single subscriber without conflict.
    This test verifies that multiple publishers can send messages to a single subscriber and all messages are received correctly.

    Args:
        oEventBusClient: The EventBusClient instance to test

    Returns:
        str: Result message indicating success or failure
    """
    received_messages = []
    routing_key = "test.multiple.publishers"
    publisher_count = 3
    test_message_contents = [f"Publisher {i} message" for i in range(1, publisher_count + 1)]

    async def message_callback(message):
        received_messages.append(message.get_value())

    try:
        await oEventBusClient.on(routing_key, SimpleTestMessage, message_callback)
        await asyncio.sleep(0.2)

        # Simulate multiple publishers sending messages
        for content in test_message_contents:
            test_message = SimpleTestMessage(content)
            await oEventBusClient.send(routing_key, test_message)
            await asyncio.sleep(0.05)

        await asyncio.sleep(0.8)  # Wait for all messages to be processed

        # Check that all expected messages were received (order doesn't matter for multiple publishers)
        if len(received_messages) != publisher_count:
            return f"Expected {publisher_count} messages, but received {len(received_messages)}: {received_messages}"

        # Check that all expected message contents are present
        for expected_content in test_message_contents:
            if expected_content not in received_messages:
                return f"Missing expected message: '{expected_content}'. Received: {received_messages}"

        # Check for unexpected messages
        for received_content in received_messages:
            if received_content not in test_message_contents:
                return f"Received unexpected message: '{received_content}'. Expected only: {test_message_contents}"

        # All messages received correctly (regardless of order)
        return f"All {publisher_count} messages received successfully: {sorted(received_messages)}"

    except Exception as e:
        return f"Error during multiple publisher test: {str(e)}"
