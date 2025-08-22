# Plugin Structure

## Custom Plugin

To create a custom plugin:

\- Create a directory for your plugin inside the `plugins` folder.
\- Implement required interfaces: `BaseExchangeHandler`, `BaseMessage`, `BaseSerializer`.
\- Register your plugin in the `config.jsonp` file.
\- Ensure your plugin is discoverable by `EventBusClient`.

Example structure for a plugin named `CustomPlugin`:

```plaintext
plugins/
    CustomPlugin/
        __init__.py
        custom_exchange_handler.py
        custom_message.py
        custom_serializer.py
```

Built-in Plugins
- XRTopicExchangeHandler: Handles topic exchanges with RabbitMQ.
- BasicMessage: Default message class for basic message.
- PickleSerializer: Serializes messages using Pickle.
- JSONSerializer: Serializes messages to JSON.
- ProtobufSerializer: Serializes messages using Protocol Buffers.

You can use these built-in plugins directly or extend them for custom functionality.