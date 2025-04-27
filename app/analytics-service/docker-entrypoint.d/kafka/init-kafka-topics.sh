#!/bin/sh

KT="/opt/bitnami/kafka/bin/kafka-topics.sh"

echo "Waiting for kafka..."
"$KT" --bootstrap-server localhost:9092 --list

echo "Creating kafka topics"
"$KT" --bootstrap-server localhost:9092 --create --if-not-exists --topic "$KAFKA_TOPIC" --replication-factor 3 --config min.insync.replicas=2

echo "Successfully created the following topics:"
"$KT" --bootstrap-server localhost:9092 --list
