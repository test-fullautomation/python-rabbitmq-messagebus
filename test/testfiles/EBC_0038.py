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
# EBC_0038.py
#
# Test case for EBC_0038: - Sending to an unroutable routing key MUST NOT raise.
#                         - The provided callback MUST be invoked once for the unroutable message.
#
# --------------------------------------------------------------------------------------------------------------

import asyncio
import os
import sys
import uuid

# Add parent directory to path to access test modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from testutils.messages.simple_test_message import SimpleTestMessage
from testutils.polling_utils import wait_for_messages, wait_for_client_connected, PollingTimeoutError
from EventBusClient.event_bus_client import EventBusClient
from EventBusClient.startup_policy import ConfigureUnroutablePolicy


async def test(config_folder_path):
    """
    Test case EBC_0038: ConfigureUnroutablePolicy (mode=return, on_unroutable=callback)

    Expectation:
      - Sending to an unroutable routing key MUST NOT raise.
      - The provided callback MUST be invoked once for the unroutable message.
    """

    oEventBusClient = None
    callback_events = []

    def on_unroutable_callback(*args, **kwargs):
        # Accept any signature to stay compatible with implementation details
        callback_events.append((args, kwargs))

    try:
        config_file = os.path.join(config_folder_path, 'config_topic.jsonp')

        config_unrout = ConfigureUnroutablePolicy(
            mode="return",
            alternate_exchange=None,
            on_unroutable="callback",
            on_unroutable_callback=on_unroutable_callback
        )

        oEventBusClient = await EventBusClient.from_config(
            config_file,
            startup_policy=config_unrout,
            start_connection=False
        )

        oEventBusClient.exchange_handler.exchange_name = f"unroutable_return_callback_{uuid.uuid4().hex}"

        await oEventBusClient.connect()
        await wait_for_client_connected(oEventBusClient)

        routing_key = "unroutable.test.callback"
        test_message = SimpleTestMessage("unroutable-callback")

        try:
            await oEventBusClient.send(routing_key, test_message)
        except Exception as e:
            return f"BUG: Exception raised in callback mode: {type(e).__name__}: {e}", oEventBusClient

        try:
            await wait_for_messages(callback_events, expected_count=1, timeout_seconds=5.0)
            return "Callback invoked for unroutable message", oEventBusClient
        except PollingTimeoutError:
            return "BUG: Callback not invoked for unroutable message", oEventBusClient

    except Exception:
        raise
