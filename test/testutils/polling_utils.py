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
# polling_utils.py
#
# Utility functions for polling operations with timeout and retry logic
#
# --------------------------------------------------------------------------------------------------------------

import asyncio
import time
from typing import Callable, Any, Optional, Union


class PollingTimeoutError(Exception):
    """Exception raised when polling operation times out."""
    pass


async def poll_until_condition(
    condition_func: Callable[[], bool],
    timeout_seconds: float = 5.0,
    poll_interval: float = 0.1,
    error_message: Optional[str] = None
) -> bool:
    """
    Poll until a condition is met or timeout occurs.

    Args:
        condition_func: A callable that returns True when the condition is met
        timeout_seconds: Maximum time to wait in seconds (default: 5.0)
        poll_interval: Time to wait between checks in seconds (default: 0.1)
        error_message: Custom error message for timeout (optional)

    Returns:
        True if condition was met within timeout

    Raises:
        PollingTimeoutError: If timeout is reached before condition is met
        ValueError: If timeout_seconds or poll_interval is negative
    """
    if timeout_seconds < 0:
        raise ValueError("timeout_seconds must be non-negative")
    if poll_interval < 0:
        raise ValueError("poll_interval must be non-negative")

    start_time = time.time()

    while time.time() - start_time < timeout_seconds:
        try:
            if condition_func():
                return True
        except Exception as e:
            raise PollingTimeoutError(f"Error in condition function: {e}")
        await asyncio.sleep(poll_interval)

    if error_message is None:
        error_message = f"Condition not met within {timeout_seconds} seconds"

    raise PollingTimeoutError(error_message)


async def poll_until_count(
    get_count_func: Callable[[], int],
    expected_count: int,
    timeout_seconds: float = 5.0,
    poll_interval: float = 0.1,
    error_message: Optional[str] = None
) -> bool:
    """
    Poll until a specific count is reached or timeout occurs.

    Args:
        get_count_func: A callable that returns the current count
        expected_count: The expected count to reach
        timeout_seconds: Maximum time to wait in seconds (default: 5.0)
        poll_interval: Time to wait between checks in seconds (default: 0.1)
        error_message: Custom error message for timeout (optional)

    Returns:
        True if expected count was reached within timeout

    Raises:
        PollingTimeoutError: If timeout is reached before expected count is met
        ValueError: If timeout_seconds or poll_interval is negative
    """
    if timeout_seconds < 0:
        raise ValueError("timeout_seconds must be non-negative")
    if poll_interval < 0:
        raise ValueError("poll_interval must be non-negative")

    def condition():
        try:
            return get_count_func() >= expected_count
        except Exception as e:
            raise PollingTimeoutError(f"Error in count function: {e}")

    if error_message is None:
        error_message = f"Expected count {expected_count} not reached within {timeout_seconds} seconds"

    return await poll_until_condition(condition, timeout_seconds, poll_interval, error_message)


async def poll_with_max_attempts(
    condition_func: Callable[[], bool],
    max_attempts: int = 10,
    poll_interval: float = 0.5,
    error_message: Optional[str] = None
) -> bool:
    """
    Poll until a condition is met or maximum attempts are reached.

    Args:
        condition_func: A callable that returns True when the condition is met
        max_attempts: Maximum number of attempts (default: 10)
        poll_interval: Time to wait between attempts in seconds (default: 0.5)
        error_message: Custom error message for timeout (optional)

    Returns:
        True if condition was met within max attempts

    Raises:
        PollingTimeoutError: If max attempts are reached before condition is met
        ValueError: If max_attempts is negative or poll_interval is negative
    """
    if max_attempts < 1:
        raise ValueError("max_attempts must be positive")
    if poll_interval < 0:
        raise ValueError("poll_interval must be non-negative")

    for attempt in range(max_attempts):
        try:
            if condition_func():
                return True
        except Exception as e:
            raise PollingTimeoutError(f"Error in condition function: {e}")
        if attempt < max_attempts - 1:  # Don't sleep after last attempt
            await asyncio.sleep(poll_interval)

    if error_message is None:
        error_message = f"Condition not met after {max_attempts} attempts"

    raise PollingTimeoutError(error_message)


