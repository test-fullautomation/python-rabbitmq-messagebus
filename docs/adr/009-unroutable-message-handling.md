# ADR-009: Configurable Unroutable Message Handling

## Status

Accepted

## Date

2025-08-05

## Author

Nguyen Huynh Tri Cuong (MS/EMC51)

## Reviewer

- Nguyen Huynh Tri Cuong (MS/EMC51)

## History

| Date | Version | Description |
|------|---------|-------------|
| 2025-08-05 | 1.0 | Initial version |
| 2025-08-20 | 1.1 | Added alternate-exchange policy |

## Context

In IPC systems, unroutable messages are common failure modes:
- Consumer not started yet
- Wrong routing key used
- Missing queue binding
- Environment drift across deployments

Different environments want different reactions:
- **CI/Testing**: Fail-fast to catch routing errors early
- **Development**: Log evidence without crashing
- **Production-like**: Durable capture for analysis

Without configuration, these scenarios lead to silent message loss:
```python
await client.send("typo.in.routing.key", message)
# Message silently dropped - no error, no trace!
```

## Decision

Provide a configurable mechanism with two dimensions:

### 1. Policy (How RabbitMQ Handles Unroutables)

| Policy | Description | RabbitMQ Behavior |
|--------|-------------|-------------------|
| `drop` | Default, silently discard | Normal publish |
| `return` | Return to sender | `mandatory=True`, handle `basic.return` |
| `alternate-exchange` | Route to fallback exchange | Declare AE on main exchange |

### 2. Action (What Library Does When Detected)

| Action | Description |
|--------|-------------|
| `log` | Log warning message |
| `cache` | Store in unroutable cache for later retrieval |
| `callback` | Invoke user-provided callback function |
| `raise` | Raise `UnroutableMessageError` exception |

### Configuration

Via StartupPolicy:
```python
policy = ConfigureUnroutablePolicy(
    mode="return",           # RabbitMQ policy
    on_unroutable="cache",   # Library action
    alternate_exchange=None
)
```

Via ExchangeHandler:
```python
handler.configure_unroutable(
    policy="alternate-exchange",
    alternate_exchange="unroutable_exchange",
    on_unroutable="log"
)
```

### Retrieving Cached Unroutables

```python
# After some operations...
unroutable_messages = client.pop_unroutables()
for info in unroutable_messages:
    print(f"Unroutable: {info.routing_key} - {info.message}")
```

### Alternate Exchange Setup

When `policy="alternate-exchange"`:
1. Declare alternate exchange (fanout type)
2. Declare durable queue bound to AE
3. Set `alternate-exchange` argument on main exchange
4. Unroutable messages automatically routed to AE queue

## Consequences

### Positive

- Prevents silent message loss
- Environment-appropriate handling
- Multiple reaction options
- Testable routing configurations

### Negative

- Configuration complexity
- Alternate exchange creates additional resources
- Return policy adds latency for basic.return handling

### Neutral

- Documentation must guide teams on mode selection
- Tests should cover each policy/action combination

## Alternatives Considered

### 1. Always Drop Unroutables (Rejected)

Simplest approach, matches default RabbitMQ behavior.

Rejected because:
- Hides routing mistakes
- Hard to troubleshoot missing messages
- Silent failures in production

### 2. Always Raise on Unroutables (Rejected)

Fail immediately on any unroutable message.

Rejected because:
- Too strict for some runtime contexts
- May crash during normal transient conditions
- Not appropriate for all environments

### 3. Always Use Alternate Exchange (Rejected)

Always configure alternate exchange for capture.

Rejected because:
- Creates queues/exchanges even when not needed
- Requires governance for AE cleanup
- Overkill for development/testing

## References

- [RabbitMQ Alternate Exchanges](https://www.rabbitmq.com/ae.html)
- [AMQP Mandatory Flag](https://www.rabbitmq.com/publishers.html#unroutable)
- Source: `EventBusClient/exchange_handler/base.py`
- Source: `EventBusClient/startup_policy.py` (ConfigureUnroutablePolicy)
- Diagram: `docs/diagrams/sequence-unroutable.puml`
