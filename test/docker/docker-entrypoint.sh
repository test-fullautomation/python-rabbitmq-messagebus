#!/bin/bash

rabbitmq-server &
RABBITMQ_PID=$!

# Wait a moment for RabbitMQ to start
sleep 10

/usr/local/bin/init-rabbitmq.sh

wait $RABBITMQ_PID
