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
# EBC_0027.py
#
# Test case for EBC_0027: Test BasicMessage creation from dictionary representation
#
# --------------------------------------------------------------------------------------------------------------

import os
import sys

# Add parent directory to path to access test modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from EventBusClient.message.basic_message import BasicMessage

async def test(config_folder_path):
    """
    Test case EBC_0027: Test BasicMessage creation from dictionary representation.

    This test verifies that BasicMessage instances can be correctly created from dictionary
    representation and maintain data integrity. It tests various scenarios:
    1. Create BasicMessage from dictionary with both content and headers
    2. Create BasicMessage from dictionary with only content
    3. Create BasicMessage from dictionary with only headers
    4. Create BasicMessage from empty dictionary
    5. Round-trip conversion (to_dict -> from_dict)
    6. Verify equality of original and recreated messages
    7. Test with complex header structures
    8. Test with special characters in content

    Args:
        config_folder_path: Path to the folder containing config files (not used in this test)

    Returns:
        tuple: (result_message, None) - None because we don't need EventBusClient cleanup
    """

    try:
        # Test 1: Create BasicMessage from dictionary with both content and headers
        test_dict1 = {
            "content": "Hello from dictionary",
            "headers": {"uuid": "test-uuid-1", "priority": "high", "timestamp": "2025-08-28T10:00:00Z"}
        }
        message1 = BasicMessage.from_dict(test_dict1)

        if message1.content != test_dict1["content"]:
            return "Test failed: Content not correctly set from dictionary", None

        if message1.headers != test_dict1["headers"]:
            return "Test failed: Headers not correctly set from dictionary", None

        # Test 2: Create BasicMessage from dictionary with only content
        test_dict2 = {
            "content": "Content only message"
        }
        message2 = BasicMessage.from_dict(test_dict2)

        if message2.content != test_dict2["content"]:
            return "Test failed: Content-only message not correctly created", None

        if message2.headers != {}:
            return "Test failed: Default headers should be empty dictionary when not provided", None

        # Test 3: Create BasicMessage from dictionary with only headers
        test_dict3 = {
            "headers": {"uuid": "header-only-uuid", "type": "notification"}
        }
        message3 = BasicMessage.from_dict(test_dict3)

        if message3.content != "":
            return "Test failed: Default content should be empty string when not provided", None

        if message3.headers != test_dict3["headers"]:
            return "Test failed: Headers-only message not correctly created", None

        # Test 4: Create BasicMessage from empty dictionary
        empty_dict = {}
        message4 = BasicMessage.from_dict(empty_dict)

        if message4.content != "":
            return "Test failed: Default content should be empty string for empty dictionary", None

        if message4.headers != {}:
            return "Test failed: Default headers should be empty dictionary for empty dictionary", None

        # Test 5: Round-trip conversion (to_dict -> from_dict)
        original_message = BasicMessage(
            content="Round-trip test message",
            headers={"uuid": "round-trip-uuid", "priority": "medium", "source": "test"}
        )

        # Convert to dictionary
        message_dict = original_message.to_dict()

        # Verify dictionary structure
        if "content" not in message_dict or "headers" not in message_dict:
            return "Test failed: Dictionary should contain 'content' and 'headers' keys", None

        if message_dict["content"] != original_message.content:
            return "Test failed: Dictionary content doesn't match original", None

        if message_dict["headers"] != original_message.headers:
            return "Test failed: Dictionary headers don't match original", None

        # Create new message from dictionary
        recreated_message = BasicMessage.from_dict(message_dict)

        # Test 6: Verify equality of original and recreated messages
        if original_message != recreated_message:
            return "Test failed: Original and recreated messages should be equal", None

        if original_message.content != recreated_message.content:
            return "Test failed: Round-trip content doesn't match", None

        if original_message.headers != recreated_message.headers:
            return "Test failed: Round-trip headers don't match", None

        # Test 7: Test with complex header structures
        complex_dict = {
            "content": "Complex headers test",
            "headers": {
                "uuid": "complex-uuid",
                "nested": {"level1": {"level2": "deep value"}},
                "array": [1, 2, 3, "string", {"key": "value"}],
                "boolean": True,
                "number": 42,
                "null_value": None
            }
        }
        complex_message = BasicMessage.from_dict(complex_dict)

        if complex_message.content != complex_dict["content"]:
            return "Test failed: Complex message content not correctly set", None

        if complex_message.headers != complex_dict["headers"]:
            return "Test failed: Complex headers not correctly preserved", None

        # Verify round-trip with complex headers
        complex_dict_recreated = complex_message.to_dict()
        complex_message_recreated = BasicMessage.from_dict(complex_dict_recreated)

        if complex_message != complex_message_recreated:
            return "Test failed: Complex message round-trip failed", None

        # Test 8: Test with special characters in content
        special_content_dict = {
            "content": "Special chars: áéíóú ñ €$£¥ 中文 🚀 \n\t\r \\\"'",
            "headers": {"uuid": "special-chars-uuid", "encoding": "utf-8"}
        }
        special_message = BasicMessage.from_dict(special_content_dict)

        if special_message.content != special_content_dict["content"]:
            return "Test failed: Special characters not correctly preserved in content", None

        if special_message.headers != special_content_dict["headers"]:
            return "Test failed: Headers with special content not correctly preserved", None

        # Verify round-trip with special characters
        special_dict_recreated = special_message.to_dict()
        special_message_recreated = BasicMessage.from_dict(special_dict_recreated)

        if special_message != special_message_recreated:
            return "Test failed: Special characters round-trip failed", None

        # Test 9: Verify that from_dict creates new instances (not references)
        dict_for_independence_test = {
            "content": "Independence test",
            "headers": {"uuid": "independence-uuid"}
        }

        # Create two messages from separate dictionary copies to test independence
        message_a = BasicMessage.from_dict(dict_for_independence_test.copy())
        # Create a deep copy of the dictionary to ensure headers are independent
        import copy
        dict_copy = copy.deepcopy(dict_for_independence_test)
        message_b = BasicMessage.from_dict(dict_copy)

        if message_a is message_b:
            return "Test failed: from_dict should create new instances, not return same reference", None

        # Modify one message's headers
        message_a.headers["modified"] = True

        if "modified" in message_b.headers:
            return "Test failed: Modifications to one instance should not affect another", None

        # Test 10: Verify type consistency
        if not isinstance(message1.content, str):
            return "Test failed: Content should be string type", None

        if not isinstance(message1.headers, dict):
            return "Test failed: Headers should be dict type", None

        return "BasicMessage dictionary creation test passed: All dictionary conversion and creation tests successful", None

    except Exception as e:
        return f"Test failed with exception: {str(e)}", None
