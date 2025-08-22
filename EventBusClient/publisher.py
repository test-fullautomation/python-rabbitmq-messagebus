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
# File: publisher.py
#
# Initially created by Nguyen Huynh Tri Cuong (MS/EMC51) / July 2025.
#
# Description:
#
#   AsyncPublisher: Publishes messages to an exchange using aio_pika.
#
# History:
#
# 17.07.2025 / V 1.0.0 / Nguyen Huynh Tri Cuong
# - Initialize
#
# *******************************************************************************
from typing import Optional
import aio_pika
from EventBusClient.serializer.pickle_serializer import PickleSerializer
from EventBusClient.serializer.base_serializer import Serializer
from EventBusClient.message.base_message import BaseMessage


class AsyncPublisher:
   """
AsyncPublisher: Publishes messages to an exchange using aio_pika.
   """
   def __init__(
      self,
      channel: aio_pika.abc.AbstractChannel,
      exchange: aio_pika.abc.AbstractExchange,
      serializer: Optional[Serializer] = None
   ):
      """
AsyncPublisher: Initializes the publisher with a channel, exchange, and optional serializer.

**Arguments:**

* ``channel``

  / *Condition*: required / *Type*: aio_pika.abc.AbstractChannel /

  The channel to publish messages on.

* ``exchange``

  / *Condition*: required / *Type*: aio_pika.abc.AbstractExchange /

  The exchange to publish messages to.

* ``serializer``

  / *Condition*: optional / *Type*: Serializer /

  The serializer used to serialize messages. Defaults to PickleSerializer if not provided.
      """
      self._channel = channel
      self._exchange = exchange
      self._serializer = serializer or PickleSerializer()

   async def publish(
      self,
      message: BaseMessage,
      routing_key: str,
      headers: Optional[dict] = None
   ):
      """
Publish a message to the exchange with the specified routing key.

**Arguments:**

* ``message``

  / *Condition*: required / *Type*: BaseMessage /

  The message to be published. It should be an instance of BaseMessage or its subclasses.

* ``routing_key``

  / *Condition*: required / *Type*: str /

  The routing key used to route the message to the appropriate subscribers.

* ``headers``

  / *Condition*: optional / *Type*: dict /

  Additional headers to include with the message. This can be used for metadata or routing information.

**Note:**
This method serializes the message using the specified serializer and publishes it to the exchange with the given routing key.
The message is sent with a delivery mode of NOT_PERSISTENT, meaning it will not be saved to disk and will not survive a broker restart.
      """
      body: bytes = self._serializer.serialize(message)
      await self._exchange.publish(
         aio_pika.Message(
            body=body,
            headers=headers or {},
            delivery_mode=aio_pika.DeliveryMode.NOT_PERSISTENT
         ),
         routing_key=routing_key
      )
