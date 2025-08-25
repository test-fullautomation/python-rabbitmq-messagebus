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
from typing import Deque, Generic, Iterable, List, Optional, TypeVar, Callable

T = TypeVar("T")

class SubscriptionCache(Generic[T]):
    def __init__(self, maxlen: int = 200) -> None:
        self._buf: Deque[T] = deque(maxlen=maxlen)
        self._cv = threading.Condition()
        self._maxlen = maxlen

    # ---- producer side (called by your consumer callback)
    def append(self, item: T) -> None:
        with self._cv:
            self._buf.append(item)  # deque auto-drops oldest when full
            self._cv.notify_all()

    # ---- sync consumers
    def get(self, timeout: Optional[float] = None) -> T:
        """Block until any item arrives; return it (FIFO)."""
        end = None if timeout is None else (time.time() + timeout)
        with self._cv:
            while not self._buf:
                remaining = None if end is None else end - time.time()
                if remaining is not None and remaining <= 0:
                    raise TimeoutError("cache.get timed out")
                self._cv.wait(timeout=remaining)
            return self._buf.popleft()

    def wait_for(self, predicate: Callable[[T], bool], timeout: Optional[float] = None) -> T:
        """Block until an item matches predicate, return it (and remove it)."""
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
        """Remove and return up to max_items (all if None)."""
        with self._cv:
            out: List[T] = []
            n = len(self._buf) if max_items is None else min(max_items, len(self._buf))
            for _ in range(n):
                out.append(self._buf.popleft())
            return out

    def peek_last(self) -> Optional[T]:
        with self._cv:
            return self._buf[-1] if self._buf else None

    def __len__(self) -> int:
        with self._cv:
            return len(self._buf)

    # ---- async convenience wrappers (run blocking ops in a thread)
    async def aget(self, timeout: Optional[float] = None) -> T:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.get, timeout)

    async def await_for(self, predicate: Callable[[T], bool], timeout: Optional[float] = None) -> T:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.wait_for, predicate, timeout)
