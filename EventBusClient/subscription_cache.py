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
# File: subscription_cache.py
#
# Initially created by Nguyen Huynh Tri Cuong (MS/EMC51) / August 2025.
#
# Description:
#
#    SubscriptionCache: A thread-safe cache for storing and retrieving items in a FIFO manner.
#
# History:
#
# 12.08.2025 / V 1.0.0 / Nguyen Huynh Tri Cuong
# - Initialize
#
# *******************************************************************************
from __future__ import annotations
import time, asyncio, threading
from collections import deque
from typing import Deque, Generic, Iterable, List, Optional, TypeVar, Callable, Any
from .wait_mode import WaitMode

T = TypeVar("T")

class SubscriptionCache(Generic[T]):
    """
    A thread-safe cache for storing and retrieving items in a FIFO manner.
    """
    def __init__(self, maxlen: int = 200) -> None:
        """
Initialize the SubscriptionCache with an optional maximum length.

**Arguments:**

* ``maxlen``

  / *Condition*: required / *Type*: int /

  Maximum number of items to store in the cache. Older items will be discarded when the limit is reached.
        """
        self._buf: Deque[T] = deque(maxlen=maxlen)
        self._cv = threading.Condition()
        self._maxlen = maxlen

    def register_callback(self, callback: Callable[[T], None]) -> None:
        """
Register a callback function to be called whenever a new item is added to the cache.

**Arguments:**

* ``callback``

  / *Condition*: required / *Type*: Callable[[T], None] /

  A function that takes an item of type T and returns None. This function will be called in a separate thread whenever a new item is added to the cache.
        """
        def thread_func():
            while True:
                item = self.get()
                callback(item)
        thread = threading.Thread(target=thread_func, daemon=True)
        thread.start()


    # ---- producer side (called by your consumer callback)
    def append(self, item: T) -> None:
        """
Add an item to the cache, possibly dropping the oldest item if full.

**Arguments:**

* ``item``

  / *Condition*: required / *Type*: T /

  The item to add to the cache.
        """
        with self._cv:
            self._buf.append(item)  # deque auto-drops oldest when full
            self._cv.notify_all()

    # ---- sync consumers
    def get(self, timeout: Optional[float] = None) -> T:
        """
Block until any item arrives; return it (FIFO) and remove it.

**Arguments:**

* ``timeout``

  / *Condition*: optional / *Type*: Optional[float] / *Default*: None /

  Maximum time to wait for an item in seconds. If None, wait indefinitely.
        """
        end = None if timeout is None else (time.time() + timeout)
        with self._cv:
            while not self._buf:
                remaining = None if end is None else end - time.time()
                if remaining is not None and remaining <= 0:
                    raise TimeoutError("cache.get timed out")
                self._cv.wait(timeout=remaining)
            return self._buf.popleft()

    def pop(self, timeout: Optional[float] = None) -> T:
        """
Alias for get().

**Arguments:**

* ``timeout``

  / *Condition*: optional / *Type*: Optional[float] / *Default*: None /

  Maximum time to wait for an item in seconds. If None, wait indefinitely.

**Returns:**

  / *Type*: T /

  The next item from the cache, removed from the cache.
        """
        return self.get(timeout)

    def pop_nothrow(self) -> Optional[T]:
        """
Remove and return the first item in the cache, only if not empty.

**Returns:**

  / *Type*: Optional[T] /

  The first item from the cache, or None if the cache is empty.
        """
        with self._cv:
            if len(self._buf) > 0:
                return self._buf.popleft()
        return None

    def peek_nothrow(self) -> Optional[T]:
        """
Peek at the first item in the cache, only if not empty.

**Returns:**

  / *Type*: Optional[T] /

  The first item from the cache, or None if the cache is empty.
        """
        with self._cv:
            return self._buf[0] if self._buf else None

    def peek(self, timeout: Optional[float] = None) -> T:
        """
Block until any item arrives; return it (FIFO) but do not remove it.

**Arguments:**

* ``timeout``

  / *Condition*: optional / *Type*: Optional[float] / *Default*: None /

  Maximum time to wait for an item in seconds. If None, wait indefinitely.

**Returns:**

  / *Type*: T /

  The next item from the cache, without removing it.
        """
        end = None if timeout is None else (time.time() + timeout)
        with self._cv:
            while not self._buf:
                remaining = None if end is None else end - time.time()
                if remaining is not None and remaining <= 0:
                    raise TimeoutError("cache.peek timed out")
                self._cv.wait(timeout=remaining)
            return self._buf[0]

    def wait_for(self, predicate: Callable[[T], bool], timeout: Optional[float] = None) -> T:
        """
Block until an item matching the predicate arrives; return it and remove it.

**Arguments:**

* ``predicate``

  / *Condition*: required / *Type*: Callable[[T], bool] /

  A function that takes an item of type T and returns True if it matches the desired condition.

* ``timeout``

  / *Condition*: optional / *Type*: Optional[float] / *Default*: None /

  Maximum time to wait for a matching item in seconds. If None, wait indefinitely.

**Returns:**

  / *Type*: T /

  The first item that matches the predicate, removed from the cache.
        """
        end = None if timeout is None else (time.time() + timeout)
        with self._cv:
            # check existing items first
            for i, x in enumerate(self._buf):
                if predicate(x):
                    # remove ith item
                    self._buf.rotate(-i)
                    res = self._buf.popleft()
                    self._buf.rotate(i)
                    return res
            # wait for future matches
            while True:
                remaining = None if end is None else end - time.time()
                if remaining is not None and remaining <= 0:
                    raise TimeoutError("cache.wait_for timed out")
                self._cv.wait(timeout=remaining)
                for i, x in enumerate(self._buf):
                    if predicate(x):
                        self._buf.rotate(-i)
                        res = self._buf.popleft()
                        self._buf.rotate(i)
                        return res

    def drain(self, max_items: Optional[int] = None) -> List[T]:
        """
Remove and return up to max_items from the cache in FIFO order.

**Arguments:**

* ``max_items``

  / *Condition*: optional / *Type*: Optional[int] / *Default*: None /

  Maximum number of items to remove. If None, remove all items.

**Returns:**

  / *Type*: List[T] /

  A list of removed items, in the order they were in the cache.
        """
        with self._cv:
            out: List[T] = []
            n = len(self._buf) if max_items is None else min(max_items, len(self._buf))
            for _ in range(n):
                out.append(self._buf.popleft())
            return out

    def peek_last(self) -> Optional[T]:
        """
Peek at the last item in the cache, only if not empty.

**Returns:**

  / *Type*: Optional[T] /

  The last item in the cache, or None if the cache is empty.
        """
        with self._cv:
            return self._buf[-1] if self._buf else None

    def __len__(self) -> int:
        """
Return the current number of items in the cache.

**Returns:**

  / *Type*: int /

  The current number of items in the cache.
        """
        with self._cv:
            return len(self._buf)

    def __iter__(self):
        """
Return an iterator over a snapshot of the current items in the cache.

**Returns:**

  / *Type*: Iterator[T] /

  An iterator over the items currently in the cache, in FIFO order.
        """
        with self._cv:
            return iter(list(self._buf))

    # ---- async convenience wrappers (run blocking ops in a thread)
    async def aget(self, timeout: Optional[float] = None) -> T:
        """
Async version of get using a thread executor.

**Arguments:**

* ``timeout``

  / *Condition*: optional / *Type*: Optional[float] / *Default*: None /

  Maximum time to wait for an item in seconds. If None, wait indefinitely.

**Returns:**

  / *Type*: T /

  The next item from the cache, removed from the cache.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.get, timeout)

    async def await_for(self, predicate: Callable[[T], bool], timeout: Optional[float] = None) -> T:
        """
