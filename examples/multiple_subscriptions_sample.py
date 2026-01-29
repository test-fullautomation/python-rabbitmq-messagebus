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
# File: multiple_subscriptions_sample.py
#
# Initially created by Claude Code / January 2026.
#
# Description:
#
#   Demonstrates subscribing to multiple topics with different routing keys
#   and handling messages from multiple sources.
#
# Usage:
#   Terminal 1: python multiple_subscriptions_sample.py consumer
#   Terminal 2: python multiple_subscriptions_sample.py producer
#
# *******************************************************************************
import asyncio
import logging
import sys
import os
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from EventBusClient.event_bus_client import EventBusClient
from EventBusClient.message.base_message import BaseMessage


class SensorMessage(BaseMessage):
    """Message from a sensor."""
    def __init__(self, sensor_id: str = None, sensor_type: str = None, value: float = None, unit: str = None):
        super().__init__()
        self.sensor_id = sensor_id
        self.sensor_type = sensor_type
        self.value = value
        self.unit = unit

    @classmethod
    def from_data(cls, data):
        return cls(
            sensor_id=data.get("sensor_id"),
            sensor_type=data.get("sensor_type"),
            value=data.get("value"),
            unit=data.get("unit")
        )

    def get_value(self):
        return self

    def __repr__(self):
        return f"Sensor({self.sensor_id}, {self.sensor_type}={self.value}{self.unit})"


class AlertMessage(BaseMessage):
    """Alert message for threshold violations."""
    def __init__(self, alert_id: str = None, severity: str = None, source: str = None, message: str = None):
        super().__init__()
        self.alert_id = alert_id
        self.severity = severity
        self.source = source
        self.message = message

    @classmethod
    def from_data(cls, data):
        return cls(
            alert_id=data.get("alert_id"),
            severity=data.get("severity"),
            source=data.get("source"),
            message=data.get("message")
        )

    def get_value(self):
        return self

    def __repr__(self):
        return f"Alert({self.severity}: {self.message})"


class SystemMessage(BaseMessage):
    """System status message."""
    def __init__(self, component: str = None, status: str = None, details: str = None):
        super().__init__()
        self.component = component
        self.status = status
        self.details = details

    @classmethod
    def from_data(cls, data):
        return cls(
            component=data.get("component"),
            status=data.get("status"),
            details=data.get("details")
        )

    def get_value(self):
        return self

    def __repr__(self):
        return f"System({self.component}: {self.status})"


# Statistics for tracking
stats = {
    "temperature": 0,
    "humidity": 0,
    "pressure": 0,
    "alerts": 0,
    "system": 0,
}


async def handle_temperature(message: SensorMessage, headers: dict):
    """Handle temperature sensor messages."""
    stats["temperature"] += 1
    logging.info(f"[TEMP] {message}")

    # Check for high temperature alert
    if message.value > 35.0:
        logging.warning(f"[TEMP] High temperature detected: {message.value}C")


async def handle_humidity(message: SensorMessage, headers: dict):
    """Handle humidity sensor messages."""
    stats["humidity"] += 1
    logging.info(f"[HUMID] {message}")


async def handle_pressure(message: SensorMessage, headers: dict):
    """Handle pressure sensor messages."""
    stats["pressure"] += 1
    logging.info(f"[PRESS] {message}")


async def handle_all_sensors(message: SensorMessage, headers: dict):
    """Handle all sensor messages (wildcard subscription)."""
    logging.debug(f"[ALL] Received sensor data: {message}")


async def handle_alerts(message: AlertMessage, headers: dict):
    """Handle alert messages."""
    stats["alerts"] += 1
    if message.severity == "critical":
        logging.critical(f"[ALERT] {message}")
    elif message.severity == "warning":
        logging.warning(f"[ALERT] {message}")
    else:
        logging.info(f"[ALERT] {message}")


async def handle_system(message: SystemMessage, headers: dict):
    """Handle system status messages."""
    stats["system"] += 1
    logging.info(f"[SYSTEM] {message}")


