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
# EBC_0006.py
#
# Test case for EBC_0006: Verify routing key case sensitivity
#
# --------------------------------------------------------------------------------------------------------------

import asyncio
import os
import sys

# Add parent directory to path to access test modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from testutils.messages.simple_test_message import SimpleTestMessage
from testutils.polling_utils import poll_until_condition, PollingTimeoutError
from EventBusClient.event_bus_client import EventBusClient

async def test(config_folder_path):
    """
    Test case EBC_0006: Verify routing key case sensitivity.
    This test verifies that routing keys with different cases are treated as separate routes.

    Args:
        config_folder_path: Path to the folder containing config files

    Returns:
        tuple: (result_message, oEventBusClient) for proper cleanup
    """

    oEventBusClient = None
    lowercase_received_messages = []
    uppercase_received_messages = []

    # Define routing keys with different cases
    lowercase_routing_key = "test.case.sensitivity"
    uppercase_routing_key = "TEST.CASE.SENSITIVITY"

    lowercase_message_content = "lowercase message"
    uppercase_message_content = "uppercase message"

    async def lowercase_callback(message):
        """Callback function for lowercase routing key."""
        lowercase_received_messages.append(message.get_value())

    async def uppercase_callback(message):
        """Callback function for uppercase routing key."""
        uppercase_received_messages.append(message.get_value())

    try:
        config_file = os.path.join(config_folder_path, 'config.jsonp')
        oEventBusClient = await EventBusClient.from_config(config_file)

        await oEventBusClient.on(lowercase_routing_key, SimpleTestMessage, lowercase_callback)
        await oEventBusClient.on(uppercase_routing_key, SimpleTestMessage, uppercase_callback)

        # Send message to lowercase routing key
        lowercase_message = SimpleTestMessage(lowercase_message_content)
        await oEventBusClient.send(lowercase_routing_key, lowercase_message)

        # Send message to uppercase routing key
        uppercase_message = SimpleTestMessage(uppercase_message_content)
        await oEventBusClient.send(uppercase_routing_key, uppercase_message)

        def both_case_messages_received():
            return (len(lowercase_received_messages) >= 1 and len(uppercase_received_messages) >= 1)

        try:
            await poll_until_condition(both_case_messages_received, timeout_seconds=5.0)
        except PollingTimeoutError:
            result = f"Not all case-sensitive messages received within timeout. Lowercase: {len(lowercase_received_messages)}, Uppercase: {len(uppercase_received_messages)}"
            return result, oEventBusClient

        lowercase_count = len(lowercase_received_messages)
        uppercase_count = len(uppercase_received_messages)

        # Verify case sensitivity: each subscriber should only receive its specific message
        if (lowercase_count == 1 and
            uppercase_count == 1 and
            lowercase_received_messages[0] == lowercase_message_content and
            uppercase_received_messages[0] == uppercase_message_content):
            result = f"Case sensitivity verified: lowercase received {lowercase_count} messages, uppercase received {uppercase_count} messages"
        else:
            result = f"Case sensitivity test failed: lowercase received {lowercase_count} messages {lowercase_received_messages}, uppercase received {uppercase_count} messages {uppercase_received_messages}"

        return result, oEventBusClient

    except Exception as e:
        print(e)
        result = f"Error during case sensitivity test: {str(e)}"
        return result, oEventBusClient
