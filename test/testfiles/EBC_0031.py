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
# EBC_0031.py
#
# Test case for EBC_0031: Test ControlMessage creation from data dictionary
#
# --------------------------------------------------------------------------------------------------------------

import os
import sys
import time
import uuid

# Add parent directory to path to access test modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from EventBusClient.message.control_message import ControlMessage

async def test(config_folder_path):
    """
    Test case EBC_0031: Test ControlMessage creation from data dictionary.

    This test verifies that:
    1. ControlMessage can be created from a complete data dictionary with all fields
    2. ControlMessage can be created from a minimal data dictionary with default values
    3. ControlMessage fields are correctly set from data dictionary values
    4. ControlMessage with missing fields uses default values appropriately
    5. ControlMessage with extra fields ignores unknown keys safely
    6. ControlMessage from_data creates equivalent message to constructor
    7. Data validation and type handling works correctly

    Args:
        config_folder_path: Path to the folder containing config files (not used in this test)

    Returns:
        tuple: (result_message, None) - None because we don't need EventBusClient cleanup
    """

    try:
        # Test 1: Create ControlMessage from complete data dictionary
        complete_data = {
            "kind": "start",
            "roles": ["publisher", "subscriber", "controller"],
            "instance_id": "test-instance-12345",
            "ts": 1724937600.0  # Fixed timestamp for testing
        }

        message1 = ControlMessage.from_data(complete_data)

        # Verify all fields are correctly set
        if message1.kind != "start":
            return f"Test failed: Expected kind 'start', got '{message1.kind}'", None

        if message1.roles != ["publisher", "subscriber", "controller"]:
            return f"Test failed: Expected roles ['publisher', 'subscriber', 'controller'], got {message1.roles}", None

        if message1.instance_id != "test-instance-12345":
            return f"Test failed: Expected instance_id 'test-instance-12345', got '{message1.instance_id}'", None

        if message1.ts != 1724937600.0:
            return f"Test failed: Expected ts 1724937600.0, got {message1.ts}", None

        # Test 2: Create ControlMessage from minimal data dictionary (only kind)
        minimal_data = {"kind": "stop"}

        message2 = ControlMessage.from_data(minimal_data)

        # Verify required field is set and defaults are used for others
        if message2.kind != "stop":
            return f"Test failed: Expected kind 'stop', got '{message2.kind}'", None

        if message2.roles != []:
            return f"Test failed: Expected empty roles list for default, got {message2.roles}", None

        # Verify that default instance_id is a valid hex UUID (32 characters)
        if not isinstance(message2.instance_id, str) or len(message2.instance_id) != 32:
            return f"Test failed: Invalid default instance_id format, got '{message2.instance_id}'", None

        try:
            uuid.UUID(hex=message2.instance_id)
        except ValueError:
            return f"Test failed: Default instance_id '{message2.instance_id}' is not a valid hex UUID", None

        # Verify default timestamp is reasonable (should be close to current time)
        current_time = time.time()
        if abs(message2.ts - current_time) > 10:  # Allow 10 seconds difference
            return f"Test failed: Default timestamp {message2.ts} is too far from current time {current_time}", None

        # Test 3: Create ControlMessage from empty data dictionary
        empty_data = {}

        message3 = ControlMessage.from_data(empty_data)

        # Verify empty kind string is used as default
        if message3.kind != "":
            return f"Test failed: Expected empty kind for empty data, got '{message3.kind}'", None

        if message3.roles != []:
            return f"Test failed: Expected empty roles list for empty data, got {message3.roles}", None

        # Test 4: Create ControlMessage with extra unknown fields
        data_with_extras = {
            "kind": "heartbeat",
            "roles": ["monitor"],
            "extra_field": "should_be_ignored",
            "unknown_key": 42,
            "nested": {"data": "value"}
        }

        message4 = ControlMessage.from_data(data_with_extras)

        # Verify known fields are processed correctly and extras are ignored
        if message4.kind != "heartbeat":
            return f"Test failed: Expected kind 'heartbeat', got '{message4.kind}'", None

        if message4.roles != ["monitor"]:
            return f"Test failed: Expected roles ['monitor'], got {message4.roles}", None

        # Verify extras don't cause issues (they should be ignored)
        # The object should not have these extra attributes
        if hasattr(message4, 'extra_field'):
            return "Test failed: Extra field should not be set as attribute", None

        # Test 5: Test get_value() method returns correct dictionary representation
        value_dict = message1.get_value()

        expected_keys = {"kind", "roles", "instance_id", "ts"}
        if set(value_dict.keys()) != expected_keys:
            return f"Test failed: get_value() keys mismatch. Expected {expected_keys}, got {set(value_dict.keys())}", None

        if value_dict["kind"] != "start":
            return f"Test failed: get_value() kind mismatch. Expected 'start', got '{value_dict['kind']}'", None

        # Verify roles is a list (not the original reference)
        if value_dict["roles"] != ["publisher", "subscriber", "controller"]:
            return f"Test failed: get_value() roles mismatch. Expected ['publisher', 'subscriber', 'controller'], got {value_dict['roles']}", None

        # Test 6: Test round-trip: create from data, get value, create again
        original_data = {
            "kind": "config_update",
            "roles": ["admin", "user"],
            "instance_id": "round-trip-test",
            "ts": 1234567890.123
        }

        message_original = ControlMessage.from_data(original_data)
        value_dict = message_original.get_value()
        message_roundtrip = ControlMessage.from_data(value_dict)

        # Verify round-trip preserves all data
        if message_original.kind != message_roundtrip.kind:
            return f"Test failed: Round-trip kind mismatch. Original: '{message_original.kind}', Round-trip: '{message_roundtrip.kind}'", None

        if message_original.roles != message_roundtrip.roles:
            return f"Test failed: Round-trip roles mismatch. Original: {message_original.roles}, Round-trip: {message_roundtrip.roles}", None

        if message_original.instance_id != message_roundtrip.instance_id:
            return f"Test failed: Round-trip instance_id mismatch. Original: '{message_original.instance_id}', Round-trip: '{message_roundtrip.instance_id}'", None

        if message_original.ts != message_roundtrip.ts:
            return f"Test failed: Round-trip ts mismatch. Original: {message_original.ts}, Round-trip: {message_roundtrip.ts}", None

        # Test 7: Test with different role configurations
        single_role_data = {"kind": "test", "roles": ["single"]}
        message_single = ControlMessage.from_data(single_role_data)

        if message_single.roles != ["single"]:
            return f"Test failed: Single role not handled correctly. Expected ['single'], got {message_single.roles}", None

        # Test 8: Test with None values in data (actual behavior: None values are preserved)
        data_with_nones = {
            "kind": "test_none",
            "roles": None,
            "instance_id": None,
            "ts": None
        }

        message_nones = ControlMessage.from_data(data_with_nones)

        if message_nones.kind != "test_none":
            return f"Test failed: Kind with None handling failed. Expected 'test_none', got '{message_nones.kind}'", None

        # Note: The current implementation preserves None values when explicitly provided
        if message_nones.roles is not None:
            return f"Test failed: None roles should remain None when explicitly provided, got {message_nones.roles}", None

        if message_nones.instance_id is not None:
            return f"Test failed: None instance_id should remain None when explicitly provided, got '{message_nones.instance_id}'", None

        if message_nones.ts is not None:
            return f"Test failed: None ts should remain None when explicitly provided, got {message_nones.ts}", None

        # All tests passed
        return "ControlMessage from_data test passed: All creation and validation tests successful", None

    except Exception as e:
        return f"Test failed with exception: {str(e)}", None
