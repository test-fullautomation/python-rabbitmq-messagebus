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
# EBC_0029.py
#
# Test case for EBC_0029: Test BasicMessage with empty content and no headers
#
# --------------------------------------------------------------------------------------------------------------

import os
import sys
import uuid

# Add parent directory to path to access test modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from EventBusClient.message.basic_message import BasicMessage

async def test(config_folder_path):
    """
    Test case EBC_0029: Test BasicMessage with empty content and no headers.

    This test verifies that:
    1. A BasicMessage can be created with empty content
    2. When no headers are provided, an auto-generated UUID header is created
    3. The message structure is valid and contains the expected components

    Args:
        config_folder_path: Path to the folder containing config files

    Returns:
        tuple: (result_message, None) as no cleanup is needed
    """

    try:
        # Test 1: Create BasicMessage with empty content and no headers
        message1 = BasicMessage()

        # Verify empty content
        if message1.content != "":
            return f"Test failed: Expected empty content, got '{message1.content}'", None

        # Verify auto-generated UUID header exists
        if 'uuid' not in message1.headers:
            return "Test failed: UUID header was not auto-generated", None

        # Verify UUID header is a valid hex string (32 characters)
        uuid_value = message1.headers['uuid']
        if not isinstance(uuid_value, str) or len(uuid_value) != 32:
            return f"Test failed: Invalid UUID format, got '{uuid_value}'", None

        # Try to validate it's a proper UUID by creating UUID object from hex
        try:
            uuid_obj = uuid.UUID(hex=uuid_value)
        except ValueError:
            return f"Test failed: UUID value '{uuid_value}' is not a valid hex UUID", None

        # Test 2: Create another BasicMessage and verify UUIDs are different
        message2 = BasicMessage()

        if message1.headers['uuid'] == message2.headers['uuid']:
            return "Test failed: Two messages should have different UUIDs", None

        # Test 3: Verify that explicitly passing empty content works the same
        message3 = BasicMessage(content="")

        if message3.content != "":
            return f"Test failed: Expected empty content for explicit empty string, got '{message3.content}'", None

        if 'uuid' not in message3.headers:
            return "Test failed: UUID header was not auto-generated for explicit empty content", None

        # Test 4: Verify that explicitly passing None headers results in UUID generation
        message4 = BasicMessage(content="", headers=None)

        if 'uuid' not in message4.headers:
            return "Test failed: UUID header was not auto-generated when headers=None", None

        # Test 5: Verify string representations work correctly
        str_repr = str(message1)
        if "BasicMessage(content=, headers=" not in str_repr:
            return f"Test failed: Unexpected string representation: {str_repr}", None

        # Test 6: Verify dictionary conversion works
        message_dict = message1.to_dict()
        expected_keys = {'content', 'headers'}
        if set(message_dict.keys()) != expected_keys:
            return f"Test failed: Dictionary keys mismatch. Expected {expected_keys}, got {set(message_dict.keys())}", None

        if message_dict['content'] != "":
            return f"Test failed: Dictionary content mismatch. Expected empty string, got '{message_dict['content']}'", None

        if 'uuid' not in message_dict['headers']:
            return "Test failed: UUID not present in dictionary headers", None

        # Test 7: Verify from_dict creates equivalent message
        reconstructed_message = BasicMessage.from_dict(message_dict)
        if not (reconstructed_message == message1):
            return "Test failed: Reconstructed message is not equal to original", None

        return "BasicMessage with empty content and auto-generated UUID header test passed", None

    except Exception as e:
        return f"Test failed with exception: {str(e)}", None
