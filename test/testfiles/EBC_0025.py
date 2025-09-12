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
# EBC_0025.py
#
# Test case for EBC_0025: Test BasicMessage with x-rtopic reverse routing logic
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
    Test case EBC_0025: Test BasicMessage with x-rtopic reverse routing logic.

    This test verifies the reverse routing logic in x-rtopic exchanges where:
    - Subscriber uses literal routing key (e.g., "device.sensor.temperature")
    - Publisher uses pattern routing key (e.g., "device.sensor.*")

    In normal topic exchanges, it's the opposite:
    - Publisher uses literal key
    - Subscriber uses pattern

    This is the key feature of x-rtopic (reverse topic) exchanges.

    Args:
        config_folder_path: Path to the folder containing config files

    Returns:
        tuple: (result_message, oEventBusClient) for proper cleanup
    """

    oEventBusClient = None
    received_messages = []
    test_message_content = "Test x-rtopic reverse routing content"

    # In x-rtopic reverse routing:
    # - Subscriber uses literal key
    # - Publisher uses pattern key
    literal_routing_key = "device.sensor.temperature"  # Subscriber uses this literal key
    pattern_routing_key = "device.sensor.*"            # Publisher uses this pattern

    async def message_callback(message, headers):
        """Callback function to handle received BasicMessage."""
        received_messages.append(message.content)

    try:
        # Create EventBusClient from x-rtopic config file
        config_file = os.path.join(config_folder_path, 'config_rtopic.jsonp')
        oEventBusClient = await EventBusClient.from_config(config_file)

        # Subscribe using literal routing key (this is the reverse of normal topic routing)
        await oEventBusClient.on(literal_routing_key, BasicMessage, message_callback)

        # Wait for client to be connected before sending message
        await wait_for_client_connected(oEventBusClient)

        # Create and send BasicMessage using pattern routing key
        # In x-rtopic, the pattern "device.sensor.*" should match the literal subscription "device.sensor.temperature"
        test_message = BasicMessage(content=test_message_content)
        await oEventBusClient.send(pattern_routing_key, test_message)

        # Wait for message to be processed using polling utility
        try:
            await wait_for_messages(received_messages, expected_count=1, timeout_seconds=5.0)
            result = f"BasicMessage with x-rtopic reverse routing successful: {received_messages[0]}"
        except PollingTimeoutError:
            result = "No BasicMessage received within timeout for x-rtopic reverse routing"

        return result, oEventBusClient

    except Exception as e:
        print(f"Error during x-rtopic reverse routing test: {e}")
        result = f"Error during x-rtopic reverse routing test: {str(e)}"
        return result, oEventBusClient
