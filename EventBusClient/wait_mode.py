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
# *******************************************************************************
#
# File: wait_mode.py
#
# Initially created by Nguyen Huynh Tri Cuong (MS/EMC51) / October 2025.
#
# Description:
#   This module defines the WaitMode enumeration used to specify different waiting strategies.
#
# History:
#
# 08.10.2025 / V 0.1 / Cuong Nguyen
# - Initialize
#
# *******************************************************************************
from enum import Enum

class WaitMode(Enum):
    """
Enumeration for different wait modes.

    - ALL_IN_GIVEN_ORDER: Wait for all specified messages in the given order.

    - ALL_IN_RANDOM_ORDER: Wait for all specified messages in any order.

    - ANY_OF_GIVEN_MSGS: Wait for any one of the specified messages.
    """
    ALL_IN_GIVEN_ORDER   = 1
    ALL_IN_RANDOM_ORDER  = 2
    ANY_OF_GIVEN_MSGS    = 3
