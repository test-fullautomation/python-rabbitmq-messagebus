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
# EBC_0035.py
#
# Test case for EBC_0035: Test ControlMessage with invalid ts (timestamp)
#
# --------------------------------------------------------------------------------------------------------------

import os
import sys

# Add parent directory to path to access test modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from EventBusClient.message.control_message import ControlMessage


async def test(config_folder_path):
    """
    Test case EBC_0035: Test ControlMessage with invalid ts (timestamp).

    This test verifies that ControlMessage should validate input and raise TypeError
    when ts is not a number (int or float) but another data type like string, dict, etc.

    The implementation should validate that:
    1. ts parameter must be a number (int or float) or None
    2. TypeError should be raised for invalid types like str, dict, list, etc.

    Args:
        config_folder_path: Path to the folder containing config files (not used in this test)

    Returns:
        tuple: (result_message, None) - Should raise TypeError before returning
    """

    try:
        # This should raise TypeError because ts should be numeric, not string
        message = ControlMessage(
            kind="test_kind",
            roles=["test_role"],
            ts="invalid_string_timestamp"  # Should be int/float, not str
        )

        # If we reach here, the implementation failed to validate - this is unexpected
        return f"BUG: ControlMessage accepted invalid ts type 'str' when number was expected", None

    except TypeError as e:
        # This is what should happen when the implementation validates correctly
        # Let the exception propagate to the test framework for proper validation
        raise

    except Exception as e:
        # Any other exception - let it propagate as well
        raise
