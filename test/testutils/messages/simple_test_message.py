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
# File: simple_test_message.py
#
# Description:
#   SimpleTestMessage: A basic message class for testing purposes that can be properly pickled.
#
# *******************************************************************************

import sys
import os

# Add the project root to the path to access EventBusClient
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from EventBusClient.message.base_message import BaseMessage


class SimpleTestMessage(BaseMessage):
    """Simple test message class for testing purposes."""

    def __init__(self, content=""):
        self.content = content

    @classmethod
    def from_data(cls, data):
        """Create a SimpleTestMessage from data."""
        if isinstance(data, dict) and 'content' in data:
            return cls(data['content'])
        return cls(str(data))

    def get_value(self):
        """Return the content of the message."""
        return self.content
