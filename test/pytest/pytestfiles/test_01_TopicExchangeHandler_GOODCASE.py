# **************************************************************************************************************
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
# --------------------------------------------------------------------------------------------------------------
#
# test_01_TopicExchangeHandler_GOODCASE.py
#
# XC-HWP/ESW3-Queckenstedt
#
# 11.08.2025 - 15:37:41
#
# --------------------------------------------------------------------------------------------------------------

import pytest
from pytestlibs.CExecute import CExecute

# --------------------------------------------------------------------------------------------------------------

class Test_TopicExchangeHandler_GOODCASE:

# --------------------------------------------------------------------------------------------------------------
   # Expected: Message successfully sent and received with correct content
   @pytest.mark.parametrize(
      "Description", ["Send message from one publisher to one specific subscriber and confirm receipt",]
   )
   def test_EBC_0001(self, Description):
      nReturn = CExecute.Execute("EBC_0001")
      assert nReturn == 0
# --------------------------------------------------------------------------------------------------------------
   # Expected: Messages received in the same order they were sent
   @pytest.mark.parametrize(
      "Description", ["Ensure messages arrive in same order they are sent",]
   )
   def test_EBC_0002(self, Description):
      nReturn = CExecute.Execute("EBC_0002")
      assert nReturn == 0
# --------------------------------------------------------------------------------------------------------------
   # Expected: All subscribers receive the same message with correct content
   @pytest.mark.parametrize(
      "Description", ["Test one publisher delivering messages to multiple subscribers using the same routing key",]
   )
   def test_EBC_0003(self, Description):
      nReturn = CExecute.Execute("EBC_0003")
      assert nReturn == 0
# --------------------------------------------------------------------------------------------------------------
   # Expected: Subscriber receives all messages from all publishers correctly
   @pytest.mark.parametrize(
      "Description", ["Validate multiple publishers can send to a single subscriber without conflict",]
   )
   def test_EBC_0004(self, Description):
      nReturn = CExecute.Execute("EBC_0004")
      assert nReturn == 0
# --------------------------------------------------------------------------------------------------------------
   # Expected: Messages delivered correctly to subscribers using wildcard routing patterns
   @pytest.mark.parametrize(
      "Description", ["Send message with wildcard routing key patterns (* and #)",]
   )
   def test_EBC_0005(self, Description):
      nReturn = CExecute.Execute("EBC_0005")
      assert nReturn == 0
# --------------------------------------------------------------------------------------------------------------
   # Expected: Messages with different case routing keys should be treated as separate routes
   @pytest.mark.parametrize(
      "Description", ["Verify routing key case sensitivity",]
   )
   def test_EBC_0006(self, Description):
      nReturn = CExecute.Execute("EBC_0006")
      assert nReturn == 0
# --------------------------------------------------------------------------------------------------------------
