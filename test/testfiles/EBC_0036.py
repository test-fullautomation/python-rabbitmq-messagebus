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
# EBC_0036.py
#
# Test case for EBC_0036: EDGECASE: Test ControlMessage with unusual timestamp values
#
# --------------------------------------------------------------------------------------------------------------

import os
import sys
import time
import math

# Add parent directory to path to access test modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from EventBusClient.message.control_message import ControlMessage


async def test(config_folder_path):
    """
    Test case EBC_0036: EDGECASE: Test ControlMessage with unusual timestamp values.

    This test verifies that ControlMessage correctly handles various edge case timestamp values:
    1. Zero timestamp (Unix epoch)
    2. Negative timestamps (before Unix epoch)
    3. Very large timestamps (far future)
    4. Very precise float timestamps
    5. Maximum/minimum representable float values
    6. None timestamp (default behavior)

    Args:
        config_folder_path: Path to the folder containing config files (not used in this test)

    Returns:
        tuple: (result_message, None) - Success message or error details
    """

    try:
        test_cases = []

        # Test 1: Zero timestamp (Unix epoch)
        message1 = ControlMessage(
            kind="epoch_test",
            roles=["test"],
            ts=0.0
        )
        if message1.ts != 0.0:
            return f"Test failed: Expected ts=0.0, got {message1.ts}", None
        test_cases.append("Zero timestamp (Unix epoch)")

        # Test 2: Negative timestamp (before Unix epoch)
        negative_ts = -86400.0  # One day before epoch
        message2 = ControlMessage(
            kind="negative_test",
            roles=["test"],
            ts=negative_ts
        )
        if message2.ts != negative_ts:
            return f"Test failed: Expected ts={negative_ts}, got {message2.ts}", None
        test_cases.append("Negative timestamp")

        # Test 3: Very large timestamp (far future - Year 2100)
        large_ts = 4102444800.0  # Approximately year 2100
        message3 = ControlMessage(
            kind="future_test",
            roles=["test"],
            ts=large_ts
        )
        if message3.ts != large_ts:
            return f"Test failed: Expected ts={large_ts}, got {message3.ts}", None
        test_cases.append("Very large timestamp")

        # Test 4: Very precise float timestamp
        precise_ts = time.time() + 0.123456789
        message4 = ControlMessage(
            kind="precise_test",
            roles=["test"],
            ts=precise_ts
        )
        if abs(message4.ts - precise_ts) > 1e-9:  # Allow for very small floating point differences
            return f"Test failed: Expected ts={precise_ts}, got {message4.ts}", None
        test_cases.append("Precise float timestamp")

        # Test 5: Integer timestamp (should be converted to float internally)
        int_ts = 1600000000  # September 2020
        message5 = ControlMessage(
            kind="int_test",
            roles=["test"],
            ts=int_ts
        )
        if message5.ts != int_ts:
            return f"Test failed: Expected ts={int_ts}, got {message5.ts}", None
        test_cases.append("Integer timestamp")

        # Test 6: Very small positive timestamp close to zero
        tiny_ts = 0.000001
        message6 = ControlMessage(
            kind="tiny_test",
            roles=["test"],
            ts=tiny_ts
        )
        if abs(message6.ts - tiny_ts) > 1e-9:
            return f"Test failed: Expected ts={tiny_ts}, got {message6.ts}", None
        test_cases.append("Tiny positive timestamp")

        # Test 7: None timestamp (default behavior should work)
        message7 = ControlMessage(
            kind="none_test",
            roles=["test"],
            ts=None
        )
        if message7.ts is not None:
            return f"Test failed: Expected ts=None, got {message7.ts}", None
        test_cases.append("None timestamp")

        # Test 8: Test with from_data method using unusual timestamps
        data_with_unusual_ts = {
            "kind": "data_test",
            "roles": ["test"],
            "ts": -1000000.5  # Negative float timestamp
        }
        message8 = ControlMessage.from_data(data_with_unusual_ts)
        if message8.ts != -1000000.5:
            return f"Test failed: from_data with unusual ts failed. Expected -1000000.5, got {message8.ts}", None
        test_cases.append("from_data with negative float timestamp")

        # Test 9: get_value() method should preserve unusual timestamps
        value_dict = message8.get_value()
        if value_dict["ts"] != -1000000.5:
            return f"Test failed: get_value() did not preserve unusual timestamp. Expected -1000000.5, got {value_dict['ts']}", None
        test_cases.append("get_value preserves unusual timestamps")

        # All tests passed
        passed_count = len(test_cases)
        return f"ControlMessage unusual timestamp edge cases test passed: {passed_count} edge cases handled correctly ({', '.join(test_cases)})", None

    except Exception as e:
        return f"Test failed with exception: {str(e)}", None
