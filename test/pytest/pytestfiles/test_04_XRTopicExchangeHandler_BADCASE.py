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
# test_04_XRTopicExchangeHandler_BADCASE.py
#
# XC-HWP/ESW3-Queckenstedt
#
# 29.01.2026 - 15:13:45
#
# --------------------------------------------------------------------------------------------------------------

import pytest
from pytestlibs.CExecute import CExecute

# --------------------------------------------------------------------------------------------------------------

class Test_XRTopicExchangeHandler_BADCASE:

# --------------------------------------------------------------------------------------------------------------
   # Expected: Exception should be raised when using null/None values in routing patterns
   @pytest.mark.parametrize(
      "Description", ["Test routing pattern with null or None values",]
   )
   def test_EBC_0017(self, Description):
      nReturn = CExecute.Execute("EBC_0017")
      assert nReturn == 0
# --------------------------------------------------------------------------------------------------------------
   # Expected: Exception should be raised when using routing key exceeding maximum length
   @pytest.mark.parametrize(
      "Description", ["Send message with routing key exceeding maximum length",]
   )
   def test_EBC_0018(self, Description):
      nReturn = CExecute.Execute("EBC_0018")
      assert nReturn == 0
# --------------------------------------------------------------------------------------------------------------
   # Expected: Exception should be raised when message serialization fails with x-rtopic patterns
   @pytest.mark.parametrize(
      "Description", ["Test serialization failure with x-rtopic patterns",]
   )
   def test_EBC_0019(self, Description):
      nReturn = CExecute.Execute("EBC_0019")
      assert nReturn == 0
# --------------------------------------------------------------------------------------------------------------