Async version of wait_for using a thread executor.

**Arguments:**

* ``predicate``

  / *Condition*: required / *Type*: Callable[[T], bool] /

  A function that takes an item of type T and returns True if it matches the desired condition.

* ``timeout``

  / *Condition*: optional / *Type*: Optional[float] / *Default*: None /

  Maximum time to wait for a matching item in seconds. If None, wait indefinitely.

**Returns:**

  / *Type*: T /

  The first item that matches the predicate, removed from the cache.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.wait_for, predicate, timeout)

    def wait_for_one(self, target: Any, *, timeout: float = 30.0) -> bool:
        """
Wait for a single target message to appear in the cache.

**Arguments:**

* ``target``

  / *Condition*: required / *Type*: Any /

  The target message to wait for.

* ``timeout``

  / *Condition*: optional / *Type*: float / *Default*: 30.0 /

  Maximum time to wait in seconds.

**Returns:**

  / *Type*: bool /

  True if the target message was found and removed from the cache, False if the timeout was reached.
        """
        end = time.time() + timeout
        with self._cv:
            while True:
                idx = next((i for i, m in enumerate(self._buf) if m == target), -1)
                if idx >= 0:
                    for _ in range(idx):
                        self._buf.popleft()
                    self._buf.popleft()
                    return True
                remaining = end - time.time()
                if remaining <= 0:
                    return False
                self._cv.wait(remaining)

    def wait_for_many(self, targets: List[Any], *, mode: WaitMode, timeout: float = 30.0) -> List[int]:
        """
Wait for multiple target messages to appear in the cache.

**Arguments:**

* ``targets``

    / *Condition*: required / *Type*: List[Any] /

    List of target messages to wait for.

* ``mode``

    / *Condition*: required / *Type*: WaitMode /

    Mode of waiting:

    - WaitMode.ALL_IN_GIVEN_ORDER: Wait for all target messages in the given order.

    - WaitMode.ALL_IN_RANDOM_ORDER: Wait for all target messages in any order.

    - WaitMode.ANY_OF_GIVEN_MSGS: Wait for any one of the target messages.

* ``timeout``

    / *Condition*: optional / *Type*: float / *Default*: 30.0 /

    Maximum time to wait in seconds.

**Returns:**

  / *Type*: List[int] /

  List of indices of the target messages that were found, in the order they were found.
        """
        end = time.time() + timeout
        seen: List[int] = []
        next_idx = 0
        checked = [False] * len(targets)

        with self._cv:
            while True:
                while self._buf:
                    msg = self._buf.popleft()
                    if mode is WaitMode.ALL_IN_GIVEN_ORDER:
                        if next_idx < len(targets) and msg == targets[next_idx]:
                            seen.append(next_idx)
                            next_idx += 1
                            if next_idx >= len(targets):
                                return seen
                    elif mode is WaitMode.ALL_IN_RANDOM_ORDER:
                        k = next((i for i, m in enumerate(targets) if (not checked[i]) and m == msg), -1)
                        if k >= 0:
                            checked[k] = True
                            seen.append(k)
                            if all(checked):
                                return seen
                    else:  # ANY_OF_GIVEN_MSGS
                        k = next((i for i, m in enumerate(targets) if m == msg), -1)
                        if k >= 0:
                            return [k]
                remaining = end - time.time()
                if remaining <= 0:
                    # For ORDER mode, timeout means not all seen → empty result to match old API
                    return [] if mode is WaitMode.ALL_IN_GIVEN_ORDER and len(seen) < len(targets) else seen
                self._cv.wait(remaining)
