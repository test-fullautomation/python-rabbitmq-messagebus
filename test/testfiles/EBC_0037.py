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
# EBC_0037.py
#
# Test case for EBC_0037: Sending to an unroutable routing key MUST raise an exception when on_unroutable="raise".
#
# --------------------------------------------------------------------------------------------------------------
import asyncio
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
    Test case EBC_0037: ConfigureUnroutablePolicy (mode=return, on_unroutable=raise)

    Expectation:
      - Sending to an unroutable routing key MUST raise an exception when on_unroutable="raise".

    Note:
      - With aio-pika, exceptions raised inside basic.return callback may NOT propagate to `await send()`.
        Therefore we wrap the return-callback to capture the exception via a Future.
    """

    oEventBusClient = None
    try:
        config_file = os.path.join(config_folder_path, 'config_topic.jsonp')

        # Configure policy: return unroutable messages to the sender and raise on unroutable
        config_unrout = ConfigureUnroutablePolicy(
            mode="return",
            alternate_exchange=None,
            on_unroutable="raise",
        )

        # Build client without connecting yet, so we can force a unique exchange name (avoid broker collisions)
        oEventBusClient = await EventBusClient.from_config(
            config_file,
            startup_policy=config_unrout,
            start_connection=False
        )

        # Ensure unique exchange for this test run to avoid PRECONDITION_FAILED with existing exchanges
        oEventBusClient.exchange_handler.exchange_name = f"unroutable_return_raise_{uuid.uuid4().hex}"

        # ------------------------------------------------------------------------------------------
        # Capture exception raised inside the aio-pika basic.return callback (ExchangeHandler._on_basic_return)
        # ------------------------------------------------------------------------------------------
        loop = asyncio.get_running_loop()
        unroutable_cb_exc_fut = loop.create_future()

        # Wrap BEFORE connect() so that connect() registers the wrapped callback
        if hasattr(oEventBusClient.exchange_handler, "_on_basic_return"):
            orig_on_basic_return = oEventBusClient.exchange_handler._on_basic_return

            def _wrapped_on_basic_return(sender, *args, **kwargs):
                try:
                    return orig_on_basic_return(sender, *args, **kwargs)
                except Exception as e:
                    if not unroutable_cb_exc_fut.done():
                        unroutable_cb_exc_fut.set_result(e)
                    # keep behavior identical (aio-pika will log this)
                    raise

            # Replace callback method on instance
            oEventBusClient.exchange_handler._on_basic_return = _wrapped_on_basic_return

        await oEventBusClient.connect()
        await wait_for_client_connected(oEventBusClient)

        # No subscriber binds this routing key => unroutable
        routing_key = "unroutable.test.raise"
        test_message = SimpleTestMessage("unroutable-raise")

        # 1) Try to catch direct exception (in case implementation changes to raise from send())
        try:
            await oEventBusClient.send(routing_key, test_message)
        except Exception as e:
            s = str(e).lower()
            # Guard against false positives like connection errors: require some unroutable signal
            if ("no_route" in s) or ("no route" in s) or ("unrout" in s) or ("return" in s):
                return "Unroutable exception raised", oEventBusClient
            return f"BUG: Unexpected exception type/content: {type(e).__name__}: {e}", oEventBusClient

        # 2) If send() did not raise, check whether the exception was raised in the return callback
        try:
            e_cb = await asyncio.wait_for(unroutable_cb_exc_fut, timeout=1.0)
        except asyncio.TimeoutError:
            return "BUG: No exception raised for unroutable message (neither send() nor return-callback)", oEventBusClient

        s_cb = str(e_cb).lower()
        if ("no_route" in s_cb) or ("no route" in s_cb) or ("unrout" in s_cb) or ("return" in s_cb):
            return "Unroutable exception raised", oEventBusClient

        return f"BUG: Unexpected callback exception type/content: {type(e_cb).__name__}: {e_cb}", oEventBusClient

    except Exception:
        # Let infrastructure errors propagate (should be visible in component_test output)
        raise