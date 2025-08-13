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
# EBC_0007.py
#
# Test case for EBC_0007: Send message with malformed routing key pattern
#
# --------------------------------------------------------------------------------------------------------------

import asyncio
import os
import sys

# Add parent directory to path to access test modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from testutils.messages.simple_test_message import SimpleTestMessage
from EventBusClient.event_bus_client import EventBusClient

async def test(config_folder_path):
    """
    Test case EBC_0007: Send message with malformed routing key pattern.
    This is a BadCase test that verifies proper error handling when using invalid routing keys.

    Args:
        config_folder_path: Path to the folder containing config files

    Returns:
        tuple: (result_message, oEventBusClient) for proper cleanup
    """

    oEventBusClient = None
    test_message_content = "Test message with malformed routing key"

    # Test with None routing key (most likely to cause TypeError)
    malformed_routing_key = None

    try:
        # Create EventBusClient from config file
        config_file = os.path.join(config_folder_path, 'config.jsonp')
        oEventBusClient = await EventBusClient.from_config(config_file)

        # Try to send message with malformed routing key (should raise exception)
        test_message = SimpleTestMessage(test_message_content)
        await oEventBusClient.send(malformed_routing_key, test_message)

        # If we reach here, no exception was raised (unexpected)
        result = f"Unexpected success: Message sent with malformed routing key '{malformed_routing_key}'"
        return result, oEventBusClient

    except Exception as e:
        # Don't handle the exception here - let it propagate to the test framework
        # But first ensure cleanup if possible
        if oEventBusClient:
            try:
                await oEventBusClient.close()
            except:
                pass
        raise
