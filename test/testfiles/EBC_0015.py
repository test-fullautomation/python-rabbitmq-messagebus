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
# EBC_0015.py
#
# Test case for EBC_0015: Test multiple publishers with different routing patterns
# using Reverse Topic Exchange (x-rtopic) where patterns and keys are reversed from standard topic exchange
#
# --------------------------------------------------------------------------------------------------------------

import os

from testutils.messages.simple_test_message import SimpleTestMessage
from testutils.polling_utils import wait_for_client_connected, poll_until_condition, PollingTimeoutError
from EventBusClient.event_bus_client import EventBusClient

async def test(config_folder_path):
    """
    Test case EBC_0015: Test multiple publishers with different routing patterns.

    TEST LOGIC FOR REVERSE TOPIC EXCHANGE (x-rtopic):
    In x-rtopic exchange, the matching logic is REVERSED:
    - Bindings (subscriber keys) are treated as LITERAL KEYS
    - Message routing keys are treated as PATTERNS

    This test verifies that multiple publishers using different routing patterns
    can send messages to appropriate subscribers.

    Test Scenario:
    1. Set up 4 subscribers with specific literal keys:
       - "notifications.user.email" (for email notifications)
       - "notifications.user.sms" (for SMS notifications)
       - "events.system.startup" (for system events)
       - "events.user.login" (for user events)

    2. Use 3 publishers with different patterns:
       - Publisher 1: "notifications.user.*" (matches both notification subscribers)
       - Publisher 2: "events.*.login" (matches user login subscriber)
       - Publisher 3: "events.system.*" (matches system startup subscriber)

    Expected Results:
    - Notification subscribers should receive messages from Publisher 1
    - User login subscriber should receive message from Publisher 2
    - System startup subscriber should receive message from Publisher 3

    Args:
        config_folder_path: Path to the folder containing config files

    Returns:
        tuple: (result_message, oEventBusClient) for proper cleanup
    """

    oEventBusClient = None

    # Storage for received messages from each subscriber
    email_subscriber_messages = []
    sms_subscriber_messages = []
    system_subscriber_messages = []
    login_subscriber_messages = []

    # In x-rtopic exchange: subscribers bind to SPECIFIC keys (treated as literals)
    email_subscriber_key = "notifications.user.email"
    sms_subscriber_key = "notifications.user.sms"
    system_subscriber_key = "events.system.startup"
    login_subscriber_key = "events.user.login"

    # Publishers use WILDCARD PATTERNS that should match specific subscriber keys
    publisher1_pattern = "notifications.user.*"  # Should match email and SMS subscribers
    publisher2_pattern = "events.*.login"        # Should match login subscriber
    publisher3_pattern = "events.system.*"       # Should match system subscriber

    # Test messages from each publisher
    publisher1_message = "Notification from Publisher 1"
    publisher2_message = "Login event from Publisher 2"
    publisher3_message = "System event from Publisher 3"

    # Callback functions for each subscriber
    async def email_subscriber_callback(message, headers):
        """Callback for email notification subscriber"""
        email_subscriber_messages.append(message.get_value())

    async def sms_subscriber_callback(message, headers):
        """Callback for SMS notification subscriber"""
        sms_subscriber_messages.append(message.get_value())

    async def system_subscriber_callback(message, headers):
        """Callback for system event subscriber"""
        system_subscriber_messages.append(message.get_value())

    async def login_subscriber_callback(message, headers):
        """Callback for login event subscriber"""
        login_subscriber_messages.append(message.get_value())

    try:
        # Create EventBusClient from config file (uses XRTopicExchangeHandler)
        config_file = os.path.join(config_folder_path, 'config_rtopic.jsonp')
        oEventBusClient = await EventBusClient.from_config(config_file)

        # Set up multiple subscribers with SPECIFIC KEYS (treated as literals in x-rtopic)
        await oEventBusClient.on(email_subscriber_key, SimpleTestMessage, email_subscriber_callback)
        await oEventBusClient.on(sms_subscriber_key, SimpleTestMessage, sms_subscriber_callback)
        await oEventBusClient.on(system_subscriber_key, SimpleTestMessage, system_subscriber_callback)
        await oEventBusClient.on(login_subscriber_key, SimpleTestMessage, login_subscriber_callback)

        # Wait for client to be connected before sending messages
        await wait_for_client_connected(oEventBusClient)

        # Publisher 1: Send message using pattern that should match email and SMS subscribers
        test_message1 = SimpleTestMessage(publisher1_message)
        await oEventBusClient.send(publisher1_pattern, test_message1)

        # Publisher 2: Send message using pattern that should match login subscriber
        test_message2 = SimpleTestMessage(publisher2_message)
        await oEventBusClient.send(publisher2_pattern, test_message2)

        # Publisher 3: Send message using pattern that should match system subscriber
        test_message3 = SimpleTestMessage(publisher3_message)
        await oEventBusClient.send(publisher3_pattern, test_message3)

        # Wait for messages to be processed by all subscribers
        def expected_messages_received():
            return (len(email_subscriber_messages) >= 1 and      # Should receive from Publisher 1
                   len(sms_subscriber_messages) >= 1 and        # Should receive from Publisher 1
                   len(system_subscriber_messages) >= 1 and     # Should receive from Publisher 3
                   len(login_subscriber_messages) >= 1)         # Should receive from Publisher 2

        try:
            await poll_until_condition(expected_messages_received, timeout_seconds=10.0, poll_interval=0.2)
        except PollingTimeoutError:
            result = f"Not all subscribers received expected messages within timeout. Email: {len(email_subscriber_messages)}, SMS: {len(sms_subscriber_messages)}, System: {len(system_subscriber_messages)}, Login: {len(login_subscriber_messages)}"
            return result, oEventBusClient

        # Verify each subscriber received the correct messages
        success = True
        error_details = []

        # Email subscriber should receive message from Publisher 1
        if len(email_subscriber_messages) != 1 or email_subscriber_messages[0] != publisher1_message:
            error_details.append(f"Email subscriber expected 1 message '{publisher1_message}', got {len(email_subscriber_messages)} messages: {email_subscriber_messages}")
            success = False

        # SMS subscriber should receive message from Publisher 1
        if len(sms_subscriber_messages) != 1 or sms_subscriber_messages[0] != publisher1_message:
            error_details.append(f"SMS subscriber expected 1 message '{publisher1_message}', got {len(sms_subscriber_messages)} messages: {sms_subscriber_messages}")
            success = False

        # System subscriber should receive message from Publisher 3
        if len(system_subscriber_messages) != 1 or system_subscriber_messages[0] != publisher3_message:
            error_details.append(f"System subscriber expected 1 message '{publisher3_message}', got {len(system_subscriber_messages)} messages: {system_subscriber_messages}")
            success = False

        # Login subscriber should receive message from Publisher 2
        if len(login_subscriber_messages) != 1 or login_subscriber_messages[0] != publisher2_message:
            error_details.append(f"Login subscriber expected 1 message '{publisher2_message}', got {len(login_subscriber_messages)} messages: {login_subscriber_messages}")
            success = False

        if success:
            result = "All subscribers received expected messages from multiple publishers with different patterns"
            return result, oEventBusClient
        else:
            result = f"Multiple publisher routing test failed: {'; '.join(error_details)}"
            return result, oEventBusClient

    except Exception as e:
        result = f"Error during multiple publisher routing test: {str(e)}"
        return result, oEventBusClient
