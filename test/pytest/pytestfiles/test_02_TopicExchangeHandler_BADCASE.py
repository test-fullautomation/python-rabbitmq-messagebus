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
# test_02_TopicExchangeHandler_BADCASE.py
#
# XC-HWP/ESW3-Queckenstedt
#
# 11.08.2025 - 15:37:41
#
# --------------------------------------------------------------------------------------------------------------

import pytest
from pytestlibs.CExecute import CExecute

# --------------------------------------------------------------------------------------------------------------

class Test_TopicExchangeHandler_BADCASE:

# --------------------------------------------------------------------------------------------------------------
   # Expected: Exception should be raised when using invalid routing key format
   @pytest.mark.parametrize(
      "Description", ["Send message with malformed routing key pattern",]
   )
   def test_EBC_0007(self, Description):
      nReturn = CExecute.Execute("EBC_0007")
      assert nReturn == 0
# --------------------------------------------------------------------------------------------------------------
   # Expected: Exception should be raised when using invalid wildcard in routing keys
   @pytest.mark.parametrize(
      "Description", ["Use invalid wildcard in routing key",]
   )
   def test_EBC_0008(self, Description):
      nReturn = CExecute.Execute("EBC_0008")
      assert nReturn == 0
# --------------------------------------------------------------------------------------------------------------
   # Expected: Exception should be raised when using routing key exceeding maximum length
   @pytest.mark.parametrize(
      "Description", ["Send message with routing key exceeding maximum length",]
   )
   def test_EBC_0009(self, Description):
      nReturn = CExecute.Execute("EBC_0009")
      assert nReturn == 0
# --------------------------------------------------------------------------------------------------------------
   # Expected: Exception should be raised when message serialization fails due to encoding issues
   @pytest.mark.parametrize(
      "Description", ["Topic pattern matching fails due to encoding/serialization issues",]
   )
   def test_EBC_0010(self, Description):
      nReturn = CExecute.Execute("EBC_0010")
      assert nReturn == 0
# --------------------------------------------------------------------------------------------------------------
