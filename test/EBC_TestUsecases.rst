.. Copyright 2020-2025 Robert Bosch GmbH

.. Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

.. http://www.apache.org/licenses/LICENSE-2.0

.. Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

Test Use Cases
==============

* **Test EBC_0001**

  [TopicExchangeHandler / GOODCASE]

   **Send message from one publisher to one specific subscriber and confirm receipt**

   Expected: Message successfully sent and received with correct content

----

* **Test EBC_0002**

  [TopicExchangeHandler / GOODCASE]

   **Ensure messages arrive in same order they are sent**

   Expected: Messages received in the same order they were sent

----

* **Test EBC_0003**

  [TopicExchangeHandler / GOODCASE]

   **Test one publisher delivering messages to multiple subscribers using the same routing key**

   Expected: All subscribers receive the same message with correct content

----

* **Test EBC_0004**

  [TopicExchangeHandler / GOODCASE]

   **Validate multiple publishers can send to a single subscriber without conflict**

   Expected: Subscriber receives all messages from all publishers correctly

----

* **Test EBC_0005**

  [TopicExchangeHandler / GOODCASE]

   **Send message with wildcard routing key patterns (* and #)**

   Expected: Messages delivered correctly to subscribers using wildcard routing patterns

----

* **Test EBC_0006**

  [TopicExchangeHandler / GOODCASE]

   **Verify routing key case sensitivity**

   Expected: Messages with different case routing keys should be treated as separate routes

----

* **Test EBC_0007**

  [TopicExchangeHandler / BADCASE]

   **Send message with malformed routing key pattern**

   Expected: Exception should be raised when using invalid routing key format

----

* **Test EBC_0008**

  [TopicExchangeHandler / BADCASE]

   **Use invalid wildcard in routing key**

   Expected: Exception should be raised when using invalid wildcard in routing keys

----

* **Test EBC_0009**

  [TopicExchangeHandler / BADCASE]

   **Send message with routing key exceeding maximum length**

   Expected: Exception should be raised when using routing key exceeding maximum length

----

* **Test EBC_0010**

  [TopicExchangeHandler / BADCASE]

   **Topic pattern matching fails due to encoding/serialization issues**

   Expected: Exception should be raised when message serialization fails due to encoding issues

----

Generated: 11.08.2025 - 15:37:41

