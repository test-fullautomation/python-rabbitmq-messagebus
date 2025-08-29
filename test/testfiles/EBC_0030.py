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
# EBC_0030.py
#
# Test case for EBC_0030: Test BasicMessage string representations using str() and repr() methods
#
# --------------------------------------------------------------------------------------------------------------

import os
import sys

# Add parent directory to path to access test modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from EventBusClient.message.basic_message import BasicMessage

async def test(config_folder_path):
    """
    Test case EBC_0030: Test BasicMessage string representations using str() and repr() methods.

    This test verifies that BasicMessage instances provide correct string representations
    through both str() and repr() methods. It tests various scenarios:
    1. BasicMessage with simple content and default headers
    2. BasicMessage with complex content and custom headers
    3. BasicMessage with empty content and default headers
    4. BasicMessage with special characters in content
    5. BasicMessage with None content (edge case)
    6. Verify that str() and repr() produce different but valid representations
    7. Verify that repr() can be used for debugging purposes

    Args:
        config_folder_path: Path to the folder containing config files (not used in this test)

    Returns:
        tuple: (result_message, None) - None because we don't need EventBusClient cleanup
    """

    try:
        # Test 1: BasicMessage with simple content and default headers
        message1 = BasicMessage(content="Hello, World!")
        str_repr1 = str(message1)
        repr_repr1 = repr(message1)

        # Verify that both representations contain expected elements
        if "BasicMessage" not in str_repr1 or "Hello, World!" not in str_repr1:
            return "Test failed: str() representation does not contain expected content", None

        if "BasicMessage" not in repr_repr1 or "Hello, World!" not in repr_repr1:
            return "Test failed: repr() representation does not contain expected content", None

        # Test 2: BasicMessage with complex content and custom headers
        custom_headers = {"uuid": "test-uuid-123", "priority": "high", "timestamp": "2025-01-01"}
        message2 = BasicMessage(content="Complex Content with Numbers 123 and Symbols !@#", headers=custom_headers)
        str_repr2 = str(message2)
        repr_repr2 = repr(message2)

        # Verify that custom headers appear in representations
        if "test-uuid-123" not in str_repr2 or "priority" not in str_repr2:
            return "Test failed: str() representation does not contain custom headers", None

        if "test-uuid-123" not in repr_repr2 or "priority" not in repr_repr2:
            return "Test failed: repr() representation does not contain custom headers", None

        # Test 3: BasicMessage with empty content and default headers
        message3 = BasicMessage(content="")
        str_repr3 = str(message3)
        repr_repr3 = repr(message3)

        # Verify that empty content is handled correctly
        if "content=" not in str_repr3 or "headers=" not in str_repr3:
            return "Test failed: str() representation missing content or headers for empty message", None

        if "content=" not in repr_repr3 or "headers=" not in repr_repr3:
            return "Test failed: repr() representation missing content or headers for empty message", None

        # Test 4: BasicMessage with special characters in content
        special_content = "Content with quotes \"double\" and 'single' and newlines\nand tabs\t"
        message4 = BasicMessage(content=special_content)
        str_repr4 = str(message4)
        repr_repr4 = repr(message4)

        # Both representations should handle special characters
        if "Content with quotes" not in str_repr4:
            return "Test failed: str() representation does not handle special characters correctly", None

        if "Content with quotes" not in repr_repr4:
            return "Test failed: repr() representation does not handle special characters correctly", None

        # Test 5: Verify that str() and repr() produce different formats
        # repr() should use repr() formatting for strings (with quotes), str() should not
        if str_repr1 == repr_repr1:
            return "Test failed: str() and repr() should produce different representations", None

        # Test 6: Verify that repr() representation contains quoted strings (more detailed)
        # repr() should use {content!r} which adds quotes around strings
        if "'" not in repr_repr1 and '"' not in repr_repr1:
            return "Test failed: repr() should contain quoted string representations", None

        # Test 7: Verify format consistency - both should start with "BasicMessage("
        if not str_repr1.startswith("BasicMessage(") or not str_repr1.endswith(")"):
            return "Test failed: str() representation format is incorrect", None

        if not repr_repr1.startswith("BasicMessage(") or not repr_repr1.endswith(")"):
            return "Test failed: repr() representation format is incorrect", None

        # Test 8: Test with None-like content (edge case)
        message5 = BasicMessage(content="None")
        str_repr5 = str(message5)
        repr_repr5 = repr(message5)

        if "None" not in str_repr5 or "None" not in repr_repr5:
            return "Test failed: None-like content not handled correctly in string representations", None

        # Test 9: Verify that headers are properly formatted in both representations
        # Headers should appear as dictionaries in both cases
        if "uuid" not in str_repr1 or "{" not in str_repr1:
            return "Test failed: Headers not properly formatted in str() representation", None

        if "uuid" not in repr_repr1 or "{" not in repr_repr1:
            return "Test failed: Headers not properly formatted in repr() representation", None

        # Test 10: Test consistency - calling str()/repr() multiple times should give same result
        if str(message1) != str(message1):
            return "Test failed: str() representation is not consistent across multiple calls", None

        if repr(message1) != repr(message1):
            return "Test failed: repr() representation is not consistent across multiple calls", None

        # All tests passed
        return "BasicMessage string representation test passed: All str() and repr() tests successful", None

    except Exception as e:
        return f"Test failed with exception: {str(e)}", None
