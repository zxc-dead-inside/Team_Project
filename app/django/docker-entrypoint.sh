#!/bin/bash
set -e

# Run the database setup script
python scripts/docker_compose_setup.py

exec "$@"
