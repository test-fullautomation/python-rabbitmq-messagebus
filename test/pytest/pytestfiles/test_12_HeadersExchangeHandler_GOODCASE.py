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
# test_12_HeadersExchangeHandler_GOODCASE.py
#
# XC-HWP/ESW3-Queckenstedt
#
# 29.01.2026 - 15:13:45
#
# --------------------------------------------------------------------------------------------------------------

import pytest
from pytestlibs.CExecute import CExecute

# --------------------------------------------------------------------------------------------------------------

class Test_HeadersExchangeHandler_GOODCASE:

# --------------------------------------------------------------------------------------------------------------
   # Expected: Message successfully sent and received when ALL headers match
   @pytest.mark.parametrize(
      "Description", ["Headers exchange with match_all=True (AND logic)",]
   )
   def test_EBC_0042(self, Description):
      nReturn = CExecute.Execute("EBC_0042")
      assert nReturn == 0
# --------------------------------------------------------------------------------------------------------------
   # Expected: Message successfully sent and received when ANY header matches
   @pytest.mark.parametrize(
      "Description", ["Headers exchange with match_all=False (OR logic)",]
   )
   def test_EBC_0043(self, Description):
      nReturn = CExecute.Execute("EBC_0043")
      assert nReturn == 0
# --------------------------------------------------------------------------------------------------------------
   # Expected: Multiple subscribers receive messages based on their individual header bindings
   @pytest.mark.parametrize(
      "Description", ["Headers exchange with multiple subscribers using different binding criteria",]
   )
   def test_EBC_0044(self, Description):
      nReturn = CExecute.Execute("EBC_0044")
      assert nReturn == 0
# --------------------------------------------------------------------------------------------------------------
   # Expected: Messages are received in the same order they were sent
   @pytest.mark.parametrize(
      "Description", ["Headers exchange message ordering",]
   )
   def test_EBC_0045(self, Description):
      nReturn = CExecute.Execute("EBC_0045")
      assert nReturn == 0
# --------------------------------------------------------------------------------------------------------------
   # Expected: Message with non-matching headers should not be delivered to subscriber
   @pytest.mark.parametrize(
      "Description", ["Headers exchange with non-matching headers",]
   )
   def test_EBC_0046(self, Description):
      nReturn = CExecute.Execute("EBC_0046")
      assert nReturn == 0
# --------------------------------------------------------------------------------------------------------------
   # Expected: Message with partial header match should not be delivered when using AND logic
   @pytest.mark.parametrize(
      "Description", ["Headers exchange partial match with AND logic should not deliver",]
   )
   def test_EBC_0047(self, Description):
      nReturn = CExecute.Execute("EBC_0047")
      assert nReturn == 0
# --------------------------------------------------------------------------------------------------------------
