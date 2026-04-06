#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
"""
Headers Exchange Sample:
=======================

This example demonstrates the HeadersExchangeHandler which routes messages
based on header attributes instead of routing keys.

Headers exchanges are useful when:
- You need to route based on multiple attributes
- Routing logic requires AND/OR conditions
- The routing criteria are more complex than simple patterns

Key Concepts:
- x-match=all: ALL specified headers must match (AND logic)
- x-match=any: At least ONE header must match (OR logic)
- Routing key is ignored in headers exchange

Usage:
    python headers_exchange_sample.py
"""

import asyncio
from EventBusClient.event_bus_client import EventBusClient
from EventBusClient.exchange_handler.headers_handler import HeadersExchangeHandler
from EventBusClient.serializer.json_serializer import JsonSerializer
from EventBusClient.message.base_message import BaseMessage


# Define custom message classes
class DocumentMessage(BaseMessage):
    """Message representing a document."""
    def __init__(self, title: str = "", content: str = ""):
        self.title = title
        self.content = content

    @classmethod
    def from_data(cls, data):
        """Create a DocumentMessage from raw data."""
        if isinstance(data, dict):
            return cls(title=data.get("title", ""), content=data.get("content", ""))
        return cls()

    def get_value(self):
        """Get the value of the message."""
        return {"title": self.title, "content": self.content}

    def __repr__(self):
        return f"DocumentMessage(title='{self.title}')"


class ReportMessage(BaseMessage):
    """Message representing a report."""
    def __init__(self, report_id: str = "", data: dict = None):
        self.report_id = report_id
        self.data = data or {}

    @classmethod
    def from_data(cls, data):
        """Create a ReportMessage from raw data."""
        if isinstance(data, dict):
            return cls(report_id=data.get("report_id", ""), data=data.get("data", {}))
        return cls()

    def get_value(self):
        """Get the value of the message."""
        return {"report_id": self.report_id, "data": self.data}

    def __repr__(self):
        return f"ReportMessage(id='{self.report_id}')"


async def subscriber_all_match():
    """
    Subscriber that uses x-match=all (AND logic).
    Only receives messages where ALL specified headers match.
    """
    print("\n=== Subscriber (match ALL headers) ===")

    # Create client with HeadersExchangeHandler
    handler = HeadersExchangeHandler(
        name="documents_exchange",
        serializer=JsonSerializer()
    )
    client = EventBusClient(
        exchange_handler=handler,
        host="localhost",
        port=5672
    )

    await client.connect()
    print("Connected to RabbitMQ")

    # Subscribe to messages where format=pdf AND department=engineering
    # Both headers must match for message to be delivered
    async def handle_engineering_pdf(msg, headers):
        print(f"  [ALL MATCH] Received: {msg}")
        print(f"              Headers: {headers}")

    cache = await client.on(
        routing_key="",  # Ignored in headers exchange
        message_cls=DocumentMessage,
        callback=handle_engineering_pdf,
        binding_headers={"format": "pdf", "department": "engineering"},
        match_all=True  # x-match=all
    )

    print("Subscribed with binding: format=pdf AND department=engineering")
    return client, cache


async def subscriber_any_match():
    """
    Subscriber that uses x-match=any (OR logic).
    Receives messages where ANY of the specified headers match.
    """
    print("\n=== Subscriber (match ANY header) ===")

    handler = HeadersExchangeHandler(
        name="documents_exchange",
        serializer=JsonSerializer()
    )
    client = EventBusClient(
        exchange_handler=handler,
        host="localhost",
        port=5672
    )

    await client.connect()
    print("Connected to RabbitMQ")

    # Subscribe to messages where format=pdf OR priority=high
    # At least one header must match
    async def handle_important_docs(msg, headers):
        print(f"  [ANY MATCH] Received: {msg}")
        print(f"              Headers: {headers}")

    cache = await client.on(
        routing_key="",  # Ignored in headers exchange
        message_cls=DocumentMessage,
        callback=handle_important_docs,
        binding_headers={"format": "pdf", "priority": "high"},
        match_all=False  # x-match=any
    )

    print("Subscribed with binding: format=pdf OR priority=high")
    return client, cache