async def consumer(config_path: str):
    """Consumer that subscribes to multiple topics."""
    logging.info("Consumer: Starting with multiple subscriptions")
    client = await EventBusClient.from_config(config_path)

    # Subscribe to specific sensor types
    await client.on("sensors.temperature", SensorMessage, handle_temperature)
    logging.info("Subscribed to: sensors.temperature")

    await client.on("sensors.humidity", SensorMessage, handle_humidity)
    logging.info("Subscribed to: sensors.humidity")

    await client.on("sensors.pressure", SensorMessage, handle_pressure)
    logging.info("Subscribed to: sensors.pressure")

    # Subscribe to alerts
    await client.on("alerts.system", AlertMessage, handle_alerts)
    logging.info("Subscribed to: alerts.system")

    # Subscribe to system status
    await client.on("system.status", SystemMessage, handle_system)
    logging.info("Subscribed to: system.status")

    # Note: For wildcard subscriptions like "sensors.*", you would need
    # to use a topic exchange type. The exact syntax depends on your
    # exchange configuration.

    logging.info("Consumer: All subscriptions active. Waiting for messages...")

    # Keep running and periodically print stats
    try:
        while True:
            await asyncio.sleep(10)
            logging.info(f"Stats: temp={stats['temperature']}, humid={stats['humidity']}, "
                        f"press={stats['pressure']}, alerts={stats['alerts']}, system={stats['system']}")
    except KeyboardInterrupt:
        logging.info("Consumer: Shutting down")
    finally:
        await client.close()


async def producer(config_path: str):
    """Producer that sends messages to multiple topics."""
    logging.info("Producer: Starting")
    client = await EventBusClient.from_config(config_path)

    sensor_count = 0
    alert_count = 0

    try:
        for i in range(30):
            # Send temperature reading
            temp = SensorMessage(
                sensor_id=f"temp-{i % 3}",
                sensor_type="temperature",
                value=round(20 + random.uniform(-5, 20), 1),
                unit="C"
            )
            await client.send("sensors.temperature", temp)
            sensor_count += 1

            # Send humidity reading
            humid = SensorMessage(
                sensor_id=f"humid-{i % 2}",
                sensor_type="humidity",
                value=round(40 + random.uniform(-10, 30), 1),
                unit="%"
            )
            await client.send("sensors.humidity", humid)
            sensor_count += 1

            # Send pressure reading every 3rd iteration
            if i % 3 == 0:
                press = SensorMessage(
                    sensor_id="press-0",
                    sensor_type="pressure",
                    value=round(1013 + random.uniform(-10, 10), 1),
                    unit="hPa"
                )
                await client.send("sensors.pressure", press)
                sensor_count += 1

            # Send occasional alerts
            if random.random() < 0.2:
                severity = random.choice(["info", "warning", "critical"])
                alert = AlertMessage(
                    alert_id=f"alert-{alert_count}",
                    severity=severity,
                    source="sensor-monitor",
                    message=f"Threshold exceeded on iteration {i}"
                )
                await client.send("alerts.system", alert)
                alert_count += 1

            # Send system status every 5 iterations
            if i % 5 == 0:
                status = SystemMessage(
                    component="sensor-gateway",
                    status="healthy",
                    details=f"Processed {sensor_count} readings"
                )
                await client.send("system.status", status)

            await asyncio.sleep(0.3)

        logging.info(f"Producer: Done. Sent {sensor_count} sensor readings, {alert_count} alerts")

    finally:
        await client.close()


async def demo_unsubscribe(config_path: str):
    """Demonstrate subscribing and unsubscribing."""
    logging.info("Demo: Subscribe/Unsubscribe")
    client = await EventBusClient.from_config(config_path)

    async def temp_handler(msg, headers):
        logging.info(f"Got temperature: {msg}")

    # Subscribe
    logging.info("Subscribing to sensors.temperature...")
    await client.on("sensors.temperature", SensorMessage, temp_handler)

    # Wait a bit
    await asyncio.sleep(5)

    # Unsubscribe
    logging.info("Unsubscribing from sensors.temperature...")
    await client.off("sensors.temperature", temp_handler)

    logging.info("Unsubscribed. No more messages should be received.")
    await asyncio.sleep(3)

    await client.close()


def main():
    config_path = "./config.jsonp"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python multiple_subscriptions_sample.py consumer    - Start consumer")
        print("  python multiple_subscriptions_sample.py producer    - Start producer")
        print("  python multiple_subscriptions_sample.py unsub       - Demo unsubscribe")
        sys.exit(1)

    mode = sys.argv[1]

    if mode == "consumer":
        asyncio.run(consumer(config_path))
    elif mode == "producer":
        asyncio.run(producer(config_path))
    elif mode == "unsub":
        asyncio.run(demo_unsubscribe(config_path))
    else:
        print(f"Unknown mode: {mode}")
        sys.exit(1)


if __name__ == "__main__":
    main()
