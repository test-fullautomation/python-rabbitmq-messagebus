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
# test_03_XRTopicExchangeHandler_GOODCASE.py
#
# XC-HWP/ESW3-Queckenstedt
#
# 29.01.2026 - 15:13:45
#
# --------------------------------------------------------------------------------------------------------------

import pytest
from pytestlibs.CExecute import CExecute

# --------------------------------------------------------------------------------------------------------------

class Test_XRTopicExchangeHandler_GOODCASE:

# --------------------------------------------------------------------------------------------------------------
   # Expected: Message successfully sent and received by all subscribers using wildcard pattern
   @pytest.mark.parametrize(
      "Description", ["Send message with single wildcard (*) in routing key to multiple subscribers",]
   )
   def test_EBC_0011(self, Description):
      nReturn = CExecute.Execute("EBC_0011")
      assert nReturn == 0
# --------------------------------------------------------------------------------------------------------------
   # Expected: Message successfully sent and received by all subscribers using multi-level wildcard pattern
   @pytest.mark.parametrize(
      "Description", ["Send message with multi-level wildcard (#) in routing key to multiple subscribers",]
   )
   def test_EBC_0012(self, Description):
      nReturn = CExecute.Execute("EBC_0012")
      assert nReturn == 0
# --------------------------------------------------------------------------------------------------------------
   # Expected: Message successfully sent and received by all subscribers using mixed wildcard patterns (* and #) in single routing key
   @pytest.mark.parametrize(
      "Description", ["Test mixed wildcard patterns in single routing key",]
   )
   def test_EBC_0013(self, Description):
      nReturn = CExecute.Execute("EBC_0013")
      assert nReturn == 0
# --------------------------------------------------------------------------------------------------------------
   # Expected: Messages arrive in the same order they are sent using x-rtopic exchange
   @pytest.mark.parametrize(
      "Description", ["Test message order preservation in x-rtopic exchange",]
   )
   def test_EBC_0014(self, Description):
      nReturn = CExecute.Execute("EBC_0014")
      assert nReturn == 0
# --------------------------------------------------------------------------------------------------------------
   # Expected: Multiple publishers using different routing patterns can send to appropriate subscribers using x-rtopic exchange
   @pytest.mark.parametrize(
      "Description", ["Test multiple publishers with different routing patterns",]
   )
   def test_EBC_0015(self, Description):
      nReturn = CExecute.Execute("EBC_0015")
      assert nReturn == 0
# --------------------------------------------------------------------------------------------------------------
   # Expected: Case sensitivity should be respected in x-rtopic pattern matching
   @pytest.mark.parametrize(
      "Description", ["Test case sensitivity in x-rtopic routing patterns",]
   )
   def test_EBC_0016(self, Description):
      nReturn = CExecute.Execute("EBC_0016")
      assert nReturn == 0
# --------------------------------------------------------------------------------------------------------------
