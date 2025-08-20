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
# EBC_0012.py
#
# Test case for EBC_0012: Send message with multi-level wildcard (#) in routing key to multiple subscribers
# using Reverse Topic Exchange (x-rtopic) where patterns and keys are reversed from standard topic exchange
#
# --------------------------------------------------------------------------------------------------------------

import asyncio
import os
import sys

# Add parent directory to path to access test modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from testutils.messages.simple_test_message import SimpleTestMessage
from testutils.polling_utils import wait_for_client_connected, poll_until_condition, PollingTimeoutError
from EventBusClient.event_bus_client import EventBusClient

async def test(config_folder_path):
    """
    Test case EBC_0012: Send message with multi-level wildcard (#) in routing key to multiple subscribers.

    TEST LOGIC FOR REVERSE TOPIC EXCHANGE (x-rtopic):
    In x-rtopic exchange, the matching logic is REVERSED:
    - Bindings (subscriber keys) are treated as LITERAL KEYS
    - Message routing keys are treated as PATTERNS

    1. Subscribers bind to SPECIFIC routing keys (no wildcards, treated as literal keys)
    2. Publisher sends with MULTI-LEVEL WILDCARD PATTERN containing hash (#)
    3. The publisher's pattern should match multiple subscriber keys with different depths

    Example:
    - Subscriber 1 binds to: "logs.error" (literal key - 2 levels)
    - Subscriber 2 binds to: "logs.warning.database" (literal key - 3 levels)
    - Subscriber 3 binds to: "logs.info.system.auth" (literal key - 4 levels)
    - Subscriber 4 binds to: "logs.debug.network.connection.timeout" (literal key - 5 levels)
    - Publisher sends pattern: "logs.#" (pattern that matches all subscribers with any levels)

    Args:
        config_folder_path: Path to the folder containing config files

    Returns:
        tuple: (result_message, oEventBusClient) for proper cleanup
    """

    oEventBusClient = None
    # Storage for received messages from each subscriber
    subscriber1_messages = []
    subscriber2_messages = []
    subscriber3_messages = []
    subscriber4_messages = []

    test_message_content = "Hello, Multi-Level Wildcard Subscribers!"

    # In x-rtopic exchange: subscribers bind to SPECIFIC keys (treated as literals)
    # These are the literal keys that subscribers will bind to - different depths to test # wildcard
    subscriber1_key = "logs.error"                                  # 2 levels
    subscriber2_key = "logs.warning.database"                       # 3 levels
    subscriber3_key = "logs.info.system.auth"                       # 4 levels
    subscriber4_key = "logs.debug.network.connection.timeout"       # 5 levels

    # Publisher uses MULTI-LEVEL WILDCARD PATTERN that should match all subscriber keys
    # In x-rtopic: the routing key is treated as a pattern
    # The # wildcard matches zero or more words, so "logs.#" matches anything starting with "logs."
    publisher_pattern = "logs.#"                                    # Pattern that matches all subscriber keys

    # Callback functions for each subscriber
    async def subscriber1_callback(message):
        """Callback for subscriber 1 with key: logs.error"""
        subscriber1_messages.append(message.get_value())

    async def subscriber2_callback(message):
        """Callback for subscriber 2 with key: logs.warning.database"""
        subscriber2_messages.append(message.get_value())

    async def subscriber3_callback(message):
        """Callback for subscriber 3 with key: logs.info.system.auth"""
        subscriber3_messages.append(message.get_value())

    async def subscriber4_callback(message):
        """Callback for subscriber 4 with key: logs.debug.network.connection.timeout"""
        subscriber4_messages.append(message.get_value())

    try:
        # Create EventBusClient from config file (uses XRTopicExchangeHandler)
        config_file = os.path.join(config_folder_path, 'config_rtopic.jsonp')
        oEventBusClient = await EventBusClient.from_config(config_file)

        # Set up multiple subscribers with SPECIFIC KEYS (treated as literals in x-rtopic)
        await oEventBusClient.on(subscriber1_key, SimpleTestMessage, subscriber1_callback)
        await oEventBusClient.on(subscriber2_key, SimpleTestMessage, subscriber2_callback)
        await oEventBusClient.on(subscriber3_key, SimpleTestMessage, subscriber3_callback)
        await oEventBusClient.on(subscriber4_key, SimpleTestMessage, subscriber4_callback)

        # Wait for client to be connected before sending message
        await wait_for_client_connected(oEventBusClient)

        # Send message using the MULTI-LEVEL WILDCARD PATTERN (treated as pattern in x-rtopic)
        test_message = SimpleTestMessage(test_message_content)
        await oEventBusClient.send(publisher_pattern, test_message)

        # Wait for messages to be processed by all subscribers
        def all_subscribers_received_message():
            return (len(subscriber1_messages) >= 1 and
                   len(subscriber2_messages) >= 1 and
                   len(subscriber3_messages) >= 1 and
                   len(subscriber4_messages) >= 1)

        try:
            await poll_until_condition(all_subscribers_received_message, timeout_seconds=10.0, poll_interval=0.2)
        except PollingTimeoutError:
            result = f"Not all subscribers received message within timeout. Sub1: {len(subscriber1_messages)}, Sub2: {len(subscriber2_messages)}, Sub3: {len(subscriber3_messages)}, Sub4: {len(subscriber4_messages)}"
            return result, oEventBusClient

        # Verify all subscribers received the correct message through reverse topic matching with multi-level wildcard
        if (len(subscriber1_messages) == 1 and subscriber1_messages[0] == test_message_content and
            len(subscriber2_messages) == 1 and subscriber2_messages[0] == test_message_content and
            len(subscriber3_messages) == 1 and subscriber3_messages[0] == test_message_content and
            len(subscriber4_messages) == 1 and subscriber4_messages[0] == test_message_content):

            result = f"All 4 subscribers received message using multi-level wildcard pattern: {test_message_content}"
            return result, oEventBusClient
        else:
            # Detailed error reporting for debugging
            error_details = []
            if len(subscriber1_messages) != 1 or (subscriber1_messages and subscriber1_messages[0] != test_message_content):
                error_details.append(f"Subscriber 1 key '{subscriber1_key}' failed: expected 1 message '{test_message_content}', got {len(subscriber1_messages)} messages {subscriber1_messages}")

            if len(subscriber2_messages) != 1 or (subscriber2_messages and subscriber2_messages[0] != test_message_content):
                error_details.append(f"Subscriber 2 key '{subscriber2_key}' failed: expected 1 message '{test_message_content}', got {len(subscriber2_messages)} messages {subscriber2_messages}")

            if len(subscriber3_messages) != 1 or (subscriber3_messages and subscriber3_messages[0] != test_message_content):
                error_details.append(f"Subscriber 3 key '{subscriber3_key}' failed: expected 1 message '{test_message_content}', got {len(subscriber3_messages)} messages {subscriber3_messages}")

            if len(subscriber4_messages) != 1 or (subscriber4_messages and subscriber4_messages[0] != test_message_content):
                error_details.append(f"Subscriber 4 key '{subscriber4_key}' failed: expected 1 message '{test_message_content}', got {len(subscriber4_messages)} messages {subscriber4_messages}")

            result = f"Multi-level wildcard reverse topic exchange test failed: {'; '.join(error_details)}"
            return result, oEventBusClient

    except Exception as e:
        result = f"Error during multi-level wildcard reverse topic exchange test: {str(e)}"
        return result, oEventBusClient
