#!/bin/sh
set -e

# Generate keys if they don't exist
python scripts/create_rs256_keys.py

# Execute the main command
exec "$@"