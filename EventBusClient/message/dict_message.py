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
# File: dict_message.py
#
# Initially created by Nguyen Huynh Tri Cuong (MS/EMC51) / August 2025.
#
# Description:
#
#   DictMessage: A message that can be initialized from a dictionary.
#
# History:
#
# 12.08.2025 / V 1.0.0 / Nguyen Huynh Tri Cuong
# - Initialize
#
# *******************************************************************************
from EventBusClient.message.base_message import BaseMessage

class DictMessage(BaseMessage):
    """
    DictMessage: A message that can be initialized from a dictionary.
    """

    def __init__(self, data: dict = None):
        super().__init__()
        self.data = data or {}

    @classmethod
    def from_data(cls, data: dict):
        return cls(data)

    def get_value(self):
        return self.data