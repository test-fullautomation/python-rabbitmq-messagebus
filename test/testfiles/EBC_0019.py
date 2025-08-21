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
# EBC_0019.py
#
# Test case for EBC_0019: Test serialization failure with x-rtopic patterns
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
from EventBusClient.message.base_message import BaseMessage


class NonSerializableMessage(BaseMessage):
    """A message class that contains data that cannot be serialized by pickle."""

    def __init__(self, content=""):
        self.content = content
        # Create data that's problematic for pickle serialization
        # Lambda functions cannot be pickled
        self.unpicklable_function = lambda x: x + 1
        # Thread locks also cannot be pickled
        self.unpicklable_lock = asyncio.Lock()

    @classmethod
    def from_data(cls, data):
        """Create a NonSerializableMessage from data."""
        if isinstance(data, dict) and 'content' in data:
            return cls(data['content'])
        return cls(str(data))

    def get_value(self):
        """Return the content of the message."""
        return self.content


async def test(config_folder_path):
    """
    Test case EBC_0019: Test serialization failure with x-rtopic patterns.
    This is a BadCase test that verifies proper error handling when message serialization
    fails specifically with x-rtopic exchange patterns.

    TEST LOGIC FOR X-RTOPIC EXCHANGE (BADCASE):
    This test creates a message that contains unpicklable data (lambda function and asyncio.Lock)
    and attempts to send it using a wildcard pattern. The serialization should fail
    when the PickleSerializer tries to serialize the unpicklable content.

    Args:
        config_folder_path: Path to the folder containing config files

    Returns:
        tuple: (result_message, oEventBusClient) for proper cleanup
    """

    oEventBusClient = None
    test_message_content = "Test message with serialization issue in x-rtopic"

    try:
        # Create EventBusClient from config file (uses XRTopicExchangeHandler)
        config_file = os.path.join(config_folder_path, 'config_rtopic.jsonp')
        oEventBusClient = await EventBusClient.from_config(config_file)

        # Wait for client to be connected before sending message
        await wait_for_client_connected(oEventBusClient)

        # Create a message that will cause serialization issues
        problematic_message = NonSerializableMessage(test_message_content)

        rtopic_pattern = "events.*.serialization.#"

        # The PickleSerializer should fail when trying to serialize the unpicklable content
        # This should raise a RuntimeError with "Can't pickle" substring in the message
        await oEventBusClient.send(rtopic_pattern, problematic_message)

        # If we reach here, no exception was raised (unexpected)
        result = f"Unexpected success: Message with unpicklable content sent with x-rtopic pattern: {rtopic_pattern}"
        return result, oEventBusClient

    except Exception as e:
        # Don't handle the exception here - let it propagate to the test framework
        # The test framework expects an exception containing "Can't pickle" substring
        # But first ensure cleanup if possible
        if oEventBusClient:
            try:
                await oEventBusClient.close()
            except:
                pass
        raise
