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
# test_09_ControlMessage_BADCASE.py
#
# XC-HWP/ESW3-Queckenstedt
#
# 29.01.2026 - 15:13:45
#
# --------------------------------------------------------------------------------------------------------------

import pytest
from pytestlibs.CExecute import CExecute

# --------------------------------------------------------------------------------------------------------------

class Test_ControlMessage_BADCASE:

# --------------------------------------------------------------------------------------------------------------
   # Expected: Exception should be raised when ControlMessage is created with invalid roles data type (non-list)
   @pytest.mark.parametrize(
      "Description", ["Test ControlMessage with invalid roles data type",]
   )
   def test_EBC_0032(self, Description):
      nReturn = CExecute.Execute("EBC_0032")
      assert nReturn == 0
# --------------------------------------------------------------------------------------------------------------
   # Expected: Exception should be raised when ControlMessage is created with invalid kind data type (non-string)
   @pytest.mark.parametrize(
      "Description", ["Test ControlMessage with invalid kind data type",]
   )
   def test_EBC_0033(self, Description):
      nReturn = CExecute.Execute("EBC_0033")
      assert nReturn == 0
# --------------------------------------------------------------------------------------------------------------
   # Expected: Exception should be raised when ControlMessage is created with invalid instance_id data type (non-string)
   @pytest.mark.parametrize(
      "Description", ["Test ControlMessage with invalid instance_id data type",]
   )
   def test_EBC_0034(self, Description):
      nReturn = CExecute.Execute("EBC_0034")
      assert nReturn == 0
# --------------------------------------------------------------------------------------------------------------
   # Expected: Exception should be raised when ControlMessage is created with invalid ts data type (non-numeric)
   @pytest.mark.parametrize(
      "Description", ["Test ControlMessage with invalid ts (timestamp)",]
   )
   def test_EBC_0035(self, Description):
      nReturn = CExecute.Execute("EBC_0035")
      assert nReturn == 0
# --------------------------------------------------------------------------------------------------------------
