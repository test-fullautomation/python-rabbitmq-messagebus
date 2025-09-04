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
# EBC_0026.py
#
# Test case for EBC_0026: Test BasicMessage equality comparison between two instances
#
# --------------------------------------------------------------------------------------------------------------

import os
import sys

# Add parent directory to path to access test modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from EventBusClient.message.basic_message import BasicMessage

async def test(config_folder_path):
    """
    Test case EBC_0026: Test BasicMessage equality comparison between two instances.

    This test verifies that BasicMessage instances can be correctly compared for equality.
    It tests various scenarios:
    1. Two identical messages (same content and headers) should be equal
    2. Messages with same content but different headers should not be equal
    3. Messages with different content but same headers should not be equal
    4. Messages with both different content and headers should not be equal
    5. Comparison with non-BasicMessage object should return NotImplemented
    6. Self-comparison should return True

    Args:
        config_folder_path: Path to the folder containing config files (not used in this test)

    Returns:
        tuple: (result_message, None) - None because we don't need EventBusClient cleanup
    """

    try:
        # Test 1: Two identical messages should be equal
        message1 = BasicMessage(content="Hello World", headers={"uuid": "test-uuid-1", "priority": "high"})
        message2 = BasicMessage(content="Hello World", headers={"uuid": "test-uuid-1", "priority": "high"})

        if not (message1 == message2):
            return "Test failed: Identical BasicMessage instances should be equal", None

        # Test 2: Messages with same content but different headers should not be equal
        message3 = BasicMessage(content="Hello World", headers={"uuid": "test-uuid-2", "priority": "low"})

        if message1 == message3:
            return "Test failed: BasicMessage instances with different headers should not be equal", None

        # Test 3: Messages with different content but same headers should not be equal
        message4 = BasicMessage(content="Different Content", headers={"uuid": "test-uuid-1", "priority": "high"})

        if message1 == message4:
            return "Test failed: BasicMessage instances with different content should not be equal", None

        # Test 4: Messages with both different content and headers should not be equal
        message5 = BasicMessage(content="Different Content", headers={"uuid": "test-uuid-3", "priority": "medium"})

        if message1 == message5:
            return "Test failed: BasicMessage instances with different content and headers should not be equal", None

        # Test 5: Self-comparison should return True
        if not (message1 == message1):
            return "Test failed: BasicMessage instance should be equal to itself", None

        # Test 6: Comparison with non-BasicMessage object should return NotImplemented
        # Note: This is tested indirectly - Python handles NotImplemented by trying the reverse comparison
        non_message_object = "Not a BasicMessage"
        comparison_result = message1 == non_message_object

        if comparison_result:
            return "Test failed: BasicMessage should not be equal to non-BasicMessage object", None

        # Test 7: Test with empty content and default headers
        empty_message1 = BasicMessage()
        empty_message2 = BasicMessage()

        # These should NOT be equal because they have different UUIDs in headers
        if empty_message1 == empty_message2:
            return "Test failed: Empty BasicMessage instances with different UUIDs should not be equal", None

        # Test 8: Test with manually set same headers
        same_headers = {"uuid": "same-uuid", "type": "test"}
        message_same_headers1 = BasicMessage(content="Same content", headers=same_headers)
        message_same_headers2 = BasicMessage(content="Same content", headers=same_headers)

        if not (message_same_headers1 == message_same_headers2):
            return "Test failed: BasicMessage instances with identical content and headers should be equal", None

        # Test 9: Test inequality operator (__ne__ is automatically derived from __eq__)
        if not (message1 != message3):
            return "Test failed: Inequality operator should work correctly", None

        if message1 != message2:
            return "Test failed: Identical messages should not be unequal", None

        return "BasicMessage equality comparison test passed: All equality tests successful", None

    except Exception as e:
        return f"Test failed with exception: {str(e)}", None
