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
# *******************************************************************************
#
# File: custom_message_sample.py
#
# Initially created by Claude Code / January 2026.
#
# Description:
#
#   Demonstrates creating custom message classes with validation,
#   serialization helpers, and type safety.
#
# Usage:
#   python custom_message_sample.py
#
# *******************************************************************************
import asyncio
import logging
import sys
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from enum import Enum

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from EventBusClient.event_bus_client import EventBusClient
from EventBusClient.message.base_message import BaseMessage


# =============================================================================
# Example 1: Simple message with validation
# =============================================================================

class UserMessage(BaseMessage):
    """
    User message with basic validation.
    """
    def __init__(self, user_id: int = None, username: str = None, email: str = None):
        super().__init__()
        self.user_id = user_id
        self.username = username
        self.email = email
        self._validate()

    def _validate(self):
        """Validate message fields."""
        if self.user_id is not None and self.user_id < 0:
            raise ValueError("user_id must be non-negative")
        if self.username and len(self.username) > 50:
            raise ValueError("username must be 50 characters or less")
        if self.email and "@" not in self.email:
            raise ValueError("email must contain @")

    @classmethod
    def from_data(cls, data):
        return cls(
            user_id=data.get("user_id"),
            username=data.get("username"),
            email=data.get("email")
        )

    def get_value(self):
        return self

    def to_dict(self) -> dict:
        """Convert to dictionary for logging/debugging."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email
        }

    def __repr__(self):
        return f"UserMessage(id={self.user_id}, username={self.username!r})"


# =============================================================================
# Example 2: Message with enum status
# =============================================================================

class OrderStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class OrderMessage(BaseMessage):
    """
    Order message with enum status and computed properties.
    """
    def __init__(
        self,
        order_id: str = None,
        customer_id: int = None,
        items: List[dict] = None,
        status: OrderStatus = OrderStatus.PENDING,
        created_at: str = None
    ):
        super().__init__()
        self.order_id = order_id
        self.customer_id = customer_id
        self.items = items or []
        self.status = status if isinstance(status, OrderStatus) else OrderStatus(status)
        self.created_at = created_at or datetime.now().isoformat()

    @classmethod
    def from_data(cls, data):
        status = data.get("status", "pending")
        if isinstance(status, str):
            status = OrderStatus(status)
        return cls(
            order_id=data.get("order_id"),
            customer_id=data.get("customer_id"),
            items=data.get("items", []),
            status=status,
            created_at=data.get("created_at")
        )

    def get_value(self):
        return self

    @property
    def total_items(self) -> int:
        """Total number of items in the order."""
        return sum(item.get("quantity", 1) for item in self.items)

    @property
    def total_price(self) -> float:
        """Total price of the order."""
        return sum(
            item.get("price", 0) * item.get("quantity", 1)
            for item in self.items
        )

    @property
    def is_complete(self) -> bool:
        """Check if order is in a final state."""
        return self.status in (OrderStatus.DELIVERED, OrderStatus.CANCELLED)

    def update_status(self, new_status: OrderStatus) -> 'OrderMessage':
        """Return a new message with updated status."""
        return OrderMessage(
            order_id=self.order_id,
            customer_id=self.customer_id,
            items=self.items,
            status=new_status,
            created_at=self.created_at
        )

    def __repr__(self):
        return f"Order({self.order_id}, status={self.status.value}, items={self.total_items})"


# =============================================================================
# Example 3: Nested message with complex structure
# =============================================================================

class AddressMessage(BaseMessage):
    """Address component of a message."""
    def __init__(self, street: str = None, city: str = None, country: str = None, postal_code: str = None):
        super().__init__()
        self.street = street
        self.city = city
        self.country = country
        self.postal_code = postal_code

    @classmethod
    def from_data(cls, data):
        if data is None:
            return None
        return cls(
            street=data.get("street"),
            city=data.get("city"),
            country=data.get("country"),
            postal_code=data.get("postal_code")
        )

    def get_value(self):
        return self

    def __repr__(self):
        return f"{self.street}, {self.city}, {self.country}"


class ShipmentMessage(BaseMessage):
    """
    Shipment message with nested address objects.
    """
    def __init__(
        self,
        shipment_id: str = None,
        order_id: str = None,
        from_address: AddressMessage = None,
        to_address: AddressMessage = None,
        weight_kg: float = None,
        tracking_number: str = None
    ):
        super().__init__()
        self.shipment_id = shipment_id
        self.order_id = order_id
        self.from_address = from_address
        self.to_address = to_address
        self.weight_kg = weight_kg
        self.tracking_number = tracking_number

    @classmethod
    def from_data(cls, data):
        return cls(
            shipment_id=data.get("shipment_id"),
            order_id=data.get("order_id"),
            from_address=AddressMessage.from_data(data.get("from_address")),
            to_address=AddressMessage.from_data(data.get("to_address")),
            weight_kg=data.get("weight_kg"),
            tracking_number=data.get("tracking_number")
        )

    def get_value(self):
        return self

    def __repr__(self):
        return f"Shipment({self.shipment_id}, {self.from_address.city} -> {self.to_address.city})"


# =============================================================================
# Example 4: Message with equality and hashing for wait operations
# =============================================================================

class EventMessage(BaseMessage):
    """
    Event message with proper equality for wait_for operations.
    """
    def __init__(self, event_type: str = None, source: str = None, payload: dict = None):
        super().__init__()
        self.event_type = event_type
        self.source = source
        self.payload = payload or {}

    @classmethod
    def from_data(cls, data):
        return cls(
            event_type=data.get("event_type"),
            source=data.get("source"),
            payload=data.get("payload", {})
        )

    def get_value(self):
        return self

    def __eq__(self, other):
        """
        Two events are equal if they have the same type and source.
        Payload is not considered for equality (useful for wait operations).
        """
        if isinstance(other, EventMessage):
            return self.event_type == other.event_type and self.source == other.source
        return False

    def __hash__(self):
        """Hash based on type and source for use in sets/dicts."""
        return hash((self.event_type, self.source))

    def __repr__(self):
        return f"Event({self.event_type}, source={self.source!r})"


# =============================================================================
# Demo
# =============================================================================

async def demo(config_path: str):
    """Demonstrate custom message classes."""
    logging.info("Starting custom message demo")
    client = await EventBusClient.from_config(config_path)

    # Demo 1: UserMessage with validation
    logging.info("\n=== Demo 1: UserMessage with validation ===")
    try:
        user = UserMessage(user_id=123, username="john_doe", email="john@example.com")
        logging.info(f"Created valid user: {user}")
        logging.info(f"As dict: {user.to_dict()}")

        # This will raise validation error
        invalid_user = UserMessage(user_id=-1, username="test", email="invalid")
    except ValueError as e:
        logging.info(f"Validation error (expected): {e}")

    # Demo 2: OrderMessage with enum and properties
    logging.info("\n=== Demo 2: OrderMessage with enum status ===")
    order = OrderMessage(
        order_id="ORD-001",
        customer_id=123,
        items=[
            {"name": "Widget", "price": 9.99, "quantity": 2},
            {"name": "Gadget", "price": 19.99, "quantity": 1},
        ],
        status=OrderStatus.PENDING
    )
    logging.info(f"Created order: {order}")
    logging.info(f"Total items: {order.total_items}")
    logging.info(f"Total price: ${order.total_price:.2f}")
    logging.info(f"Is complete: {order.is_complete}")

    # Update status
    shipped_order = order.update_status(OrderStatus.SHIPPED)
    logging.info(f"Updated order: {shipped_order}")

    # Demo 3: Nested ShipmentMessage
    logging.info("\n=== Demo 3: ShipmentMessage with nested addresses ===")
    shipment = ShipmentMessage(
        shipment_id="SHIP-001",
        order_id="ORD-001",
        from_address=AddressMessage(
            street="123 Warehouse St",
            city="Chicago",
            country="USA",
            postal_code="60601"
        ),
        to_address=AddressMessage(
            street="456 Customer Ave",
            city="New York",
            country="USA",
            postal_code="10001"
        ),
        weight_kg=2.5,
        tracking_number="1Z999AA10123456784"
    )
    logging.info(f"Created shipment: {shipment}")

    # Demo 4: EventMessage with equality
    logging.info("\n=== Demo 4: EventMessage with equality ===")
    event1 = EventMessage(event_type="user.created", source="auth-service", payload={"user_id": 1})
    event2 = EventMessage(event_type="user.created", source="auth-service", payload={"user_id": 2})
    event3 = EventMessage(event_type="user.updated", source="auth-service")

    logging.info(f"event1: {event1}")
    logging.info(f"event2: {event2}")
    logging.info(f"event1 == event2: {event1 == event2} (same type/source, different payload)")
    logging.info(f"event1 == event3: {event1 == event3} (different type)")

    # Demo 5: Send and receive custom messages
    logging.info("\n=== Demo 5: Send and receive custom messages ===")

    received_orders = []

    async def order_handler(msg: OrderMessage, headers: dict):
        received_orders.append(msg)
        logging.info(f"Received order: {msg}, total=${msg.total_price:.2f}")

    await client.on("demo.orders", OrderMessage, order_handler)

    # Send some orders
    for i in range(3):
        test_order = OrderMessage(
            order_id=f"TEST-{i}",
            customer_id=i,
            items=[{"name": f"Item-{i}", "price": 10.0 * (i + 1), "quantity": i + 1}]
        )
        await client.send("demo.orders", test_order)

    await asyncio.sleep(2)  # Wait for messages
    logging.info(f"Received {len(received_orders)} orders")

    await client.close()
    logging.info("\nDemo complete!")


def main():
    config_path = "../config/config.jsonp"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    asyncio.run(demo(config_path))


if __name__ == "__main__":
    main()
