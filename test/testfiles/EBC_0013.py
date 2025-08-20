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
# EBC_0013.py
#
# Test case for EBC_0013: Test mixed wildcard patterns in single routing key
# using Reverse Topic Exchange (x-rtopic) where patterns and keys are reversed from standard topic exchange
#
# --------------------------------------------------------------------------------------------------------------

import os
import sys

# Add parent directory to path to access test modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from testutils.messages.simple_test_message import SimpleTestMessage
from testutils.polling_utils import wait_for_client_connected, poll_until_condition, PollingTimeoutError
from EventBusClient.event_bus_client import EventBusClient

async def test(config_folder_path):
    """
    Test case EBC_0013: Test mixed wildcard patterns in single routing key.

    TEST LOGIC FOR REVERSE TOPIC EXCHANGE (x-rtopic):
    In x-rtopic exchange, the matching logic is REVERSED:
    - Bindings (subscriber keys) are treated as LITERAL KEYS
    - Message routing keys are treated as PATTERNS

    This test demonstrates MIXED WILDCARD PATTERNS in a single routing key:
    1. Subscribers bind to SPECIFIC routing keys (no wildcards, treated as literal keys)
    2. Publisher sends with MIXED WILDCARD PATTERN containing both single asterisk (*) and hash (#)
    3. The publisher's pattern should match multiple subscriber keys with different structures

    Example Mixed Pattern: "events.*.system.#"
    - * matches exactly one word in the second position
    - # matches zero or more words from the fourth position onwards

    Subscriber keys that should match:
    - "events.user.system" (matches: events.*.system.#)
    - "events.admin.system.auth" (matches: events.*.system.#)
    - "events.guest.system.monitoring.alerts" (matches: events.*.system.#)
    - "events.service.system.health.check.status" (matches: events.*.system.#)
    - "events.api.system.performance" (matches: events.*.system.#)

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
    subscriber5_messages = []

    test_message_content = "Hello, Mixed Wildcard Subscribers!"

    # In x-rtopic exchange: subscribers bind to SPECIFIC keys (treated as literals)
    # These literal keys should all match the mixed wildcard pattern "events.*.system.#"
    subscriber1_key = "events.user.system"                              # Matches: events.user.system (minimal match for #)
    subscriber2_key = "events.admin.system.auth"                        # Matches: events.admin.system.auth
    subscriber3_key = "events.guest.system.monitoring.alerts"           # Matches: events.guest.system.monitoring.alerts
    subscriber4_key = "events.service.system.health.check.status"       # Matches: events.service.system.health.check.status
    subscriber5_key = "events.api.system.performance"                   # Matches: events.api.system.performance

    # Publisher uses MIXED WILDCARD PATTERN that should match all subscriber keys
    # In x-rtopic: the routing key is treated as a pattern
    publisher_mixed_pattern = "events.*.system.#"    # Mixed pattern: * for one word, # for zero or more words

    # Callback functions for each subscriber
    async def subscriber1_callback(message):
        """Callback for subscriber 1 with key: events.user.system"""
        subscriber1_messages.append(message.get_value())

    async def subscriber2_callback(message):
        """Callback for subscriber 2 with key: events.admin.system.auth"""
        subscriber2_messages.append(message.get_value())

    async def subscriber3_callback(message):
        """Callback for subscriber 3 with key: events.guest.system.monitoring.alerts"""
        subscriber3_messages.append(message.get_value())

    async def subscriber4_callback(message):
        """Callback for subscriber 4 with key: events.service.system.health.check.status"""
        subscriber4_messages.append(message.get_value())

    async def subscriber5_callback(message):
        """Callback for subscriber 5 with key: events.api.system.performance"""
        subscriber5_messages.append(message.get_value())

    try:
        # Create EventBusClient from config file (uses XRTopicExchangeHandler)
        config_file = os.path.join(config_folder_path, 'config_rtopic.jsonp')
        oEventBusClient = await EventBusClient.from_config(config_file)

        # Set up multiple subscribers with SPECIFIC KEYS (treated as literals in x-rtopic)
        await oEventBusClient.on(subscriber1_key, SimpleTestMessage, subscriber1_callback)
        await oEventBusClient.on(subscriber2_key, SimpleTestMessage, subscriber2_callback)
        await oEventBusClient.on(subscriber3_key, SimpleTestMessage, subscriber3_callback)
        await oEventBusClient.on(subscriber4_key, SimpleTestMessage, subscriber4_callback)
        await oEventBusClient.on(subscriber5_key, SimpleTestMessage, subscriber5_callback)

        # Wait for client to be connected before sending message
        await wait_for_client_connected(oEventBusClient)

        # Send message using the MIXED WILDCARD PATTERN (treated as pattern in x-rtopic)
        test_message = SimpleTestMessage(test_message_content)
        await oEventBusClient.send(publisher_mixed_pattern, test_message)

        # Wait for messages to be processed by all subscribers
        def all_subscribers_received_message():
            return (len(subscriber1_messages) >= 1 and
                   len(subscriber2_messages) >= 1 and
                   len(subscriber3_messages) >= 1 and
                   len(subscriber4_messages) >= 1 and
                   len(subscriber5_messages) >= 1)

        try:
            await poll_until_condition(all_subscribers_received_message, timeout_seconds=10.0, poll_interval=0.2)
        except PollingTimeoutError:
            result = f"Not all subscribers received message within timeout. Sub1: {len(subscriber1_messages)}, Sub2: {len(subscriber2_messages)}, Sub3: {len(subscriber3_messages)}, Sub4: {len(subscriber4_messages)}, Sub5: {len(subscriber5_messages)}"
            return result, oEventBusClient

        # Verify all subscribers received the correct message through mixed wildcard pattern matching
        if (len(subscriber1_messages) == 1 and subscriber1_messages[0] == test_message_content and
            len(subscriber2_messages) == 1 and subscriber2_messages[0] == test_message_content and
            len(subscriber3_messages) == 1 and subscriber3_messages[0] == test_message_content and
            len(subscriber4_messages) == 1 and subscriber4_messages[0] == test_message_content and
            len(subscriber5_messages) == 1 and subscriber5_messages[0] == test_message_content):

            result = f"All 5 subscribers received message using mixed wildcard patterns: {test_message_content}"
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

            if len(subscriber5_messages) != 1 or (subscriber5_messages and subscriber5_messages[0] != test_message_content):
                error_details.append(f"Subscriber 5 key '{subscriber5_key}' failed: expected 1 message '{test_message_content}', got {len(subscriber5_messages)} messages {subscriber5_messages}")

            result = f"Mixed wildcard pattern test failed: {'; '.join(error_details)}"
            return result, oEventBusClient

    except Exception as e:
        result = f"Error during mixed wildcard pattern test: {str(e)}"
        return result, oEventBusClient
