# ADR-008: SubscriptionCache for Synchronous Message Access

## Status

Accepted

## Date

2025-08-01

## Author

Nguyen Huynh Tri Cuong (MS/EMC51)

## Reviewer

- Nguyen Huynh Tri Cuong (MS/EMC51)

## History

| Date | Version | Description |
|------|---------|-------------|
| 2025-08-01 | 1.0 | Initial version |
| 2025-08-10 | 1.1 | Added WaitMode enum for wait_for_many |

## Context

EventBusClient uses async callbacks for message delivery, but synchronous callers need a way to:
- Block until a message arrives
- Access received messages without async/await
- Wait for specific messages or patterns
- Handle multiple expected messages

```python
# Async callback style - natural for async code
async def on_message(msg, headers):
    process(msg)

await client.on("topic", MessageCls, on_message)

# But sync callers need something like:
message = wait_for_message("topic", timeout=5.0)  # Blocking call
```

## Decision

Provide a thread-safe **SubscriptionCache** that bridges async message delivery to synchronous access:

### Core Design

```python
class SubscriptionCache(Generic[T]):
    def __init__(self, maxlen: int = 100):
        self._buf: Deque[T] = deque(maxlen=maxlen)
        self._cv: Condition = Condition()  # For blocking waits

    def append(self, item: T) -> None:
        """Called by subscriber when message arrives."""
        with self._cv:
            self._buf.append(item)
            self._cv.notify_all()

    def get(self, timeout: float = None) -> T:
        """Block until message available, return oldest."""

    def pop(self, timeout: float = None) -> T:
        """Block until message available, remove and return oldest."""

    def peek(self, timeout: float = None) -> T:
        """Block until message available, return without removing."""

    def wait_for(self, predicate: Callable[[T], bool], timeout: float) -> T:
        """Block until message matching predicate arrives."""

    def wait_for_one(self, target: T, timeout: float) -> bool:
        """Block until specific message arrives."""

    def wait_for_many(self, targets: list, mode: WaitMode, timeout: float) -> list[int]:
        """Wait for multiple messages with different matching modes."""

    def drain(self, max_items: int = None) -> list[T]:
        """Remove and return all available messages."""
```

### WaitMode Enum

```python
class WaitMode(Enum):
    ALL_IN_GIVEN_ORDER = 1    # Must receive in exact order
    ALL_IN_RANDOM_ORDER = 2   # Must receive all, any order
    ANY_OF_GIVEN_MSGS = 3     # Return when any one matches
```

### Integration with Subscriber

```python
# Subscribe returns the cache
cache = await client.on("topic", MessageCls, callback)

# Sync caller can use cache
msg = cache.get(timeout=5.0)

# Or wait for specific patterns
indices = cache.wait_for_many(
    [expected1, expected2],
    mode=WaitMode.ALL_IN_RANDOM_ORDER,
    timeout=10.0
)
```

### Bounded Buffer

Cache uses `deque(maxlen=N)` to prevent unbounded memory growth:
- Old messages dropped when buffer full
- Not a persistence mechanism
- Default size configurable per subscription

## Consequences

### Positive

- Bridges async delivery to sync consumption
- Thread-safe for multi-threaded callers
- Flexible waiting patterns via WaitMode
- Bounded memory usage

### Negative

- Cache is not durable - messages lost if not consumed
- Buffer overflow drops old messages silently
- Adds complexity for simple async-only usage

### Neutral

- Documentation must clarify cache is not end-to-end durability
- Size should be tuned based on message rate

## Alternatives Considered

### 1. Queue.Queue Instead of Deque (Rejected)

Use Python's Queue.Queue for thread-safe buffering.

Rejected because:
- Queue is unbounded by default (memory risk)
- deque(maxlen=N) provides natural bounded buffer
- Condition variable gives more control over waiting

### 2. No Sync Support (Rejected)

Only provide async API, require callers to manage their own buffering.

Rejected because:
- High friction for sync callers
- Duplicated buffering logic across projects
- Inconsistent patterns

### 3. Persistent Cache (Deferred)

Store messages to disk or database for durability.

Deferred because:
- Adds significant complexity
- RabbitMQ already provides persistence if needed
- Current use cases don't require it

## References

- [Python threading.Condition](https://docs.python.org/3/library/threading.html#condition-objects)
- [collections.deque](https://docs.python.org/3/library/collections.html#collections.deque)
- Source: `EventBusClient/subscription_cache.py`
- Source: `EventBusClient/wait_mode.py`
