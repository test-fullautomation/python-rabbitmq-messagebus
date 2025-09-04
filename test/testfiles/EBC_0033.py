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
# EBC_0033.py
#
# Test case for EBC_0033: Test ControlMessage with invalid kind data type
#
# --------------------------------------------------------------------------------------------------------------

import os
import sys

# Add parent directory to path to access test modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from EventBusClient.message.control_message import ControlMessage


async def test(config_folder_path):
    """
    Test case EBC_0033: Test ControlMessage with invalid kind data type.

    This test verifies that ControlMessage should validate input and raise TypeError
    when kind is not a string but another data type like int, list, dict, etc.

    The implementation should validate that:
    1. kind parameter must be a string or None
    2. TypeError should be raised for invalid types like int, list, dict, etc.

    Args:
        config_folder_path: Path to the folder containing config files (not used in this test)

    Returns:
        tuple: (result_message, None) - Should raise TypeError before returning
    """

    try:
        # This SHOULD raise TypeError according to validation logic
        message = ControlMessage(
            kind=123,  # Should be str or None, not int
            roles=["test_role"]
        )

        # If we reach here, the implementation failed to validate - this is the bug
        # Return a message indicating the test found a bug in the implementation
        return f"BUG: ControlMessage accepted invalid kind type 'int' when str or None was expected", None

    except TypeError as e:
        # This is what SHOULD happen when the implementation is working correctly
        # Let the exception propagate to the test framework for proper validation
        raise

    except Exception as e:
        # Any other exception - let it propagate as well
        raise