async def wait_for_messages(
    messages_list: list,
    expected_count: int,
    timeout_seconds: float = 5.0,
    poll_interval: float = 0.1
) -> bool:
    """
    Wait for a specific number of messages to be received.

    Args:
        messages_list: List that will be populated with received messages
        expected_count: Expected number of messages
        timeout_seconds: Maximum time to wait in seconds (default: 5.0)
        poll_interval: Time to wait between checks in seconds (default: 0.1)

    Returns:
        True if expected number of messages was received within timeout

    Raises:
        PollingTimeoutError: If timeout is reached before expected messages are received
    """
    return await poll_until_count(
        get_count_func=lambda: len(messages_list),
        expected_count=expected_count,
        timeout_seconds=timeout_seconds,
        poll_interval=poll_interval,
        error_message=f"Expected {expected_count} messages, but only received {len(messages_list)} within {timeout_seconds} seconds"
    )


async def wait_for_message_content(
    messages_list: list,
    expected_content: Any,
    timeout_seconds: float = 5.0,
    poll_interval: float = 0.1
) -> bool:
    """
    Wait for a message with specific content to be received.

    Args:
        messages_list: List that will be populated with received messages
        expected_content: Expected message content
        timeout_seconds: Maximum time to wait in seconds (default: 5.0)
        poll_interval: Time to wait between checks in seconds (default: 0.1)

    Returns:
        True if message with expected content was received within timeout

    Raises:
        PollingTimeoutError: If timeout is reached before expected message is received
    """
    def condition():
        return expected_content in messages_list

    return await poll_until_condition(
        condition_func=condition,
        timeout_seconds=timeout_seconds,
        poll_interval=poll_interval,
        error_message=f"Message with content '{expected_content}' not received within {timeout_seconds} seconds"
    )


async def wait_for_message_sequence(
    messages_list: list,
    expected_sequence: list,
    timeout_seconds: float = 5.0,
    poll_interval: float = 0.1
) -> bool:
    """
    Wait for messages to be received in a specific sequence.

    Args:
        messages_list: List that will be populated with received messages
        expected_sequence: Expected sequence of messages
        timeout_seconds: Maximum time to wait in seconds (default: 5.0)
        poll_interval: Time to wait between checks in seconds (default: 0.1)

    Returns:
        True if messages were received in expected sequence within timeout

    Raises:
        PollingTimeoutError: If timeout is reached before expected sequence is received
    """
    def condition():
        return (len(messages_list) >= len(expected_sequence) and
                messages_list[:len(expected_sequence)] == expected_sequence)

    return await poll_until_condition(
        condition_func=condition,
        timeout_seconds=timeout_seconds,
        poll_interval=poll_interval,
        error_message=f"Expected sequence {expected_sequence} not received within {timeout_seconds} seconds. Got: {messages_list}"
    )


async def wait_for_client_connected(
    event_bus_client,
    timeout_seconds: float = 5.0,
    poll_interval: float = 0.1
) -> bool:
    """
    Wait for EventBusClient to be connected.

    Args:
        event_bus_client: EventBusClient instance to check connection status
        timeout_seconds: Maximum time to wait in seconds (default: 5.0)
        poll_interval: Time to wait between checks in seconds (default: 0.1)

    Returns:
        True if client is connected within timeout

    Raises:
        PollingTimeoutError: If timeout is reached before client is connected
        AttributeError: If event_bus_client doesn't have _connected attribute
    """
    def condition():
        if not hasattr(event_bus_client, '_connected'):
            raise AttributeError("EventBusClient instance must have '_connected' attribute")
        return event_bus_client._connected

    return await poll_until_condition(
        condition_func=condition,
        timeout_seconds=timeout_seconds,
        poll_interval=poll_interval,
        error_message=f"EventBusClient not connected within {timeout_seconds} seconds"
    )
