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
# EBC_0020.py
#
# Test case for EBC_0020: EDGE CASES: Test x-rtopic with minimal routing patterns
# using Reverse Topic Exchange (x-rtopic) with the simplest possible routing scenarios
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
    Test case EBC_0020: Test x-rtopic with minimal routing patterns.

    TEST LOGIC FOR REVERSE TOPIC EXCHANGE (x-rtopic) WITH MINIMAL PATTERNS:
    This test focuses on the simplest possible routing scenarios for x-rtopic exchange:
    - Single word binding keys (no dots, no wildcards)
    - Single word routing keys (no dots, no wildcards)
    - Basic one-to-one message routing

    Test Scenarios:
    1. Single word subscriber key: "test"
    2. Single word routing key: "test"
    3. Exact match should deliver message
    4. Non-matching single word should not deliver message

    Args:
        config_folder_path: Path to the folder containing config files

    Returns:
        tuple: (result_message, oEventBusClient) for proper cleanup
    """

    oEventBusClient = None
    # Storage for received messages
    matching_subscriber_messages = []
    non_matching_subscriber_messages = []

    test_message_content = "Minimal pattern test message"

    # Minimal routing patterns - single words without dots
    matching_subscriber_key = "test"          # Literal key for matching subscriber
    non_matching_subscriber_key = "other"     # Literal key for non-matching subscriber
    routing_key = "test"                      # Single word routing key (exact match)

    # Callback functions for subscribers
    async def matching_subscriber_callback(message, headers):
        """Callback for subscriber that should receive the message"""
        matching_subscriber_messages.append(message.get_value())

    async def non_matching_subscriber_callback(message, headers):
        """Callback for subscriber that should NOT receive the message"""
        non_matching_subscriber_messages.append(message.get_value())

    try:
        # Create EventBusClient from config file (uses XRTopicExchangeHandler)
        config_file = os.path.join(config_folder_path, 'config_rtopic.jsonp')
        oEventBusClient = await EventBusClient.from_config(config_file)

        # Set up subscribers with minimal single-word keys
        await oEventBusClient.on(matching_subscriber_key, SimpleTestMessage, matching_subscriber_callback)
        await oEventBusClient.on(non_matching_subscriber_key, SimpleTestMessage, non_matching_subscriber_callback)

        # Wait for client to be connected before sending message
        await wait_for_client_connected(oEventBusClient)

        # Send message using minimal single-word routing key
        test_message = SimpleTestMessage(test_message_content)
        await oEventBusClient.send(routing_key, test_message)

        # Wait for message processing (only matching subscriber should receive)
        def message_processed():
            # Give some time for any potential non-matching messages to arrive
            return len(matching_subscriber_messages) >= 1

        try:
            await poll_until_condition(message_processed, timeout_seconds=5.0, poll_interval=0.1)
        except PollingTimeoutError:
            result = f"Matching subscriber did not receive message within timeout. Received: {len(matching_subscriber_messages)} messages"
            return result, oEventBusClient

        # Verify results: matching subscriber should receive, non-matching should not
        matching_received_correctly = (len(matching_subscriber_messages) == 1 and
                                     matching_subscriber_messages[0] == test_message_content)

        non_matching_received_nothing = len(non_matching_subscriber_messages) == 0

        if matching_received_correctly and non_matching_received_nothing:
            result = f"Minimal routing patterns test passed: single word pattern matched single word key"
            return result, oEventBusClient
        else:
            # Detailed error reporting
            error_details = []
            if not matching_received_correctly:
                error_details.append(f"Matching subscriber (key '{matching_subscriber_key}') failed: expected 1 message '{test_message_content}', got {len(matching_subscriber_messages)} messages {matching_subscriber_messages}")

            if not non_matching_received_nothing:
                error_details.append(f"Non-matching subscriber (key '{non_matching_subscriber_key}') incorrectly received {len(non_matching_subscriber_messages)} messages: {non_matching_subscriber_messages}")

            result = f"Minimal routing patterns test failed: {'; '.join(error_details)}"
            return result, oEventBusClient

    except Exception as e:
        result = f"Error during minimal routing patterns test: {str(e)}"
        return result, oEventBusClient