async def publisher():
    """
    Publisher that sends messages with various headers.
    """
    print("\n=== Publisher ===")

    handler = HeadersExchangeHandler(
        name="documents_exchange",
        serializer=JsonSerializer()
    )
    client = EventBusClient(
        exchange_handler=handler,
        host="localhost",
        port=5672
    )

    await client.connect()
    print("Connected to RabbitMQ")

    # Wait for subscribers to be ready
    await asyncio.sleep(1)

    # Test Case 1: Matches ALL subscriber (format=pdf AND department=engineering)
    print("\n--- Publishing: Engineering PDF (matches ALL subscriber) ---")
    await client.send(
        routing_key="",  # Ignored in headers exchange
        message=DocumentMessage(title="Q4 Engineering Report", content="..."),
        headers={
            "format": "pdf",
            "department": "engineering",
            "author": "john"
        }
    )

    # Test Case 2: Matches ANY subscriber (has priority=high)
    print("\n--- Publishing: High Priority Word Doc (matches ANY subscriber) ---")
    await client.send(
        routing_key="",
        message=DocumentMessage(title="Urgent Notice", content="..."),
        headers={
            "format": "docx",
            "department": "hr",
            "priority": "high"
        }
    )

    # Test Case 3: Matches ANY subscriber (has format=pdf) but NOT ALL (missing department=engineering)
    print("\n--- Publishing: Marketing PDF (matches ANY, not ALL) ---")
    await client.send(
        routing_key="",
        message=DocumentMessage(title="Marketing Brochure", content="..."),
        headers={
            "format": "pdf",
            "department": "marketing",
            "priority": "low"
        }
    )

    # Test Case 4: Matches neither (no matching headers)
    print("\n--- Publishing: Text file (matches NEITHER subscriber) ---")
    await client.send(
        routing_key="",
        message=DocumentMessage(title="Notes", content="..."),
        headers={
            "format": "txt",
            "department": "sales",
            "priority": "low"
        }
    )

    print("\nAll messages published")
    return client


async def main():
    """Run the headers exchange demonstration."""
    print("=" * 60)
    print("Headers Exchange Sample")
    print("=" * 60)
    print("""
This example shows how HeadersExchangeHandler routes messages
based on header attributes instead of routing keys.

Two subscribers will be created:
1. ALL match: Receives only messages with format=pdf AND department=engineering
2. ANY match: Receives messages with format=pdf OR priority=high
    """)

    try:
        # Start subscribers
        client1, cache1 = await subscriber_all_match()
        client2, cache2 = await subscriber_any_match()

        # Start publisher
        pub_client = await publisher()

        # Wait for messages to be processed
        await asyncio.sleep(2)

        print("\n" + "=" * 60)
        print("Summary of message routing:")
        print("=" * 60)
        print("""
Message 1 (Engineering PDF):
  - Headers: format=pdf, department=engineering
  - ALL subscriber: RECEIVED (both headers match)
  - ANY subscriber: RECEIVED (format=pdf matches)

Message 2 (High Priority Word Doc):
  - Headers: format=docx, priority=high
  - ALL subscriber: NOT received (department != engineering)
  - ANY subscriber: RECEIVED (priority=high matches)

Message 3 (Marketing PDF):
  - Headers: format=pdf, department=marketing
  - ALL subscriber: NOT received (department != engineering)
  - ANY subscriber: RECEIVED (format=pdf matches)

Message 4 (Text file):
  - Headers: format=txt, priority=low
  - ALL subscriber: NOT received (no headers match)
  - ANY subscriber: NOT received (no headers match)
        """)

        # Cleanup
        await pub_client.close()
        await client1.close()
        await client2.close()

    except Exception as e:
        print(f"Error: {e}")
        raise


async def simple_example():
    """
    Simplified example showing basic headers exchange usage.
    """
    print("=" * 60)
    print("Simple Headers Exchange Example")
    print("=" * 60)

    # Create handler and client
    handler = HeadersExchangeHandler(
        name="simple_headers_exchange",
        serializer=JsonSerializer()
    )
    client = EventBusClient(
        exchange_handler=handler,
        host="localhost",
        port=5672
    )

    await client.connect()

    # Subscribe to PDF documents from engineering
    messages_received = []

    async def on_message(msg, headers):
        messages_received.append((msg, headers))
        print(f"Received: {msg.title} with headers {headers}")

    await client.on(
        routing_key="",  # Ignored in headers exchange
        message_cls=DocumentMessage,
        callback=on_message,
        binding_headers={"format": "pdf", "department": "engineering"},
        match_all=True
    )

    # Publish a matching message
    await client.send(
        routing_key="",
        message=DocumentMessage(title="Test Document"),
        headers={"format": "pdf", "department": "engineering"}
    )

    await asyncio.sleep(1)

    # Cleanup
    await client.close()

    print(f"\nTotal messages received: {len(messages_received)}")


if __name__ == "__main__":
    # Run the full demonstration
    asyncio.run(main())

    # Or run the simple example
    # asyncio.run(simple_example())
