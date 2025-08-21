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
# EBC_0016.py
#
# Test case for EBC_0016: Test case sensitivity in x-rtopic routing patterns
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
    Test case EBC_0016: Test case sensitivity in x-rtopic routing patterns.

    TEST LOGIC FOR REVERSE TOPIC EXCHANGE (x-rtopic) WITH CASE SENSITIVITY:
    In x-rtopic exchange, the matching logic is REVERSED:
    - Bindings (subscriber keys) are treated as LITERAL KEYS
    - Message routing keys are treated as PATTERNS
    - Case sensitivity should be respected during pattern matching

    1. Set up subscribers with different case variations:
       - Subscriber 1: binds to "EVENTS.USER.LOGIN" (uppercase)
       - Subscriber 2: binds to "events.user.login" (lowercase)
       - Subscriber 3: binds to "Events.User.Login" (mixed case)
    2. Publisher sends patterns that match specific cases:
       - Pattern 1: "EVENTS.USER.LOGIN" (exact uppercase match)
       - Pattern 2: "events.user.login" (exact lowercase match)
    3. Verify case sensitivity is respected

    Args:
        config_folder_path: Path to the folder containing config files

    Returns:
        tuple: (result_message, oEventBusClient) for proper cleanup
    """

    oEventBusClient = None
    # Storage for received messages from each subscriber
    uppercase_subscriber_messages = []
    lowercase_subscriber_messages = []
    mixedcase_subscriber_messages = []

    test_message_content_1 = "Hello, Uppercase Test!"
    test_message_content_2 = "Hello, Lowercase Test!"

    # In x-rtopic exchange: subscribers bind to SPECIFIC keys (treated as literals)
    # Test case sensitivity with different cases
    uppercase_subscriber_key = "EVENTS.USER.LOGIN"    # Uppercase literal key
    lowercase_subscriber_key = "events.user.login"    # Lowercase literal key
    mixedcase_subscriber_key = "Events.User.Login"    # Mixed case literal key

    # Publisher uses EXACT PATTERNS that should match only specific subscribers
    # In x-rtopic: the routing key is treated as a pattern
    uppercase_pattern = "EVENTS.USER.LOGIN"           # Exact uppercase pattern
    lowercase_pattern = "events.user.login"           # Exact lowercase pattern

    # Callback functions for each subscriber
    async def uppercase_subscriber_callback(message):
        """Callback for uppercase subscriber with key: EVENTS.USER.LOGIN"""
        uppercase_subscriber_messages.append(message.get_value())

    async def lowercase_subscriber_callback(message):
        """Callback for lowercase subscriber with key: events.user.login"""
        lowercase_subscriber_messages.append(message.get_value())

    async def mixedcase_subscriber_callback(message):
        """Callback for mixed case subscriber with key: Events.User.Login"""
        mixedcase_subscriber_messages.append(message.get_value())

    try:
        # Create EventBusClient from config file (uses XRTopicExchangeHandler)
        config_file = os.path.join(config_folder_path, 'config_rtopic.jsonp')
        oEventBusClient = await EventBusClient.from_config(config_file)

        # Set up subscribers with different case variations
        await oEventBusClient.on(uppercase_subscriber_key, SimpleTestMessage, uppercase_subscriber_callback)
        await oEventBusClient.on(lowercase_subscriber_key, SimpleTestMessage, lowercase_subscriber_callback)
        await oEventBusClient.on(mixedcase_subscriber_key, SimpleTestMessage, mixedcase_subscriber_callback)

        # Wait for client to be connected before sending message
        await wait_for_client_connected(oEventBusClient)

        # Test 1: Send uppercase pattern - should only reach uppercase subscriber
        test_message_1 = SimpleTestMessage(test_message_content_1)
        await oEventBusClient.send(uppercase_pattern, test_message_1)

        # Test 2: Send lowercase pattern - should only reach lowercase subscriber
        test_message_2 = SimpleTestMessage(test_message_content_2)
        await oEventBusClient.send(lowercase_pattern, test_message_2)

        # Wait for messages to be processed by subscribers
        def expected_messages_received():
            return (len(uppercase_subscriber_messages) >= 1 and
                   len(lowercase_subscriber_messages) >= 1)

        try:
            await poll_until_condition(expected_messages_received, timeout_seconds=10.0, poll_interval=0.2)
        except PollingTimeoutError:
            result = f"Not all subscribers received expected messages within timeout. Uppercase: {len(uppercase_subscriber_messages)}, Lowercase: {len(lowercase_subscriber_messages)}, Mixed: {len(mixedcase_subscriber_messages)}"
            return result, oEventBusClient

        # Verify case sensitivity is respected
        uppercase_received_correctly = (len(uppercase_subscriber_messages) == 1 and
                                      uppercase_subscriber_messages[0] == test_message_content_1)
        lowercase_received_correctly = (len(lowercase_subscriber_messages) == 1 and
                                      lowercase_subscriber_messages[0] == test_message_content_2)
        mixedcase_received_nothing = len(mixedcase_subscriber_messages) == 0

        if uppercase_received_correctly and lowercase_received_correctly and mixedcase_received_nothing:
            result = "Case sensitivity test passed: uppercase subscriber received message, lowercase did not"
            return result, oEventBusClient
        else:
            # Detailed error reporting for debugging
            result = (f"Case sensitivity test failed: "
                     f"Uppercase subscriber received {len(uppercase_subscriber_messages)} messages {uppercase_subscriber_messages}, "
                     f"Lowercase subscriber received {len(lowercase_subscriber_messages)} messages {lowercase_subscriber_messages}, "
                     f"Mixed case subscriber received {len(mixedcase_subscriber_messages)} messages {mixedcase_subscriber_messages}")
            return result, oEventBusClient

    except Exception as e:
        result = f"Error during case sensitivity test in x-rtopic exchange: {str(e)}"
        return result, oEventBusClient
