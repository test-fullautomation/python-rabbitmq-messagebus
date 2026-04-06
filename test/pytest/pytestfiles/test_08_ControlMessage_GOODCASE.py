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
# test_08_ControlMessage_GOODCASE.py
#
# XC-HWP/ESW3-Queckenstedt
#
# 29.01.2026 - 15:13:45
#
# --------------------------------------------------------------------------------------------------------------

import pytest
from pytestlibs.CExecute import CExecute

# --------------------------------------------------------------------------------------------------------------

class Test_ControlMessage_GOODCASE:

# --------------------------------------------------------------------------------------------------------------
   # Expected: ControlMessage created with all fields correctly set from data dictionary
   @pytest.mark.parametrize(
      "Description", ["Test ControlMessage creation from data dictionary",]
   )
   def test_EBC_0031(self, Description):
      nReturn = CExecute.Execute("EBC_0031")
      assert nReturn == 0
# --------------------------------------------------------------------------------------------------------------
