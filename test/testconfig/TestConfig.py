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
dictUsecase['DESCRIPTION']       = "Send message from one publisher to one specific subscriber and confirm receipt"
dictUsecase['EXPECTATION']       = "Message successfully sent and received with correct content"
dictUsecase['SECTION']           = "MESSAGE_FLOW"
dictUsecase['SUBSECTION']        = "GOODCASE"
dictUsecase['HINT']              = None
dictUsecase['COMMENT']           = None
dictUsecase['TESTFILE']          = r"EBC_0001.py"
dictUsecase['EXPECTEDEXCEPTION'] = None
dictUsecase['EXPECTEDRETURN']    = "Message received: Hello, World!"
listofdictUsecases.append(dictUsecase)
del dictUsecase
# --------------------------------------------------------------------------------------------------------------
dictUsecase = {}
dictUsecase['TESTID']            = "EBC_0002"
dictUsecase['DESCRIPTION']       = "Ensure messages arrive in same order they are sent"
dictUsecase['EXPECTATION']       = "Messages received in the same order they were sent"
dictUsecase['SECTION']           = "MESSAGE_FLOW"
dictUsecase['SUBSECTION']        = "GOODCASE"
dictUsecase['HINT']              = None
dictUsecase['COMMENT']           = None
dictUsecase['TESTFILE']          = r"EBC_0002.py"
dictUsecase['EXPECTEDEXCEPTION'] = None
dictUsecase['EXPECTEDRETURN']    = "Messages received in correct order: [1, 2, 3, 4, 5]"
listofdictUsecases.append(dictUsecase)
del dictUsecase
# --------------------------------------------------------------------------------------------------------------
dictUsecase = {}
dictUsecase['TESTID']            = "EBC_0003"
dictUsecase['DESCRIPTION']       = "Test one publisher delivering messages to multiple subscribers using the same routing key"
dictUsecase['EXPECTATION']       = "All subscribers receive the same message with correct content"
dictUsecase['SECTION']           = "MESSAGE_FLOW"
dictUsecase['SUBSECTION']        = "GOODCASE"
dictUsecase['HINT']              = None
dictUsecase['COMMENT']           = None
dictUsecase['TESTFILE']          = r"EBC_0003.py"
dictUsecase['EXPECTEDEXCEPTION'] = None
dictUsecase['EXPECTEDRETURN']    = "All 3 subscribers received message: Hello, Multiple Subscribers!"
listofdictUsecases.append(dictUsecase)
del dictUsecase
# --------------------------------------------------------------------------------------------------------------
dictUsecase = {}
dictUsecase['TESTID']            = "EBC_0004"
dictUsecase['DESCRIPTION']       = "Validate multiple publishers can send to a single subscriber without conflict"
dictUsecase['EXPECTATION']       = "Subscriber receives all messages from all publishers correctly"
dictUsecase['SECTION']           = "MESSAGE_FLOW"
dictUsecase['SUBSECTION']        = "GOODCASE"
dictUsecase['HINT']              = None
dictUsecase['COMMENT']           = None
dictUsecase['TESTFILE']          = r"EBC_0004.py"
dictUsecase['EXPECTEDEXCEPTION'] = None
dictUsecase['EXPECTEDRETURN']    = "All 3 messages received successfully: ['Publisher 1 message', 'Publisher 2 message', 'Publisher 3 message']"
listofdictUsecases.append(dictUsecase)
del dictUsecase
