# ADR-004: Configuration-Driven Library Setup

## Status

Accepted

## Date

2025-08-10

## Author

Nguyen Huynh Tri Cuong (MS/EMC51)

## Reviewer

- Nguyen Huynh Tri Cuong (MS/EMC51)

## History

| Date | Version | Description |
|------|---------|-------------|
| 2025-08-10 | 1.0 | Initial version |

## Context

EventBusClient has multiple configurable aspects:
- Connection parameters (host, port, prefetch count)
- Plugin selection (serializer, exchange handler)
- Exchange configuration (name, type)
- Logging settings (file, level, mode)
- Startup behavior (general cache, policies)

Hardcoding these values requires code changes for each environment:

```python
# Hardcoded - requires code change per environment
client = EventBusClient(
    exchange_handler=TopicExchangeHandler("my_exchange", JsonSerializer()),
    ...
)
await client.connect("localhost", 5672, prefetch_count=10)
```

Different deployment environments need different configurations:
- **Development**: localhost, debug logging, pickle serializer
- **CI/Testing**: test broker, warn logging, json serializer
- **Production**: production broker, error logging, protobuf serializer

## Decision

Provide **configuration-driven setup** via external configuration files using JsonPreprocessor (JSONP format):

### Configuration Template

A documented template is provided at `EventBusClient/config/config.jsonp.template`:

```jsonp
{
  // plugins_path: Path to the directory containing plugin modules.
  "plugins_path": "./plugins",

  // host: Hostname or IP address for the server connection.
  "host": "localhost",

  // port: Port number for the server connection.
  "port": 5672,

  // serializer: Serialization method for message data.
  "serializer": "PickleSerializer",

  // exchange_handler: Handler type for message exchange.
  "exchange_handler": "TopicExchangeHandler",

  // auto_reconnect: Automatically reconnect if the connection is lost.
  "auto_reconnect": true,

  // qos_prefetch: Number of messages to prefetch for Quality of Service.
  "qos_prefetch": 10,

  // general_cache_policy: Cache policy ("off" | "on_connect" | "on_demand").
  "general_cache_policy": "off",

  // general_routing_keys: Routing keys for general messages.
  "general_routing_keys": "general",

  // general_message_cls: Message class for general messages.
  "general_message_cls": "BaseMessage",

  // logger_name: Name of the logger instance.
  "logger_name": "event_bus_client",

  // logfile: Path to the log file.
  "logfile": "eventbus.log",

  // loglevel: Logging level (DEBUG|INFO|WARNING|ERROR|CRITICAL).
  "loglevel": "INFO",

  // logger_mode: Log file write mode ("w" for overwrite, "a" for append).
  "logger_mode": "a"
}
```

### Configuration Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `host` | str | No | "localhost" | RabbitMQ server hostname or IP |
| `port` | int | No | 5672 | RabbitMQ server port (1024-65535) |
| `serializer` | str | **Yes** | - | Serializer class name (e.g., "PickleSerializer", "JsonSerializer") |
| `exchange_handler` | str | **Yes** | - | Exchange handler class name (e.g., "TopicExchangeHandler") |
| `exchange_name` | str | No | - | Custom exchange name |
| `auto_reconnect` | bool | No | true | Enable automatic reconnection |
| `qos_prefetch` | int | No | 10 | Prefetch count for QoS (must be >= 0) |
| `plugins_path` | str | No | "./plugins" | Path to custom plugins directory |
| `general_cache_policy` | str | No | "off" | General cache: "off", "on_connect", "on_demand" |
| `general_routing_keys` | str | No | "general" | Routing keys for general cache |
| `general_message_cls` | str | No | "BaseMessage" | Message class for general cache |
| `logger_name` | str | No | "event_bus_client" | Logger instance name |
| `logfile` | str | No | None | Log file path ("console" for stdout) |
| `loglevel` | str | No | "INFO" | Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `logger_mode` | str | No | "a" | Log file mode: "w" (overwrite) or "a" (append) |

### Usage

1. Copy template to your project:
   ```bash
   cp EventBusClient/config/config.jsonp.template ./config.jsonp
   ```

2. Adjust values for your environment

3. Load configuration in code:
   ```python
   client = await EventBusClient.from_config("./config.jsonp")
   ```

### Factory Methods

```python
# Async factory
client = await EventBusClient.from_config("config.jsonp")

# Sync factory
client = EventBusClient.from_config_sync("config.jsonp")
```

### ConfigValidator

Validates configuration against schema before use:

```python
CONFIG_SCHEMA = {
    "plugins_path": str,
    "host": str,
    "port": int,                    # Must be 1024-65535
    "serializer": str,              # Must match registered serializer
    "exchange_handler": str,        # Must match registered handler
    "exchange_name": str,
    "auto_reconnect": bool,
    "qos_prefetch": int,            # Must be >= 0
    "logfile": str,
    "loglevel": str,                # DEBUG|INFO|WARNING|ERROR|CRITICAL
    "logger_name": str,
    "logger_mode": str,             # "w" (overwrite) or "a" (append)
    "general_cache_policy": str,    # off|on_connect|on_demand
    "general_routing_keys": str,
    "general_message_cls": str
}
```

### JsonPreprocessor Features

Using JSONP format enables:
- **Variable substitution**: `${ENV_VAR}` syntax
- **File includes**: Split configuration across files
- **Comments**: Document configuration inline
- **Expressions**: Computed values

```jsonp
// config.jsonp - with JSONP features
{
    "host": "${RABBITMQ_HOST}",           // From environment
    "port": ${RABBITMQ_PORT:-5672},       // With default
    "loglevel": "${LOG_LEVEL:-INFO}",
    // Include environment-specific overrides
    ${include: "./env/${ENVIRONMENT}.jsonp"}
}
```

### Configuration Resolution Flow

```
config.jsonp
    ↓
JsonPreprocessor.jsonLoad()
    ↓
ConfigValidator.validate()
    ↓
PluginLoader.get_serializer(config.serializer)
PluginLoader.get_exchange_handler(config.exchange_handler)
    ↓
EventBusClient instance
```

## Consequences

### Positive

- Environment-specific configuration without code changes
- Validated configuration prevents runtime errors
- JSONP features enable flexible configuration management
- Separation of configuration from code
- Easy to version control configuration files

### Negative

- Additional dependency on JsonPreprocessor
- Configuration errors may be harder to debug than code errors
- Schema must be maintained alongside code changes

### Neutral

- Teams must manage configuration files per environment
- Documentation needed for all configuration options

## Alternatives Considered

### 1. Environment Variables Only (Rejected)

Use only environment variables for configuration.

Rejected because:
- Limited structure for complex configuration
- No validation
- Harder to manage many settings
- No support for nested configuration

### 2. Python Config Files (Rejected)

Use Python files (e.g., `config.py`) for configuration.

Rejected because:
- Mixes code with configuration
- Security concerns with executable config
- Harder to manage per-environment

### 3. YAML/TOML Configuration (Deferred)

Use YAML or TOML format instead of JSONP.

Deferred because:
- JsonPreprocessor already available and used
- JSONP provides needed features (variables, includes)
- May add YAML support if demand arises

## References

- [JsonPreprocessor Documentation](https://github.com/test-fullautomation/python-jsonpreprocessor)
- [12-Factor App Config](https://12factor.net/config)
- Template: `EventBusClient/config/config.jsonp.template`
- Source: `EventBusClient/plugin_loader.py` (ConfigValidator, CONFIG_SCHEMA)
- Source: `EventBusClient/event_bus_client.py` (from_config, from_config_sync)
