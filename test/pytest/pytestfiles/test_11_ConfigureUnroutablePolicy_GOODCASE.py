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
# test_11_ConfigureUnroutablePolicy_GOODCASE.py
#
# XC-HWP/ESW3-Queckenstedt
#
# 29.01.2026 - 15:13:45
#
# --------------------------------------------------------------------------------------------------------------

import pytest
from pytestlibs.CExecute import CExecute

# --------------------------------------------------------------------------------------------------------------

class Test_ConfigureUnroutablePolicy_GOODCASE:

# --------------------------------------------------------------------------------------------------------------
   # Expected: An unroutable message should raise (reported by the test as a PASS string)
   @pytest.mark.parametrize(
      "Description", ["ConfigureUnroutablePolicy: mode=return, on_unroutable=raise",]
   )
   def test_EBC_0037(self, Description):
      nReturn = CExecute.Execute("EBC_0037")
      assert nReturn == 0
# --------------------------------------------------------------------------------------------------------------
   # Expected: An unroutable message should trigger the provided callback and not raise
   @pytest.mark.parametrize(
      "Description", ["ConfigureUnroutablePolicy: mode=return, on_unroutable=callback",]
   )
   def test_EBC_0038(self, Description):
      nReturn = CExecute.Execute("EBC_0038")
      assert nReturn == 0
# --------------------------------------------------------------------------------------------------------------
   # Expected: An unroutable message should be cached (store for later) and not raise
   @pytest.mark.parametrize(
      "Description", ["ConfigureUnroutablePolicy: mode=return, on_unroutable=cache",]
   )
   def test_EBC_0039(self, Description):
      nReturn = CExecute.Execute("EBC_0039")
      assert nReturn == 0
# --------------------------------------------------------------------------------------------------------------
   # Expected: An unroutable message should not raise (should be logged)
   @pytest.mark.parametrize(
      "Description", ["ConfigureUnroutablePolicy: mode=return, on_unroutable=log",]
   )
   def test_EBC_0040(self, Description):
      nReturn = CExecute.Execute("EBC_0040")
      assert nReturn == 0
# --------------------------------------------------------------------------------------------------------------
   # Expected: An unroutable message should be routed to the configured alternate exchange
   @pytest.mark.parametrize(
      "Description", ["ConfigureUnroutablePolicy: mode=alternate-exchange",]
   )
   def test_EBC_0041(self, Description):
      nReturn = CExecute.Execute("EBC_0041")
      assert nReturn == 0
# --------------------------------------------------------------------------------------------------------------
