# **************************************************************************************************************
#
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
#
# **************************************************************************************************************
#
# TestConfig.py
#
# Nguyen The Dai Duong - MS/EMC-TE-XC
# Derive from the component test of JsonPreprocessor https://github.com/test-fullautomation/python-jsonpreprocessor/tree/develop/test
#
# 11.07.2025
#
# --------------------------------------------------------------------------------------------------------------

listofdictUsecases = []

# the following keys are optional, all other keys are mandatory.
# dictUsecase['HINT']         = None
# dictUsecase['COMMENT']      = None
# dictUsecase['USERAWPATH']   = False # if True, 'TESTFILE' will not be normalized

# --------------------------------------------------------------------------------------------------------------

# If both 'EXPECTEDEXCEPTION' and 'EXPECTEDRETURN' are None, the check of values returned from MessageBus is 
# skipped and the test case result is UNKNOWN.

# --------------------------------------------------------------------------------------------------------------
#TM***
# --------------------------------------------------------------------------------------------------------------
dictUsecase = {}
dictUsecase['TESTID']            = "EBC_0001"
dictUsecase['DESCRIPTION']       = "TBD"
dictUsecase['EXPECTATION']       = "TBD"
dictUsecase['SECTION']           = "TBD"
dictUsecase['SUBSECTION']        = "GOODCASE"
dictUsecase['HINT']              = None
dictUsecase['COMMENT']           = None
dictUsecase['TESTFILE']          = r"TBD"
dictUsecase['EXPECTEDEXCEPTION'] = None
dictUsecase['EXPECTEDRETURN']    = """
TBD
"""
listofdictUsecases.append(dictUsecase)
del dictUsecase
# --------------------------------------------------------------------------------------------------------------
dictUsecase = {}
dictUsecase['TESTID']            = "EBC_0002"
dictUsecase['DESCRIPTION']       = "TBD"
dictUsecase['EXPECTATION']       = "TBD"
dictUsecase['SECTION']           = "TBD"
dictUsecase['SUBSECTION']        = "GOODCASE"
dictUsecase['HINT']              = None
dictUsecase['COMMENT']           = None
dictUsecase['TESTFILE']          = r"TBD"
dictUsecase['EXPECTEDEXCEPTION'] = None
dictUsecase['EXPECTEDRETURN']    = """
TBD
"""
listofdictUsecases.append(dictUsecase)
del dictUsecase
# --------------------------------------------------------------------------------------------------------------

# --------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------
