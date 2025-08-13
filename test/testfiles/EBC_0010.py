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
# EBC_0010.py
#
# Test case for EBC_0010: Topic pattern matching fails due to encoding issues
#
# --------------------------------------------------------------------------------------------------------------

import asyncio
import os
import sys

# Add parent directory to path to access test modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from testutils.messages.simple_test_message import SimpleTestMessage
from EventBusClient.event_bus_client import EventBusClient
from EventBusClient.message.base_message import BaseMessage


class ProblematicEncodingMessage(BaseMessage):
    """A message class that will cause encoding/serialization issues."""

    def __init__(self, content=""):
        self.content = content
        # Create data that's problematic for serialization
        self.problematic_data = lambda x: x  # Functions can't be pickled

    @classmethod
    def from_data(cls, data):
        """Create a ProblematicEncodingMessage from data."""
        if isinstance(data, dict) and 'content' in data:
            return cls(data['content'])
        return cls(str(data))

    def get_value(self):
        """Return the content of the message."""
        return self.content


async def test(config_folder_path):
    """
    Test case EBC_0010: Topic pattern matching fails due to encoding issues.
    This is a BadCase test that verifies proper error handling when message serialization
    fails due to unpicklable content.

    Args:
        config_folder_path: Path to the folder containing config files

    Returns:
        tuple: (result_message, oEventBusClient) for proper cleanup
    """

    oEventBusClient = None
    test_message_content = "Test message with serialization issue"

    try:
        # Create EventBusClient from config file
        config_file = os.path.join(config_folder_path, 'config.jsonp')
        oEventBusClient = await EventBusClient.from_config(config_file)

        # Create a message that will cause serialization issues
        # This simulates encoding problems that prevent proper message serialization
        problematic_message = ProblematicEncodingMessage(test_message_content)

        # Try to send the message (serialization error should occur)
        # The PickleSerializer will fail to serialize the lambda function
        await oEventBusClient.send("test.encoding.issue", problematic_message)

        # If we reach here, no exception was raised (unexpected)
        result = f"Unexpected success: Message sent with problematic encoding/serialization"
        return result, oEventBusClient

    except Exception as e:
        # Don't handle the exception here - let it propagate to the test framework
        # The test framework expects a specific exception related to serialization
        # But first ensure cleanup if possible
        if oEventBusClient:
            try:
                await oEventBusClient.close()
            except:
                pass
        raise
