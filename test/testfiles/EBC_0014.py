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
# EBC_0014.py
#
# Test case for EBC_0014: Test message order preservation in x-rtopic exchange
# using Reverse Topic Exchange (x-rtopic) where patterns and keys are reversed from standard topic exchange
#
# --------------------------------------------------------------------------------------------------------------

import asyncio
import os
import sys

# Add parent directory to path to access test modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from testutils.messages.simple_test_message import SimpleTestMessage
from testutils.polling_utils import wait_for_client_connected, wait_for_message_sequence, PollingTimeoutError
from EventBusClient.event_bus_client import EventBusClient

async def test(config_folder_path):
    """
    Test case EBC_0014: Test message order preservation in x-rtopic exchange.

    TEST LOGIC FOR REVERSE TOPIC EXCHANGE (x-rtopic):
    In x-rtopic exchange, the matching logic is REVERSED:
    - Bindings (subscriber keys) are treated as LITERAL KEYS
    - Message routing keys are treated as PATTERNS

    This test demonstrates MESSAGE ORDER PRESERVATION in x-rtopic exchange:
    1. Subscriber binds to a SPECIFIC routing key (literal key)
    2. Publisher sends multiple messages with a PATTERN that matches the subscriber's literal key
    3. The subscriber should receive all messages in the exact order they were sent

    Example Setup:
    - Subscriber binds to literal key: "order.test.messages"
    - Publisher sends with pattern: "order.*.messages" (matches the subscriber's key)
    - Messages sent in sequence: [1, 2, 3, 4, 5]
    - Expected result: Messages received in same order [1, 2, 3, 4, 5]

    Args:
        config_folder_path: Path to the folder containing config files

    Returns:
        tuple: (result_message, oEventBusClient) for proper cleanup
    """

    oEventBusClient = None
    received_messages = []

    # In x-rtopic exchange: subscriber binds to SPECIFIC key (treated as literal)
    subscriber_literal_key = "order.test.messages"

    # Publisher uses PATTERN that should match the subscriber's literal key
    # In x-rtopic: the routing key is treated as a pattern that should match the subscriber's binding
    publisher_pattern = "order.*.messages"  # Pattern that matches "order.test.messages"

    test_message_count = 5

    async def message_callback(message):
        """Callback function to handle received messages and track order."""
        received_messages.append(message.get_value())

    try:
        # Create EventBusClient from x-rtopic config file
        config_file = os.path.join(config_folder_path, 'config_rtopic.jsonp')
        oEventBusClient = await EventBusClient.from_config(config_file)

        # Subscribe to literal key (in x-rtopic, this is treated as a literal binding)
        await oEventBusClient.on(subscriber_literal_key, SimpleTestMessage, message_callback)

        # Wait for client to be connected before sending messages
        await wait_for_client_connected(oEventBusClient)

        # Send multiple messages in sequence using pattern that matches subscriber's literal key
        expected_order = []
        for i in range(1, test_message_count + 1):
            test_message = SimpleTestMessage(i)
            # In x-rtopic: routing key is pattern, subscriber binding is literal
            # Pattern "order.*.messages" should match literal binding "order.test.messages"
            await oEventBusClient.send(publisher_pattern, test_message)
            expected_order.append(i)
            # Small delay to ensure ordering
            await asyncio.sleep(0.01)

        # Wait for messages to be received in correct sequence using polling utility
        try:
            await wait_for_message_sequence(received_messages, expected_order, timeout_seconds=10.0)
            result = f"Messages received in correct order using x-rtopic exchange: {received_messages}"
        except PollingTimeoutError as e:
            if len(received_messages) != test_message_count:
                result = f"Expected {test_message_count} messages, but received {len(received_messages)}: {received_messages}. " \
                        f"Pattern '{publisher_pattern}' may not match literal key '{subscriber_literal_key}' in x-rtopic exchange."
            else:
                result = f"Messages received in wrong order using x-rtopic exchange. Expected: {expected_order}, Got: {received_messages}"

        return result, oEventBusClient

    except Exception as e:
        result = f"Error during x-rtopic message ordering test: {str(e)}"
        return result, oEventBusClient
