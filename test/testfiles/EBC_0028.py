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
# EBC_0028.py
#
# Test case for EBC_0028: Test BasicMessage inequality with different content or headers
#
# --------------------------------------------------------------------------------------------------------------

import os
import sys

# Add parent directory to path to access test modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from EventBusClient.message.basic_message import BasicMessage

async def test(config_folder_path):
    """
    Test case EBC_0028: Test BasicMessage inequality with different content or headers.

    This test verifies that BasicMessage instances are correctly identified as non-equal
    when they have different content or headers. It tests various inequality scenarios:
    1. Messages with different content but same headers should not be equal
    2. Messages with same content but different headers should not be equal
    3. Messages with both different content and different headers should not be equal
    4. Messages with different header values should not be equal
    5. Messages with additional headers should not be equal
    6. Messages with missing headers should not be equal
    7. Empty vs non-empty content should not be equal
    8. Empty vs non-empty headers should not be equal

    Args:
        config_folder_path: Path to the folder containing config files (not used in this test)

    Returns:
        tuple: (result_message, None) - None because we don't need EventBusClient cleanup
    """

    try:
        # Test 1: Messages with different content but same headers should not be equal
        headers1 = {"uuid": "test-uuid-1", "priority": "high", "sender": "test"}
        message1 = BasicMessage(content="First Content", headers=headers1)
        message2 = BasicMessage(content="Second Content", headers=headers1)

        if message1 == message2:
            return "Test failed: Messages with different content should not be equal", None

        # Verify inequality operator works correctly
        if not (message1 != message2):
            return "Test failed: Inequality operator should return True for messages with different content", None

        # Test 2: Messages with same content but different headers should not be equal
        headers2 = {"uuid": "test-uuid-2", "priority": "low", "sender": "test"}
        message3 = BasicMessage(content="Same Content", headers=headers1)
        message4 = BasicMessage(content="Same Content", headers=headers2)

        if message3 == message4:
            return "Test failed: Messages with different headers should not be equal", None

        if not (message3 != message4):
            return "Test failed: Inequality operator should return True for messages with different headers", None

        # Test 3: Messages with both different content and different headers should not be equal
        message5 = BasicMessage(content="Content A", headers={"uuid": "uuid-a", "type": "type-a"})
        message6 = BasicMessage(content="Content B", headers={"uuid": "uuid-b", "type": "type-b"})

        if message5 == message6:
            return "Test failed: Messages with different content and headers should not be equal", None

        if not (message5 != message6):
            return "Test failed: Inequality operator should return True for completely different messages", None

        # Test 4: Messages with different header values should not be equal
        message7 = BasicMessage(content="Test", headers={"priority": "high", "status": "active"})
        message8 = BasicMessage(content="Test", headers={"priority": "low", "status": "active"})

        if message7 == message8:
            return "Test failed: Messages with different header values should not be equal", None

        if not (message7 != message8):
            return "Test failed: Inequality operator should return True for different header values", None

        # Test 5: Messages with additional headers should not be equal
        message9 = BasicMessage(content="Test", headers={"uuid": "test", "priority": "medium"})
        message10 = BasicMessage(content="Test", headers={"uuid": "test", "priority": "medium", "extra": "field"})

        if message9 == message10:
            return "Test failed: Messages with additional headers should not be equal", None

        if not (message9 != message10):
            return "Test failed: Inequality operator should return True for messages with additional headers", None

        # Test 6: Messages with missing headers should not be equal
        message11 = BasicMessage(content="Test", headers={"uuid": "test", "priority": "medium", "sender": "app"})
        message12 = BasicMessage(content="Test", headers={"uuid": "test", "priority": "medium"})

        if message11 == message12:
            return "Test failed: Messages with missing headers should not be equal", None

        if not (message11 != message12):
            return "Test failed: Inequality operator should return True for messages with missing headers", None

        # Test 7: Empty vs non-empty content should not be equal
        message13 = BasicMessage(content="", headers={"uuid": "test"})
        message14 = BasicMessage(content="Non-empty content", headers={"uuid": "test"})

        if message13 == message14:
            return "Test failed: Empty and non-empty content should not be equal", None

        if not (message13 != message14):
            return "Test failed: Inequality operator should return True for empty vs non-empty content", None

        # Test 8: Empty vs non-empty headers should not be equal (using manually created headers)
        message15 = BasicMessage(content="Test", headers={"uuid": "test"})
        message16 = BasicMessage(content="Test", headers={})

        if message15 == message16:
            return "Test failed: Messages with empty headers should not equal messages with non-empty headers", None

        if not (message15 != message16):
            return "Test failed: Inequality operator should return True for different header counts", None

        # Test 9: Messages with same structure but different values in nested scenarios
        message17 = BasicMessage(content="Data", headers={"config": {"timeout": 30, "retries": 3}})
        message18 = BasicMessage(content="Data", headers={"config": {"timeout": 60, "retries": 3}})

        if message17 == message18:
            return "Test failed: Messages with different nested header values should not be equal", None

        if not (message17 != message18):
            return "Test failed: Inequality operator should return True for different nested values", None

        # Test 10: Default UUID generation creates different messages
        message19 = BasicMessage(content="Test content")
        message20 = BasicMessage(content="Test content")

        # These should be different because each gets a unique UUID
        if message19 == message20:
            return "Test failed: Messages with auto-generated UUIDs should not be equal", None

        if not (message19 != message20):
            return "Test failed: Inequality operator should return True for messages with different auto-generated UUIDs", None

        return "BasicMessage inequality comparison test passed: All inequality tests successful", None

    except Exception as e:
        return f"Test failed with exception: {str(e)}", None
