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
# EBC_0009.py
#
# Test case for EBC_0009: Send message with routing key exceeding maximum length
#
# --------------------------------------------------------------------------------------------------------------

import asyncio
import os
import sys

# Add parent directory to path to access test modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from testutils.messages.simple_test_message import SimpleTestMessage
from testutils.polling_utils import wait_for_client_connected
from EventBusClient.event_bus_client import EventBusClient

async def test(config_folder_path):
    """
    Test case EBC_0009: Send message with routing key exceeding maximum length.
    This is a BadCase test that verifies proper error handling when using routing keys
    that exceed the maximum allowed length of 255 bytes for RabbitMQ.

    Args:
        config_folder_path: Path to the folder containing config files

    Returns:
        tuple: (result_message, oEventBusClient) for proper cleanup
    """

    oEventBusClient = None
    test_message_content = "Test message with excessively long routing key"

    # Create a routing key that exceeds the maximum length (255 characters)
    # RabbitMQ has a maximum routing key length of 255 bytes
    # We'll create a key with 300+ characters to ensure it exceeds the limit
    long_routing_key = "very.long.routing.key." + "x" * 300  # Total length > 255 chars

    try:
        # Create EventBusClient from config file
        config_file = os.path.join(config_folder_path, 'config_topic.jsonp')
        oEventBusClient = await EventBusClient.from_config(config_file)

        # Wait for client to be connected before sending message
        await wait_for_client_connected(oEventBusClient)

        # Try to send message with excessively long routing key (should raise exception)
        test_message = SimpleTestMessage(test_message_content)
        await oEventBusClient.send(long_routing_key, test_message)

        # If we reach here, no exception was raised (unexpected)
        result = f"Unexpected success: Message sent with routing key of length {len(long_routing_key)}"
        return result, oEventBusClient

    except Exception as e:
        # Don't handle the exception here - let it propagate to the test framework
        # The test framework expects a specific exception related to routing key length
        # But first ensure cleanup if possible
        if oEventBusClient:
            try:
                await oEventBusClient.close()
            except:
                pass
        raise
