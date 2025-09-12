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
# EBC_0023.py
#
# Test case for EBC_0023: EDGE CASES: Test x-rtopic with empty segments in routing patterns
# using Reverse Topic Exchange (x-rtopic) with routing patterns containing empty segments
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
    Test case EBC_0023: Test x-rtopic with empty segments in routing patterns.

    TEST LOGIC FOR REVERSE TOPIC EXCHANGE (x-rtopic) WITH EMPTY SEGMENTS:
    This test focuses on edge cases where routing patterns contain empty segments
    created by consecutive dots, leading dots, or trailing dots in routing patterns:

    - Patterns with double dots creating empty segments (e.g., "service..create")
    - Patterns with leading dots (e.g., ".service.create")
    - Patterns with trailing dots (e.g., "service.create.")
    - Patterns with multiple consecutive dots (e.g., "service...create")

    Test Scenarios for x-rtopic exchange:
    In x-rtopic exchange: the matching logic is REVERSED:
    - Bindings (subscriber keys) are treated as LITERAL KEYS
    - Message routing keys are treated as PATTERNS

    Empty Segments Test Setup:
    We have 8 subscriber keys (literal keys) and will test 4 patterns with empty segments:

    Subscriber keys (literal):
    1. "service.create"           # Normal 2-segment key
    2. "service..create"          # Key with empty segment (double dot)
    3. ".service.create"          # Key with leading empty segment
    4. "service.create."          # Key with trailing empty segment
    5. "service...create"         # Key with multiple empty segments
    6. "api.user.delete"          # Different pattern key
    7. "."                        # Single dot (empty key)
    8. ".."                       # Double dot (empty segments only)

    Routing patterns with empty segments (treated as patterns in x-rtopic):
    Pattern 1: "service..create"   - Should match key 2 (exact match with empty segment)
    Pattern 2: ".service.create"   - Should match key 3 (exact match with leading empty)
    Pattern 3: "service.create."   - Should match key 4 (exact match with trailing empty)
    Pattern 4: "service...create"  - Should match key 5 (exact match with multiple empty)

    Expected behavior:
    - Empty segments should be treated as literal parts of the routing key/pattern
    - Each pattern should only match its corresponding exact literal key
    - No wildcard matching should occur with empty segments
    - Normal keys should not match patterns with empty segments

    Args:
        config_folder_path: Path to the folder containing config files

    Returns:
        tuple: (result_message, oEventBusClient) for proper cleanup
    """

    oEventBusClient = None

    # Storage for received messages from each subscriber
    subscriber_messages = {
        'normal_key': [],
        'double_dot_key': [],
        'leading_dot_key': [],
        'trailing_dot_key': [],
        'multi_dot_key': [],
        'different_key': [],
        'single_dot_key': [],
        'double_dot_only_key': []
    }

    test_message_content_prefix = "Empty segments test message"

    # Subscriber keys (literal keys in x-rtopic) - including empty segments
    subscriber_keys = {
        'normal_key': "service.create",           # Normal key without empty segments
        'double_dot_key': "service..create",      # Key with empty segment (double dot)
        'leading_dot_key': ".service.create",     # Key with leading empty segment
        'trailing_dot_key': "service.create.",    # Key with trailing empty segment
        'multi_dot_key': "service...create",      # Key with multiple empty segments
        'different_key': "api.user.delete",       # Different pattern that shouldn't match
        'single_dot_key': ".",                    # Single dot only
        'double_dot_only_key': ".."               # Double dot only
    }

    # Routing patterns with empty segments (treated as patterns in x-rtopic)
    empty_segment_patterns = {
        'pattern1': "service..create",    # Should match double_dot_key only
        'pattern2': ".service.create",    # Should match leading_dot_key only
        'pattern3': "service.create.",    # Should match trailing_dot_key only
        'pattern4': "service...create"    # Should match multi_dot_key only
    }

    # Callback functions for each subscriber
    async def normal_key_callback(message, headers):
        subscriber_messages['normal_key'].append(message.get_value())

    async def double_dot_key_callback(message, headers):
        subscriber_messages['double_dot_key'].append(message.get_value())

    async def leading_dot_key_callback(message, headers):
        subscriber_messages['leading_dot_key'].append(message.get_value())

    async def trailing_dot_key_callback(message, headers):
        subscriber_messages['trailing_dot_key'].append(message.get_value())

    async def multi_dot_key_callback(message, headers):
        subscriber_messages['multi_dot_key'].append(message.get_value())

    async def different_key_callback(message, headers):
        subscriber_messages['different_key'].append(message.get_value())

    async def single_dot_key_callback(message, headers):
        subscriber_messages['single_dot_key'].append(message.get_value())

    async def double_dot_only_key_callback(message, headers):
        subscriber_messages['double_dot_only_key'].append(message.get_value())

    callbacks = {
        'normal_key': normal_key_callback,
        'double_dot_key': double_dot_key_callback,
        'leading_dot_key': leading_dot_key_callback,
        'trailing_dot_key': trailing_dot_key_callback,
        'multi_dot_key': multi_dot_key_callback,
        'different_key': different_key_callback,
        'single_dot_key': single_dot_key_callback,
        'double_dot_only_key': double_dot_only_key_callback
    }

    try:
        # Create EventBusClient from config file (uses XRTopicExchangeHandler)
        config_file = os.path.join(config_folder_path, 'config_rtopic.jsonp')
        oEventBusClient = await EventBusClient.from_config(config_file)

        # Set up subscribers with literal keys (including empty segments)
        for subscriber_name, subscriber_key in subscriber_keys.items():
            await oEventBusClient.on(subscriber_key, SimpleTestMessage, callbacks[subscriber_name])

        # Wait for client to be connected before sending messages
        await wait_for_client_connected(oEventBusClient)

        # Send messages using patterns with empty segments
        pattern_counter = 1
        for pattern_name, pattern in empty_segment_patterns.items():
            test_message_content = f"{test_message_content_prefix} from {pattern_name}"
            test_message = SimpleTestMessage(test_message_content)
            await oEventBusClient.send(pattern, test_message)
            pattern_counter += 1

        # Wait for all messages to be processed
        # Expected message counts based on empty segment patterns:
        # Only subscribers with exact matching keys should receive messages:
        # normal_key: 0 messages (no pattern matches)
        # double_dot_key: 1 message (matches pattern1)
        # leading_dot_key: 1 message (matches pattern2)
        # trailing_dot_key: 1 message (matches pattern3)
        # multi_dot_key: 1 message (matches pattern4)
        # different_key: 0 messages (no pattern matches)
        # single_dot_key: 0 messages (no pattern matches)
        # double_dot_only_key: 0 messages (no pattern matches)
        expected_counts = {
            'normal_key': 0,
            'double_dot_key': 1,
            'leading_dot_key': 1,
            'trailing_dot_key': 1,
            'multi_dot_key': 1,
            'different_key': 0,
            'single_dot_key': 0,
            'double_dot_only_key': 0
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
            # Verify the specific patterns that should have received messages
            patterns_with_matches = sum(1 for count in expected_counts.values() if count > 0)  # Should be 4
            total_patterns = len(empty_segment_patterns)  # 4 patterns

            result = f"Empty segments routing patterns test passed: {total_patterns} patterns with empty segments handled correctly"
            return result, oEventBusClient
        else:
            result = f"Empty segments routing patterns test failed: {'; '.join(error_details)}"
            return result, oEventBusClient

    except Exception as e:
        result = f"Error during empty segments routing patterns test: {str(e)}"
        return result, oEventBusClient
