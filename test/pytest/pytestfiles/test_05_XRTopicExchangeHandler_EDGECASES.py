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
# test_05_XRTopicExchangeHandler_EDGECASES.py
#
# XC-HWP/ESW3-Queckenstedt
#
# 29.01.2026 - 15:13:45
#
# --------------------------------------------------------------------------------------------------------------

import pytest
from pytestlibs.CExecute import CExecute

# --------------------------------------------------------------------------------------------------------------

class Test_XRTopicExchangeHandler_EDGECASES:

# --------------------------------------------------------------------------------------------------------------
   # Expected: Minimal routing patterns should work correctly with x-rtopic exchange
   @pytest.mark.parametrize(
      "Description", ["Test x-rtopic with minimal routing patterns",]
   )
   def test_EBC_0020(self, Description):
      nReturn = CExecute.Execute("EBC_0020")
      assert nReturn == 0
# --------------------------------------------------------------------------------------------------------------
   # Expected: Deep hierarchical routing patterns should work correctly with x-rtopic exchange
   @pytest.mark.parametrize(
      "Description", ["Test x-rtopic with deep hierarchical routing patterns",]
   )
   def test_EBC_0021(self, Description):
      nReturn = CExecute.Execute("EBC_0021")
      assert nReturn == 0
# --------------------------------------------------------------------------------------------------------------
   # Expected: Overlapping routing patterns should work correctly with x-rtopic exchange
   @pytest.mark.parametrize(
      "Description", ["Test x-rtopic with overlapping routing patterns",]
   )
   def test_EBC_0022(self, Description):
      nReturn = CExecute.Execute("EBC_0022")
      assert nReturn == 0
# --------------------------------------------------------------------------------------------------------------
   # Expected: Empty segments in routing patterns should be handled correctly with x-rtopic exchange
   @pytest.mark.parametrize(
      "Description", ["Test x-rtopic with empty segments in routing patterns",]
   )
   def test_EBC_0023(self, Description):
      nReturn = CExecute.Execute("EBC_0023")
      assert nReturn == 0
# --------------------------------------------------------------------------------------------------------------
