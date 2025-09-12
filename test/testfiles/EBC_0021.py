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
# EBC_0021.py
#
# Test case for EBC_0021: EDGE CASES: Test x-rtopic with deep hierarchical routing patterns
# using Reverse Topic Exchange (x-rtopic) with complex multi-level hierarchical patterns
#
# --------------------------------------------------------------------------------------------------------------

import os
import sys

# Add parent directory to path to access test modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from testutils.messages.simple_test_message import SimpleTestMessage
from testutils.polling_utils import wait_for_client_connected, poll_until_condition, PollingTimeoutError
from EventBusClient.event_bus_client import EventBusClient

async def test(config_folder_path):
    """
    Test case EBC_0021: Test x-rtopic with deep hierarchical routing patterns.

    TEST LOGIC FOR REVERSE TOPIC EXCHANGE (x-rtopic) WITH DEEP HIERARCHICAL PATTERNS:
    This test focuses on complex multi-level hierarchical routing scenarios for x-rtopic exchange:
    - Deep hierarchical subscriber keys (5+ levels deep)
    - Complex wildcard patterns with multiple wildcards at different positions
    - Testing edge cases with very specific hierarchical matching

    Test Scenarios:
    In x-rtopic exchange: the matching logic is REVERSED:
    - Bindings (subscriber keys) are treated as LITERAL KEYS
    - Message routing keys are treated as PATTERNS

    Deep Hierarchical Pattern: "org.*.dept.*.team.*.project.#"
    - * matches exactly one word at positions 2, 4, and 6
    - # matches zero or more words from position 8 onwards

    Subscriber keys that should match the pattern:
    1. "org.engineering.dept.software.team.backend.project" (minimal # match)
    2. "org.marketing.dept.digital.team.analytics.project.web.dashboard"
    3. "org.finance.dept.accounting.team.audit.project.quarterly.report.2024"
    4. "org.hr.dept.recruitment.team.screening.project.intern.hiring.program.summer"
    5. "org.operations.dept.infrastructure.team.devops.project.ci.cd.pipeline.automation.v2"
    6. "org.research.dept.ai.team.ml.project.nlp.model.training.optimization.hyperparameter.tuning"

    Args:
        config_folder_path: Path to the folder containing config files

    Returns:
        tuple: (result_message, oEventBusClient) for proper cleanup
    """

    oEventBusClient = None
    # Storage for received messages from each subscriber
    subscriber_messages = {
        'engineering': [],
        'marketing': [],
        'finance': [],
        'hr': [],
        'operations': [],
        'research': []
    }

    test_message_content = "Deep hierarchical routing test message"

    # Deep hierarchical subscriber keys (literal keys in x-rtopic)
    subscriber_keys = {
        'engineering': "org.engineering.dept.software.team.backend.project",
        'marketing': "org.marketing.dept.digital.team.analytics.project.web.dashboard",
        'finance': "org.finance.dept.accounting.team.audit.project.quarterly.report.2024",
        'hr': "org.hr.dept.recruitment.team.screening.project.intern.hiring.program.summer",
        'operations': "org.operations.dept.infrastructure.team.devops.project.ci.cd.pipeline.automation.v2",
        'research': "org.research.dept.ai.team.ml.project.nlp.model.training.optimization.hyperparameter.tuning"
    }

    # Deep hierarchical pattern (routing key treated as pattern in x-rtopic)
    complex_routing_pattern = "org.*.dept.*.team.*.project.#"

    # Callback functions for each subscriber
    async def engineering_callback(message, headers):
        """Callback for engineering subscriber"""
        subscriber_messages['engineering'].append(message.get_value())

    async def marketing_callback(message, headers):
        """Callback for marketing subscriber"""
        subscriber_messages['marketing'].append(message.get_value())

    async def finance_callback(message, headers):
        """Callback for finance subscriber"""
        subscriber_messages['finance'].append(message.get_value())

    async def hr_callback(message, headers):
        """Callback for hr subscriber"""
        subscriber_messages['hr'].append(message.get_value())

    async def operations_callback(message, headers):
        """Callback for operations subscriber"""
        subscriber_messages['operations'].append(message.get_value())

    async def research_callback(message, headers):
        """Callback for research subscriber"""
        subscriber_messages['research'].append(message.get_value())

    callbacks = {
        'engineering': engineering_callback,
        'marketing': marketing_callback,
        'finance': finance_callback,
        'hr': hr_callback,
        'operations': operations_callback,
        'research': research_callback
    }

    try:
        # Create EventBusClient from config file (uses XRTopicExchangeHandler)
        config_file = os.path.join(config_folder_path, 'config_rtopic.jsonp')
        oEventBusClient = await EventBusClient.from_config(config_file)

        # Set up subscribers with deep hierarchical LITERAL KEYS
        for dept_name, subscriber_key in subscriber_keys.items():
            await oEventBusClient.on(subscriber_key, SimpleTestMessage, callbacks[dept_name])

        # Wait for client to be connected before sending message
        await wait_for_client_connected(oEventBusClient)

        # Send message using deep hierarchical PATTERN
        test_message = SimpleTestMessage(test_message_content)
        await oEventBusClient.send(complex_routing_pattern, test_message)

        # Wait for messages to be processed by all subscribers
        def all_subscribers_received_message():
            return all(len(messages) >= 1 for messages in subscriber_messages.values())

        try:
            await poll_until_condition(all_subscribers_received_message, timeout_seconds=10.0, poll_interval=0.2)
        except PollingTimeoutError:
            received_counts = {dept: len(messages) for dept, messages in subscriber_messages.items()}
            result = f"Not all subscribers received message within timeout. Received counts: {received_counts}"
            return result, oEventBusClient

        # Verify all subscribers received the correct message
        all_received_correctly = True
        error_details = []

        for dept_name, messages in subscriber_messages.items():
            if len(messages) != 1 or (messages and messages[0] != test_message_content):
                all_received_correctly = False
                expected_key = subscriber_keys[dept_name]
                error_details.append(f"Subscriber '{dept_name}' with key '{expected_key}' failed: expected 1 message '{test_message_content}', got {len(messages)} messages {messages}")

        if all_received_correctly:
            result = f"Deep hierarchical routing patterns test passed: all 6 subscribers received message with complex pattern '{complex_routing_pattern}'"
            return result, oEventBusClient
        else:
            result = f"Deep hierarchical routing patterns test failed: {'; '.join(error_details)}"
            return result, oEventBusClient

    except Exception as e:
        result = f"Error during deep hierarchical routing patterns test: {str(e)}"
        return result, oEventBusClient
