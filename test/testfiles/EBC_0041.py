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
# EBC_0041.py
#
# Test case for EBC_0041: When mode="alternate-exchange" and alternate_exchange is provided,
#         a message published to a routing key with NO bindings on the primary exchange
#         MUST be routed to the alternate exchange.
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
    Test case EBC_0041: ConfigureUnroutablePolicy (mode=alternate-exchange)

    Expectation:
      - When mode="alternate-exchange" and alternate_exchange is provided,
        a message published to a routing key with NO bindings on the primary exchange
        MUST be routed to the alternate exchange.
    """

    received_messages = []
    routing_key = "unroutable.test.alternate"
    test_message_content = "alternate-exchange-ok"

    async def alt_callback(message, headers):
        received_messages.append(message.get_value())

    config_file = os.path.join(config_folder_path, 'config_topic.jsonp')
    config_file_fanout = os.path.join(config_folder_path, 'config_fanout.jsonp')

    # Unique exchange names to avoid conflicts with prior test runs
    alt_exchange_name = f"unroutable_alt_{uuid.uuid4().hex}"
    primary_exchange_name = f"unroutable_primary_{uuid.uuid4().hex}"

    primary_client = None
    alt_client = None

    try:
        # 1) Bring up alternate exchange (must exist)
        alt_client = await EventBusClient.from_config(
            config_file_fanout,
            start_connection=False
        )
        alt_client.exchange_handler.exchange_name = alt_exchange_name
        await alt_client.connect()
        await wait_for_client_connected(alt_client)

        await alt_client.on(routing_key, SimpleTestMessage, alt_callback)

        # 2) Bring up primary exchange WITH alternate-exchange policy
        config_unrout = ConfigureUnroutablePolicy(
            mode="alternate-exchange",
            alternate_exchange=alt_exchange_name,
            on_unroutable="log"
        )

        primary_client = await EventBusClient.from_config(
            config_file,
            startup_policy=config_unrout,
            start_connection=False
        )
        primary_client.exchange_handler.exchange_name = primary_exchange_name
        await primary_client.connect()
        await wait_for_client_connected(primary_client)

        # 3) Publish to primary exchange without any bindings there => should go to alternate exchange
        test_message = SimpleTestMessage(test_message_content)
        await primary_client.send(routing_key, test_message)

        try:
            await wait_for_messages(received_messages, expected_count=1, timeout_seconds=5.0)
        except PollingTimeoutError:
            return "BUG: Message was not routed to alternate exchange", None

        if received_messages[0] != test_message_content:
            return f"BUG: Alternate exchange received wrong content: {received_messages[0]}", None

        return "Message routed to alternate exchange", None

    except Exception as e:
        return f"BUG: Unexpected exception: {type(e).__name__}: {e}", None

    finally:
        # Close in reverse order
        try:
            if primary_client is not None:
                await primary_client.close()
        except Exception:
            pass
        try:
            if alt_client is not None:
                await alt_client.close()
        except Exception:
            pass
