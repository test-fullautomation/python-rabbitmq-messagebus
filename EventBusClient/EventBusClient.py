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
#################################################################################
#
# File: EventBusClient.py
#
# This module .......
#
# History:
#
# 2025-07:
#    - TODO
#
#################################################################################

import os
import sys

from EventBusClient.version import VERSION, VERSION_DATE

class CEventBusClient():
    """
TODO
    """

    def getVersion(self) -> str:
        """
Returns the version of EventBusClient as string.
        """
        return VERSION
    
    def getVersionDate(self) -> str:
        """
Returns the version date of EventBusClient as string.
        """
        return VERSION_DATE

    def __init__(self) -> None:
        """
TODO
        """
        pass

