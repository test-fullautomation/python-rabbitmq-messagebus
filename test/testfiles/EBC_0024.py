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
# EBC_0024.py
#
# Test case for EBC_0024: Test BasicMessage publishing and subscription with topic exchange using simple routing key
#
# --------------------------------------------------------------------------------------------------------------

import os
import sys

# Add parent directory to path to access test modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from testutils.polling_utils import wait_for_messages, wait_for_client_connected, PollingTimeoutError
from EventBusClient.event_bus_client import EventBusClient
from EventBusClient.message.basic_message import BasicMessage

async def test(config_folder_path):
    """
    Test case EBC_0024: Test BasicMessage publishing and subscription with topic exchange using simple routing key.
    This test verifies that BasicMessage can be successfully published and subscribed using a topic exchange
    with a simple routing key.

    Args:
        config_folder_path: Path to the folder containing config files

    Returns:
        tuple: (result_message, oEventBusClient) for proper cleanup
    """

    oEventBusClient = None
    received_messages = []
    test_message_content = "Test BasicMessage Content"
    routing_key = "basic.message.test"

    async def message_callback(message):
        """Callback function to handle received BasicMessage."""
        received_messages.append(message.content)

    try:
        # Create EventBusClient from config file with topic exchange handler
        config_file = os.path.join(config_folder_path, 'config_topic.jsonp')
        oEventBusClient = await EventBusClient.from_config(config_file)

        # Subscribe to the routing key using BasicMessage
        await oEventBusClient.on(routing_key, BasicMessage, message_callback)

        # Wait for client to be connected before sending message
        await wait_for_client_connected(oEventBusClient)

        # Create and send BasicMessage
        test_message = BasicMessage(content=test_message_content)
        await oEventBusClient.send(routing_key, test_message)

        # Wait for message to be processed using polling utility
        try:
            await wait_for_messages(received_messages, expected_count=1, timeout_seconds=5.0)
            result = f"BasicMessage successfully sent and received: {received_messages[0]}"
        except PollingTimeoutError:
            result = "No BasicMessage received within timeout"

        return result, oEventBusClient

    except Exception as e:
        print(f"Error during BasicMessage test: {e}")
        result = f"Error during BasicMessage test: {str(e)}"
        return result, oEventBusClient
