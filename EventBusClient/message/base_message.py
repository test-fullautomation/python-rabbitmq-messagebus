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
# File: base_message.py
#
# Initially created by Nguyen Huynh Tri Cuong (MS/EMC51) / July 2025.
#
# Description:
#
#   BaseMessage: Abstract base class for messages in the event bus system.
#
# History:
#
# 17.07.2025 / V 1.0.0 / Nguyen Huynh Tri Cuong
# - Initialize
#
# *******************************************************************************
from abc import ABC, abstractmethod

class BaseMessage(ABC):
    """
BaseMessage: Abstract base class for messages in the event bus system.
    """
    @classmethod
    @abstractmethod
    def from_data(cls, data):
        """
Create a message instance from raw data.

**Arguments:**

* ``data``

  / *Condition*: required / *Type*: Any /

  Raw data to create the message instance.
        """
        pass

    @abstractmethod
    def get_value(self):
        """
Get the value of the message.
        """
        pass