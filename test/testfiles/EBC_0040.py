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
# EBC_0040.py
#
# Test case for EBC_0040: Sending to an unroutable routing key MUST NOT raise (it should only log).
#
# --------------------------------------------------------------------------------------------------------------

import os
import sys
import uuid

# Add parent directory to path to access test modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from testutils.messages.simple_test_message import SimpleTestMessage
from testutils.polling_utils import wait_for_client_connected
from EventBusClient.event_bus_client import EventBusClient
from EventBusClient.startup_policy import ConfigureUnroutablePolicy


async def test(config_folder_path):
    """
    Test case EBC_0040: ConfigureUnroutablePolicy (mode=return, on_unroutable=log)

    Expectation:
      - Sending to an unroutable routing key MUST NOT raise (it should only log).
    """

    oEventBusClient = None
    try:
        config_file = os.path.join(config_folder_path, 'config_topic.jsonp')

        config_unrout = ConfigureUnroutablePolicy(
            mode="return",
            alternate_exchange=None,
            on_unroutable="log"
        )

        oEventBusClient = await EventBusClient.from_config(
            config_file,
            startup_policy=config_unrout,
            start_connection=False
        )

        oEventBusClient.exchange_handler.exchange_name = f"unroutable_return_log_{uuid.uuid4().hex}"

        await oEventBusClient.connect()
        await wait_for_client_connected(oEventBusClient)

        routing_key = "unroutable.test.log"
        test_message = SimpleTestMessage("unroutable-log")

        try:
            await oEventBusClient.send(routing_key, test_message)
        except Exception as e:
            return f"BUG: Exception raised in log mode: {type(e).__name__}: {e}", oEventBusClient

        return "Unroutable message logged", oEventBusClient

    except Exception:
        raise
