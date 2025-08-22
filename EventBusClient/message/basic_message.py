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
# File: basic_message.py
#
# Initially created by Nguyen Huynh Tri Cuong (MS/EMC51) / August 2025.
#
# Description:
#
#   BasicMessage: A simple message class that extends BaseMessage.
#
# History:
#
# 12.08.2025 / V 1.0.0 / Nguyen Huynh Tri Cuong
# - Initialize
#
# *******************************************************************************
from EventBusClient.message.base_message import BaseMessage
import uuid

class BasicMessage(BaseMessage):
   """
BasicMessage: A simple message class that extends BaseMessage.

This class can be used to create messages that do not require any additional fields or methods.
It inherits all the functionality from BaseMessage and can be used as a
placeholder for messages that do not need any specific attributes.
   """

   def __init__(self, content: str = "", headers: dict = None):
      """
Initialize a BasicMessage with optional content and headers.

**Arguments:**

* ``content``

  / *Condition*: optional / *Type*: str /

  The content of the message. Defaults to an empty string.

* ``headers``

  / *Condition*: optional / *Type*: dict /

  Additional headers for the message. Defaults to None.
      """
      super().__init__()
      self.content = content
      self.headers = headers if headers is not None else {"uuid": uuid.uuid4().hex}

   def __str__(self):
      """
Return a string representation of the BasicMessage.
      """
      return f"BasicMessage(content={self.content}, headers={self.headers})"
   def __repr__(self):
      """
Return a detailed string representation of the BasicMessage.
      """
      return f"BasicMessage(content={self.content!r}, headers={self.headers!r})"

   def to_dict(self):
      """
Convert the BasicMessage to a dictionary representation.

**Returns:**

  A dictionary containing the content and headers of the message.
      """
      return {
            "content": self.content,
            "headers": self.headers
      }

   @classmethod
   def from_dict(cls, data: dict):
      """
Create a BasicMessage from a dictionary representation.

**Arguments:**

* ``data``

  / *Condition*: required / *Type*: dict /

  A dictionary containing the content and headers of the message.

**Returns:**

  An instance of BasicMessage created from the provided dictionary.
      """
      return cls(content=data.get("content", ""), headers=data.get("headers", {}))

   @classmethod
   def from_data(cls, data):
      """
Create a BasicMessage from raw data.

**Arguments:**

* ``data``

  / *Condition*: required / *Type*: str /

  The raw data to create the message from. This should be a string representation of the message content.

**Returns:**

  An instance of BasicMessage created from the provided data.
      """
      return cls(content=data)

   def get_value(self):
      """
Convert the BasicMessage to raw data.

**Returns:**

  A string representation of the message content.
      """
      return self.content

   def __eq__(self, other):
      """
Check equality between two BasicMessage instances.
      """
      if not isinstance(other, BasicMessage):
          return NotImplemented
      return self.content == other.content and self.headers == other.headers


