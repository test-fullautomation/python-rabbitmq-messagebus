#!/bin/bash

# Wait for RabbitMQ to be ready
until rabbitmqctl node_health_check; do
  echo "Waiting for RabbitMQ to be ready..."
  sleep 2
done

echo "RabbitMQ is ready. Setting up guest user..."

# Need to create guest user if not exists
# so that the client can connect unauthenticated
if rabbitmqctl list_users | grep -q "^guest"; then
    echo "Guest user already exists"
else
    echo "Creating guest user..."
    rabbitmqctl add_user guest guest
    rabbitmqctl set_user_tags guest administrator
    rabbitmqctl set_permissions -p / guest ".*" ".*" ".*"
    echo "Guest user created successfully"
fi

echo "Guest user setup complete"
