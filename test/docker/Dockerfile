# Dockerfile for RabbitMQ 3.12.10 with x-rtopic plugin
FROM rabbitmq:3.12.10-management

# Copy the x-rtopic plugin file
COPY rabbitmq_rtopic_exchange-3.12.0.ez /opt/rabbitmq/plugins/rabbitmq_rtopic_exchange.ez

# Copy initialization script
COPY init-rabbitmq.sh /usr/local/bin/init-rabbitmq.sh
RUN chmod +x /usr/local/bin/init-rabbitmq.sh

# Copy custom entrypoint
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Enable the management plugin and x-rtopic plugin
RUN rabbitmq-plugins enable --offline rabbitmq_management rabbitmq_rtopic_exchange

# 5672: AMQP port
# 15672: Management UI port
EXPOSE 5672 15672

# Create directories for configuration and data
RUN mkdir -p /etc/rabbitmq /var/lib/rabbitmq

# Set proper permissions
RUN chown -R rabbitmq:rabbitmq /var/lib/rabbitmq /etc/rabbitmq

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD rabbitmq-diagnostics -q ping

CMD ["/usr/local/bin/docker-entrypoint.sh"]
