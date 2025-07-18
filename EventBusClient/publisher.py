#  Copyright 2020-2023 Robert Bosch GmbH
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
from serializer.pickle_serializer import PickleSerializer
from serializer.base_serializer import Serializer
from message.base_message import BaseMessage


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
      body: bytes = self._serializer.serialize(message)
      await self._exchange.publish(
         aio_pika.Message(
            body=body,
            headers=headers or {},
            delivery_mode=aio_pika.DeliveryMode.NOT_PERSISTENT
         ),
         routing_key=routing_key
      )
