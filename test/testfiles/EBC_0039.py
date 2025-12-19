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
# EBC_0039.py
#
# Test case for EBC_0039:  - Sending to an unroutable routing key MUST NOT raise.
#                          - The unroutable message MUST be stored in a cache accessible via the policy or client.
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


def _try_get_cache(obj):
    """Try to extract an unroutable-message cache from either policy or client.

    The concrete API is intentionally flexible (acceptance-test style).
    """
    # common attribute names
    attr_candidates = [
        "_unroutable_cache"
    ]
    for a in attr_candidates:
        if hasattr(obj, a):
            v = getattr(obj, a)
            if isinstance(v, (list, tuple)):
                return v
    # common method names
    method_candidates = [
        "pop_unroutables"
    ]
    for m in method_candidates:
        if hasattr(obj, m) and callable(getattr(obj, m)):
            try:
                v = getattr(obj, m)()
                if isinstance(v, (list, tuple)):
                    return v
            except Exception:
                # ignore and continue searching
                pass
    return None


async def test(config_folder_path):
    """
    Test case EBC_0039: ConfigureUnroutablePolicy (mode=return, on_unroutable=cache)

    Expectation:
      - Sending to an unroutable routing key MUST NOT raise.
      - The unroutable message MUST be stored in a cache accessible via the policy or client.
    """

    oEventBusClient = None
    try:
        config_file = os.path.join(config_folder_path, 'config_topic.jsonp')

        config_unrout = ConfigureUnroutablePolicy(
            mode="return",
            alternate_exchange=None,
            on_unroutable="cache"
        )

        oEventBusClient = await EventBusClient.from_config(
            config_file,
            startup_policy=config_unrout,
            start_connection=False
        )

        oEventBusClient.exchange_handler.exchange_name = f"unroutable_return_cache_{uuid.uuid4().hex}"

        await oEventBusClient.connect()
        await wait_for_client_connected(oEventBusClient)

        routing_key = "unroutable.test.cache"
        test_message = SimpleTestMessage("unroutable-cache")

        try:
            await oEventBusClient.send(routing_key, test_message)
        except Exception as e:
            return f"BUG: Exception raised in cache mode: {type(e).__name__}: {e}", oEventBusClient

        # Give async return-handling a moment
        await asyncio.sleep(0.5)

        cache = _try_get_cache(oEventBusClient)

        if cache is None:
            return "BUG: No unroutable cache interface found on policy/client", oEventBusClient

        if len(cache) < 1:
            return "BUG: Unroutable cache exists but is empty", oEventBusClient

        return "Unroutable message cached", oEventBusClient

    except Exception:
        raise
