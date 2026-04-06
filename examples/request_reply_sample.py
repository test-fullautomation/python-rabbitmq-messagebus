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
# File: request_reply_sample.py
#
# Initially created by Claude Code / January 2026.
#
# Description:
#
#   Demonstrates a request-reply pattern over the message bus.
#   A client sends requests and waits for responses using correlation IDs.
#
# Usage:
#   Terminal 1: python request_reply_sample.py server
#   Terminal 2: python request_reply_sample.py client
#
# *******************************************************************************
import asyncio
import logging
import sys
import os
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from EventBusClient.event_bus_client import EventBusClient
from EventBusClient.message.base_message import BaseMessage


class RequestMessage(BaseMessage):
    """A request message with correlation ID for tracking."""
    def __init__(self, correlation_id: str = None, method: str = None, params: dict = None, reply_to: str = None):
        super().__init__()
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.method = method
        self.params = params or {}
        self.reply_to = reply_to

    @classmethod
    def from_data(cls, data):
        return cls(
            correlation_id=data.get("correlation_id"),
            method=data.get("method"),
            params=data.get("params", {}),
            reply_to=data.get("reply_to")
        )

    def get_value(self):
        return self

    def __repr__(self):
        return f"Request({self.correlation_id[:8]}..., method={self.method!r})"


class ResponseMessage(BaseMessage):
    """A response message with correlation ID for matching to requests."""
    def __init__(self, correlation_id: str = None, success: bool = True, result=None, error: str = None):
        super().__init__()
        self.correlation_id = correlation_id
        self.success = success
        self.result = result
        self.error = error

    @classmethod
    def from_data(cls, data):
        return cls(
            correlation_id=data.get("correlation_id"),
            success=data.get("success", True),
            result=data.get("result"),
            error=data.get("error")
        )

    def get_value(self):
        return self

    def __eq__(self, other):
        if isinstance(other, ResponseMessage):
            return self.correlation_id == other.correlation_id
        return False

    def __repr__(self):
        status = "OK" if self.success else f"ERROR: {self.error}"
        return f"Response({self.correlation_id[:8]}..., {status})"


class RpcServer:
    """Simple RPC server that handles requests."""

    def __init__(self, client: EventBusClient):
        self.client = client
        self.methods = {
            "add": self._add,
            "multiply": self._multiply,
            "echo": self._echo,
            "slow_operation": self._slow_operation,
        }

    async def _add(self, a: int, b: int) -> int:
        return a + b

    async def _multiply(self, a: int, b: int) -> int:
        return a * b

    async def _echo(self, message: str) -> str:
        return f"Echo: {message}"

    async def _slow_operation(self, duration: float) -> str:
        await asyncio.sleep(duration)
        return f"Completed after {duration}s"

    async def handle_request(self, request: RequestMessage, headers: dict):
        """Process a request and send response."""
        logging.info(f"Server: Handling {request}")

        try:
            method = self.methods.get(request.method)
            if not method:
                response = ResponseMessage(
                    correlation_id=request.correlation_id,
                    success=False,
                    error=f"Unknown method: {request.method}"
                )
            else:
                result = await method(**request.params)
                response = ResponseMessage(
                    correlation_id=request.correlation_id,
                    success=True,
                    result=result
                )
        except Exception as e:
            response = ResponseMessage(
                correlation_id=request.correlation_id,
                success=False,
                error=str(e)
            )

        # Send response to reply_to topic
        if request.reply_to:
            await self.client.send(request.reply_to, response)
            logging.info(f"Server: Sent {response}")


class RpcClient:
    """RPC client that sends requests and waits for responses."""

    def __init__(self, client: EventBusClient, reply_topic: str):
        self.client = client
        self.reply_topic = reply_topic
        self.response_cache = None
        self.pending_requests = {}

    async def setup(self):
        """Subscribe to reply topic."""
        self.response_cache = await self.client.on(
            self.reply_topic, ResponseMessage, cache_size=100
        )

    async def call(self, method: str, timeout: float = 10.0, **params):
        """
        Make an RPC call and wait for response.

        Args:
            method: The method name to call
            timeout: Timeout in seconds
            **params: Method parameters

        Returns:
            The result from the server

        Raises:
            TimeoutError: If no response within timeout
            RuntimeError: If server returns an error
        """
        request = RequestMessage(
            method=method,
            params=params,
            reply_to=self.reply_topic
        )

        logging.info(f"Client: Sending {request}")
        await self.client.send("rpc.requests", request)

        # Wait for response with matching correlation_id
        expected = ResponseMessage(correlation_id=request.correlation_id)
        try:
            found = self.response_cache.wait_for_one(expected, timeout=timeout)
            if not found:
                raise TimeoutError(f"No response for {request.correlation_id}")

            # Get the actual response from cache
            response = self.response_cache.peek_last()
            logging.info(f"Client: Received {response}")

            if not response.success:
                raise RuntimeError(response.error)

            return response.result
        except TimeoutError:
            raise TimeoutError(f"RPC call {method} timed out after {timeout}s")


async def server(config_path: str):
    """Run the RPC server."""
    logging.info("Server: Starting")
    client = await EventBusClient.from_config(config_path)

    rpc_server = RpcServer(client)

    # Subscribe to request topic
    await client.on("rpc.requests", RequestMessage, rpc_server.handle_request)
    logging.info("Server: Listening for requests on 'rpc.requests'")

    # Keep server running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logging.info("Server: Shutting down")
    finally:
        await client.close()


async def client_demo(config_path: str):
    """Run the RPC client demo."""
    logging.info("Client: Starting")
    client = await EventBusClient.from_config(config_path)

    # Create RPC client with unique reply topic
    client_id = str(uuid.uuid4())[:8]
    reply_topic = f"rpc.replies.{client_id}"
    rpc = RpcClient(client, reply_topic)
    await rpc.setup()

    logging.info(f"Client: Reply topic is '{reply_topic}'")

    # Make some RPC calls
    try:
        # Test add
        result = await rpc.call("add", a=5, b=3)
        logging.info(f"Client: add(5, 3) = {result}")

        # Test multiply
        result = await rpc.call("multiply", a=4, b=7)
        logging.info(f"Client: multiply(4, 7) = {result}")

        # Test echo
        result = await rpc.call("echo", message="Hello, RPC!")
        logging.info(f"Client: echo result = {result}")

        # Test slow operation
        logging.info("Client: Calling slow_operation (2 seconds)...")
        result = await rpc.call("slow_operation", duration=2.0, timeout=5.0)
        logging.info(f"Client: slow_operation result = {result}")

        # Test unknown method
        logging.info("Client: Calling unknown method...")
        try:
            result = await rpc.call("unknown_method")
        except RuntimeError as e:
            logging.info(f"Client: Expected error - {e}")

    except Exception as e:
        logging.error(f"Client: Error - {e}")
    finally:
        await client.close()


def main():
    config_path = "./config.jsonp"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python request_reply_sample.py server    - Start RPC server")
        print("  python request_reply_sample.py client    - Run client demo")
        print()
        print("Run server first in one terminal, then client in another.")
        sys.exit(1)

    role = sys.argv[1]

    if role == "server":
        asyncio.run(server(config_path))
    elif role == "client":
        asyncio.run(client_demo(config_path))
    else:
        print(f"Unknown role: {role}")
        sys.exit(1)


if __name__ == "__main__":
    main()
