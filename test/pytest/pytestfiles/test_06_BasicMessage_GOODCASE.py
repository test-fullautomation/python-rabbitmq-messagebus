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
# test_06_BasicMessage_GOODCASE.py
#
# XC-HWP/ESW3-Queckenstedt
#
# 29.01.2026 - 15:13:45
#
# --------------------------------------------------------------------------------------------------------------

import pytest
from pytestlibs.CExecute import CExecute

# --------------------------------------------------------------------------------------------------------------

class Test_BasicMessage_GOODCASE:

# --------------------------------------------------------------------------------------------------------------
   # Expected: BasicMessage successfully sent and received with correct content using topic exchange
   @pytest.mark.parametrize(
      "Description", ["Test BasicMessage with topic exchange",]
   )
   def test_EBC_0024(self, Description):
      nReturn = CExecute.Execute("EBC_0024")
      assert nReturn == 0
# --------------------------------------------------------------------------------------------------------------
   # Expected: Message delivered using reverse topic logic where subscriber uses literal key and publisher uses pattern
   @pytest.mark.parametrize(
      "Description", ["Test BasicMessage with x-rtopic reverse routing logic",]
   )
   def test_EBC_0025(self, Description):
      nReturn = CExecute.Execute("EBC_0025")
      assert nReturn == 0
# --------------------------------------------------------------------------------------------------------------
   # Expected: BasicMessage equality comparison should correctly identify equal and non-equal instances
   @pytest.mark.parametrize(
      "Description", ["Test BasicMessage equality comparison between two instances",]
   )
   def test_EBC_0026(self, Description):
      nReturn = CExecute.Execute("EBC_0026")
      assert nReturn == 0
# --------------------------------------------------------------------------------------------------------------
   # Expected: BasicMessage should be correctly created from dictionary representation and maintain data integrity
   @pytest.mark.parametrize(
      "Description", ["Test BasicMessage creation from dictionary representation",]
   )
   def test_EBC_0027(self, Description):
      nReturn = CExecute.Execute("EBC_0027")
      assert nReturn == 0
# --------------------------------------------------------------------------------------------------------------
   # Expected: BasicMessage inequality comparison should correctly identify non-equal instances with different content or headers
   @pytest.mark.parametrize(
      "Description", ["Test BasicMessage inequality with different content or headers",]
   )
   def test_EBC_0028(self, Description):
      nReturn = CExecute.Execute("EBC_0028")
      assert nReturn == 0
# --------------------------------------------------------------------------------------------------------------
   # Expected: Message created successfully with auto-generated UUID header
   @pytest.mark.parametrize(
      "Description", ["Test BasicMessage with empty content and no headers",]
   )
   def test_EBC_0029(self, Description):
      nReturn = CExecute.Execute("EBC_0029")
      assert nReturn == 0
# --------------------------------------------------------------------------------------------------------------
