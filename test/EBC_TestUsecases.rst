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

* **Test EBC_0011**

  [XRTopicExchangeHandler / GOODCASE]

   **Send message with single wildcard (*) in routing key to multiple subscribers**

   Expected: Message successfully sent and received by all subscribers using wildcard pattern

----

* **Test EBC_0012**

  [XRTopicExchangeHandler / GOODCASE]

   **Send message with multi-level wildcard (#) in routing key to multiple subscribers**

   Expected: Message successfully sent and received by all subscribers using multi-level wildcard pattern

----

* **Test EBC_0013**

  [XRTopicExchangeHandler / GOODCASE]

   **Test mixed wildcard patterns in single routing key**

   Expected: Message successfully sent and received by all subscribers using mixed wildcard patterns (* and #) in single routing key

----

* **Test EBC_0014**

  [XRTopicExchangeHandler / GOODCASE]

   **Test message order preservation in x-rtopic exchange**

   Expected: Messages arrive in the same order they are sent using x-rtopic exchange

----

* **Test EBC_0015**

  [XRTopicExchangeHandler / GOODCASE]

   **Test multiple publishers with different routing patterns**

   Expected: Multiple publishers using different routing patterns can send to appropriate subscribers using x-rtopic exchange

----

* **Test EBC_0016**

  [XRTopicExchangeHandler / GOODCASE]

   **Test case sensitivity in x-rtopic routing patterns**

   Expected: Case sensitivity should be respected in x-rtopic pattern matching

----

* **Test EBC_0017**

  [XRTopicExchangeHandler / BADCASE]

   **Test routing pattern with null or None values**

   Expected: Exception should be raised when using null/None values in routing patterns

----

* **Test EBC_0018**

  [XRTopicExchangeHandler / BADCASE]

   **Send message with routing key exceeding maximum length**

   Expected: Exception should be raised when using routing key exceeding maximum length

----

* **Test EBC_0019**

  [XRTopicExchangeHandler / BADCASE]

   **Test serialization failure with x-rtopic patterns**

   Expected: Exception should be raised when message serialization fails with x-rtopic patterns

----

* **Test EBC_0020**

  [XRTopicExchangeHandler / EDGECASES]

   **Test x-rtopic with minimal routing patterns**

   Expected: Minimal routing patterns should work correctly with x-rtopic exchange

----

* **Test EBC_0021**

  [XRTopicExchangeHandler / EDGECASES]

   **Test x-rtopic with deep hierarchical routing patterns**

   Expected: Deep hierarchical routing patterns should work correctly with x-rtopic exchange

----

* **Test EBC_0022**

  [XRTopicExchangeHandler / EDGECASES]

   **Test x-rtopic with overlapping routing patterns**

   Expected: Overlapping routing patterns should work correctly with x-rtopic exchange

----

* **Test EBC_0023**

  [XRTopicExchangeHandler / EDGECASES]

   **Test x-rtopic with empty segments in routing patterns**

   Expected: Empty segments in routing patterns should be handled correctly with x-rtopic exchange

----

* **Test EBC_0024**

  [BasicMessage / GOODCASE]

   **Test BasicMessage with topic exchange**

   Expected: BasicMessage successfully sent and received with correct content using topic exchange

----

* **Test EBC_0025**

  [BasicMessage / GOODCASE]

   **Test BasicMessage with x-rtopic reverse routing logic**

   Expected: Message delivered using reverse topic logic where subscriber uses literal key and publisher uses pattern

----

* **Test EBC_0026**

  [BasicMessage / GOODCASE]

   **Test BasicMessage equality comparison between two instances**

   Expected: BasicMessage equality comparison should correctly identify equal and non-equal instances

----

* **Test EBC_0027**

  [BasicMessage / GOODCASE]

   **Test BasicMessage creation from dictionary representation**

   Expected: BasicMessage should be correctly created from dictionary representation and maintain data integrity

----

* **Test EBC_0028**

  [BasicMessage / GOODCASE]

   **Test BasicMessage inequality with different content or headers**

   Expected: BasicMessage inequality comparison should correctly identify non-equal instances with different content or headers

----

* **Test EBC_0029**

  [BasicMessage / GOODCASE]

   **Test BasicMessage with empty content and no headers**

   Expected: Message created successfully with auto-generated UUID header

----

* **Test EBC_0030**

  [BasicMessage / EDGECASES]

   **Test BasicMessage string representations using str() and repr() methods**

   Expected: BasicMessage should provide correct string representations through str() and repr() methods

----

* **Test EBC_0031**

  [ControlMessage / GOODCASE]

   **Test ControlMessage creation from data dictionary**

   Expected: ControlMessage created with all fields correctly set from data dictionary

----

* **Test EBC_0032**

  [ControlMessage / BADCASE]

   **Test ControlMessage with invalid roles data type**

   Expected: Exception should be raised when ControlMessage is created with invalid roles data type (non-list)

----

* **Test EBC_0033**

  [ControlMessage / BADCASE]

   **Test ControlMessage with invalid kind data type**

   Expected: Exception should be raised when ControlMessage is created with invalid kind data type (non-string)

----

* **Test EBC_0034**

  [ControlMessage / BADCASE]

   **Test ControlMessage with invalid instance_id data type**

   Expected: Exception should be raised when ControlMessage is created with invalid instance_id data type (non-string)

----

* **Test EBC_0035**

  [ControlMessage / BADCASE]

   **Test ControlMessage with invalid ts (timestamp)**

   Expected: Exception should be raised when ControlMessage is created with invalid ts data type (non-numeric)

----

* **Test EBC_0036**

  [ControlMessage / EDGECASES]

   **EDGECASE: Test ControlMessage with unusual timestamp values**

   Expected: ControlMessage should correctly handle edge case timestamp values including zero, negative, very large, and precise float values

----

* **Test EBC_0037**

  [ConfigureUnroutablePolicy / GOODCASE]

   **ConfigureUnroutablePolicy: mode=return, on_unroutable=raise**

   Expected: An unroutable message should raise (reported by the test as a PASS string)

----

* **Test EBC_0038**

  [ConfigureUnroutablePolicy / GOODCASE]

   **ConfigureUnroutablePolicy: mode=return, on_unroutable=callback**

   Expected: An unroutable message should trigger the provided callback and not raise

----

* **Test EBC_0039**

  [ConfigureUnroutablePolicy / GOODCASE]

   **ConfigureUnroutablePolicy: mode=return, on_unroutable=cache**

   Expected: An unroutable message should be cached (store for later) and not raise

----

* **Test EBC_0040**

  [ConfigureUnroutablePolicy / GOODCASE]

   **ConfigureUnroutablePolicy: mode=return, on_unroutable=log**

   Expected: An unroutable message should not raise (should be logged)

----

* **Test EBC_0041**

  [ConfigureUnroutablePolicy / GOODCASE]

   **ConfigureUnroutablePolicy: mode=alternate-exchange**

   Expected: An unroutable message should be routed to the configured alternate exchange

----

* **Test EBC_0042**

  [HeadersExchangeHandler / GOODCASE]

   **Headers exchange with match_all=True (AND logic)**

   Expected: Message successfully sent and received when ALL headers match

----

* **Test EBC_0043**

  [HeadersExchangeHandler / GOODCASE]

   **Headers exchange with match_all=False (OR logic)**

   Expected: Message successfully sent and received when ANY header matches

----

* **Test EBC_0044**

  [HeadersExchangeHandler / GOODCASE]

   **Headers exchange with multiple subscribers using different binding criteria**

   Expected: Multiple subscribers receive messages based on their individual header bindings

----

* **Test EBC_0045**

  [HeadersExchangeHandler / GOODCASE]

   **Headers exchange message ordering**

   Expected: Messages are received in the same order they were sent

----

* **Test EBC_0046**

  [HeadersExchangeHandler / GOODCASE]

   **Headers exchange with non-matching headers**

   Expected: Message with non-matching headers should not be delivered to subscriber

----

* **Test EBC_0047**

  [HeadersExchangeHandler / GOODCASE]

   **Headers exchange partial match with AND logic should not deliver**

   Expected: Message with partial header match should not be delivered when using AND logic

----

Generated: 29.01.2026 - 15:13:45

