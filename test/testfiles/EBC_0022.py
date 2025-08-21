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
# EBC_0022.py
#
# Test case for EBC_0022: EDGE CASES: Test x-rtopic with overlapping routing patterns
# using Reverse Topic Exchange (x-rtopic) with multiple overlapping routing scenarios
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
    Test case EBC_0022: Test x-rtopic with overlapping routing patterns.

    TEST LOGIC FOR REVERSE TOPIC EXCHANGE (x-rtopic) WITH OVERLAPPING PATTERNS:
    This test focuses on scenarios where multiple routing patterns could potentially
    match the same subscriber keys or where subscriber keys overlap in their coverage:

    - Multiple routing patterns that overlap in their matching scope
    - Subscriber keys that could be matched by multiple patterns
    - Testing edge cases with pattern precedence and overlapping matches

    Test Scenarios for x-rtopic exchange:
    In x-rtopic exchange: the matching logic is REVERSED:
    - Bindings (subscriber keys) are treated as LITERAL KEYS
    - Message routing keys are treated as PATTERNS

    Overlapping Pattern Test Setup:
    We have 5 subscriber keys (literal keys) and will test 3 overlapping routing patterns:

    Subscriber keys (literal):
    1. "service.user.create"
    2. "service.user.update"
    3. "service.order.create"
    4. "service.notification.send"
    5. "api.user.delete"

    Overlapping routing patterns (treated as patterns in x-rtopic):
    Pattern 1: "service.*.create" - Should match keys 1 and 3
    Pattern 2: "service.user.*"   - Should match keys 1 and 2
    Pattern 3: "*.user.*"        - Should match keys 1, 2, and 5

    Expected overlaps:
    - Key 1 ("service.user.create") matches all 3 patterns
    - Key 2 ("service.user.update") matches patterns 2 and 3
    - Key 3 ("service.order.create") matches pattern 1 only
    - Key 4 ("service.notification.send") matches none
    - Key 5 ("api.user.delete") matches pattern 3 only

    Args:
        config_folder_path: Path to the folder containing config files

    Returns:
        tuple: (result_message, oEventBusClient) for proper cleanup
    """

    oEventBusClient = None

    # Storage for received messages from each subscriber
    subscriber_messages = {
        'service_user_create': [],
        'service_user_update': [],
        'service_order_create': [],
        'service_notification_send': [],
        'api_user_delete': []
    }

    test_message_content_prefix = "Overlapping pattern test message"

    # Subscriber keys (literal keys in x-rtopic)
    subscriber_keys = {
        'service_user_create': "service.user.create",
        'service_user_update': "service.user.update",
        'service_order_create': "service.order.create",
        'service_notification_send': "service.notification.send",
        'api_user_delete': "api.user.delete"
    }

    # Overlapping routing patterns (treated as patterns in x-rtopic)
    overlapping_patterns = {
        'pattern1': "service.*.create",  # Should match service_user_create, service_order_create
        'pattern2': "service.user.*",    # Should match service_user_create, service_user_update
        'pattern3': "*.user.*"           # Should match service_user_create, service_user_update, api_user_delete
    }

    # Callback functions for each subscriber
    async def service_user_create_callback(message):
        subscriber_messages['service_user_create'].append(message.get_value())

    async def service_user_update_callback(message):
        subscriber_messages['service_user_update'].append(message.get_value())

    async def service_order_create_callback(message):
        subscriber_messages['service_order_create'].append(message.get_value())

    async def service_notification_send_callback(message):
        subscriber_messages['service_notification_send'].append(message.get_value())

    async def api_user_delete_callback(message):
        subscriber_messages['api_user_delete'].append(message.get_value())

    callbacks = {
        'service_user_create': service_user_create_callback,
        'service_user_update': service_user_update_callback,
        'service_order_create': service_order_create_callback,
        'service_notification_send': service_notification_send_callback,
        'api_user_delete': api_user_delete_callback
    }

    try:
        # Create EventBusClient from config file (uses XRTopicExchangeHandler)
        config_file = os.path.join(config_folder_path, 'config_rtopic.jsonp')
        oEventBusClient = await EventBusClient.from_config(config_file)

        # Set up subscribers with literal keys
        for subscriber_name, subscriber_key in subscriber_keys.items():
            await oEventBusClient.on(subscriber_key, SimpleTestMessage, callbacks[subscriber_name])

        # Wait for client to be connected before sending messages
        await wait_for_client_connected(oEventBusClient)

        # Send messages using overlapping patterns (each pattern sends a message)
        pattern_counter = 1
        for pattern_name, pattern in overlapping_patterns.items():
            test_message_content = f"{test_message_content_prefix} from {pattern_name}"
            test_message = SimpleTestMessage(test_message_content)
            await oEventBusClient.send(pattern, test_message)
            pattern_counter += 1

        # Wait for all messages to be processed
        # Expected message counts based on overlapping patterns:
        # service_user_create: 3 messages (matches all patterns)
        # service_user_update: 2 messages (matches pattern2, pattern3)
        # service_order_create: 1 message (matches pattern1)
        # service_notification_send: 0 messages (matches none)
        # api_user_delete: 1 message (matches pattern3)
        expected_counts = {
            'service_user_create': 3,
            'service_user_update': 2,
            'service_order_create': 1,
            'service_notification_send': 0,
            'api_user_delete': 1
        }

        def all_expected_messages_received():
            for subscriber_name, expected_count in expected_counts.items():
                if len(subscriber_messages[subscriber_name]) != expected_count:
                    return False
            return True

        try:
            await poll_until_condition(all_expected_messages_received, timeout_seconds=10.0, poll_interval=0.2)
        except PollingTimeoutError:
            received_counts = {name: len(messages) for name, messages in subscriber_messages.items()}
            result = f"Not all expected messages received within timeout. Expected: {expected_counts}, Received: {received_counts}"
            return result, oEventBusClient

        # Verify all subscribers received the correct number of messages
        all_received_correctly = True
        error_details = []

        for subscriber_name, expected_count in expected_counts.items():
            actual_count = len(subscriber_messages[subscriber_name])
            if actual_count != expected_count:
                all_received_correctly = False
                subscriber_key = subscriber_keys[subscriber_name]
                error_details.append(f"Subscriber '{subscriber_name}' with key '{subscriber_key}' failed: expected {expected_count} messages, got {actual_count} messages")

        if all_received_correctly:
            # Calculate total matches for verification
            total_expected_matches = sum(expected_counts.values())  # 3+2+1+0+1 = 7 total matches
            total_patterns = len(overlapping_patterns)              # 3 patterns
            matching_keys = sum(1 for count in expected_counts.values() if count > 0)  # 4 keys matched

            result = f"Overlapping routing patterns test passed: {total_patterns} overlapping patterns matched {matching_keys} subscriber keys correctly"
            return result, oEventBusClient
        else:
            result = f"Overlapping routing patterns test failed: {'; '.join(error_details)}"
            return result, oEventBusClient

    except Exception as e:
        result = f"Error during overlapping routing patterns test: {str(e)}"
        return result, oEventBusClient
