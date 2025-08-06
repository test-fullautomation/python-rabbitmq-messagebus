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
# EBC_0003.py
#
# Test case for EBC_0003: Test one publisher delivering messages to multiple subscribers using the same routing key
#
# --------------------------------------------------------------------------------------------------------------

import asyncio

from testutils.messages.simple_test_message import SimpleTestMessage

async def test(oEventBusClient):
    """
    Test case EBC_0003: Test one publisher delivering messages to multiple subscribers using the same routing key.
    This test verifies that a single publisher can broadcast messages to multiple subscribers
    using the same routing key.

    Args:
        oEventBusClient: The EventBusClient instance to test

    Returns:
        str: Result message indicating success or failure
    """

    # Track messages received by each subscriber
    subscriber1_messages = []
    subscriber2_messages = []
    subscriber3_messages = []

    test_message_content = "Hello, Multiple Subscribers!"
    routing_key = "test.broadcast.routing"
    expected_subscriber_count = 3

    async def subscriber1_callback(message):
        """Callback function for subscriber 1."""
        subscriber1_messages.append(message.get_value())

    async def subscriber2_callback(message):
        """Callback function for subscriber 2."""
        subscriber2_messages.append(message.get_value())

    async def subscriber3_callback(message):
        """Callback function for subscriber 3."""
        subscriber3_messages.append(message.get_value())

    try:
        await oEventBusClient.on(routing_key, SimpleTestMessage, subscriber1_callback)
        await oEventBusClient.on(routing_key, SimpleTestMessage, subscriber2_callback)
        await oEventBusClient.on(routing_key, SimpleTestMessage, subscriber3_callback)

        # Give subscribers a moment to be ready
        await asyncio.sleep(0.2)

        test_message = SimpleTestMessage(test_message_content)
        await oEventBusClient.send(routing_key, test_message)

        # Wait for message to be processed by all subscribers
        await asyncio.sleep(0.8)

        # Verify that all subscribers received the message
        all_messages = [subscriber1_messages, subscriber2_messages, subscriber3_messages]
        successful_subscribers = 0

        for i, messages in enumerate(all_messages, 1):
            if len(messages) == 1 and messages[0] == test_message_content:
                successful_subscribers += 1
            elif len(messages) == 0:
                return f"Subscriber {i} did not receive any message"
            elif len(messages) > 1:
                return f"Subscriber {i} received multiple messages: {messages}"
            else:
                return f"Subscriber {i} received unexpected message: {messages[0]}"

        if successful_subscribers == expected_subscriber_count:
            return f"All {expected_subscriber_count} subscribers received message: {test_message_content}"
        else:
            return f"Only {successful_subscribers}/{expected_subscriber_count} subscribers received the message correctly"

    except Exception as e:
        return f"Error during multiple subscriber test: {str(e)}"
