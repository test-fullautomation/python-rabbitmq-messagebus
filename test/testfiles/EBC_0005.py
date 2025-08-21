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
# EBC_0005.py
#
# Test case for EBC_0005: Send message with wildcard routing key patterns (* and #)
#
# --------------------------------------------------------------------------------------------------------------

import asyncio
import os
import sys

# Add parent directory to path to access test modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from testutils.messages.simple_test_message import SimpleTestMessage
from testutils.polling_utils import poll_until_condition, wait_for_client_connected, PollingTimeoutError
from EventBusClient.event_bus_client import EventBusClient

async def test(config_folder_path):
    """
    Test case EBC_0005: Send message with wildcard routing key patterns (* and #).
    This test verifies that messages can be sent and received using RabbitMQ wildcard patterns:
    - * (star) matches exactly one word
    - # (hash) matches zero or more words

    Args:
        config_folder_path: Path to the folder containing config files

    Returns:
        tuple: (result_message, oEventBusClient) for proper cleanup
    """

    oEventBusClient = None
    # Storage for received messages
    star_wildcard_messages = []
    hash_wildcard_messages = []

    # Test message contents
    star_content = "Star wildcard message"
    hash_content = "Hash wildcard message"

    # Routing key patterns for testing wildcards
    # * matches exactly one word
    star_routing_key = "events.user.login"
    star_subscriber_pattern = "events.*.login"

    # # matches zero or more words
    hash_routing_key = "logs.error.database.connection.timeout"
    hash_subscriber_pattern = "logs.#"

    # Callback functions for each wildcard subscriber
    async def star_wildcard_callback(message):
        """Callback for * wildcard routing pattern."""
        star_wildcard_messages.append(message.get_value())

    async def hash_wildcard_callback(message):
        """Callback for # wildcard routing pattern."""
        hash_wildcard_messages.append(message.get_value())

    try:
        # Create EventBusClient from config file
        config_file = os.path.join(config_folder_path, 'config_topic.jsonp')
        oEventBusClient = await EventBusClient.from_config(config_file)

        # Set up subscribers with wildcard routing key patterns
        await oEventBusClient.on(star_subscriber_pattern, SimpleTestMessage, star_wildcard_callback)
        await oEventBusClient.on(hash_subscriber_pattern, SimpleTestMessage, hash_wildcard_callback)

        # Wait for client to be connected before sending messages
        await wait_for_client_connected(oEventBusClient)

        # Send messages with routing keys that should match wildcard patterns
        star_message = SimpleTestMessage(star_content)
        await oEventBusClient.send(star_routing_key, star_message)

        hash_message = SimpleTestMessage(hash_content)
        await oEventBusClient.send(hash_routing_key, hash_message)

        # Wait for messages to be processed using polling utility
        def both_wildcard_messages_received():
            return (len(star_wildcard_messages) >= 1 and len(hash_wildcard_messages) >= 1)

        try:
            await poll_until_condition(both_wildcard_messages_received, timeout_seconds=5.0)
        except PollingTimeoutError:
            result = f"Not all wildcard messages received within timeout. Star: {len(star_wildcard_messages)}, Hash: {len(hash_wildcard_messages)}"
            return result, oEventBusClient

        # Verify all wildcard messages were received correctly
        if (len(star_wildcard_messages) == 1 and star_wildcard_messages[0] == star_content and
            len(hash_wildcard_messages) == 1 and hash_wildcard_messages[0] == hash_content):

            result = f"All wildcard patterns tested successfully: Star='{star_wildcard_messages[0]}', Hash='{hash_wildcard_messages[0]}'"
            return result, oEventBusClient
        else:
            # Detailed error reporting
            error_details = []
            if len(star_wildcard_messages) != 1 or (star_wildcard_messages and star_wildcard_messages[0] != star_content):
                error_details.append(f"Star wildcard pattern failed: expected 1 message '{star_content}', got {len(star_wildcard_messages)} messages {star_wildcard_messages}")

            if len(hash_wildcard_messages) != 1 or (hash_wildcard_messages and hash_wildcard_messages[0] != hash_content):
                error_details.append(f"Hash wildcard pattern failed: expected 1 message '{hash_content}', got {len(hash_wildcard_messages)} messages {hash_wildcard_messages}")

            result = f"Wildcard pattern test failed: {'; '.join(error_details)}"
            return result, oEventBusClient

    except Exception as e:
        result = f"Error during wildcard pattern test: {str(e)}"
        return result, oEventBusClient