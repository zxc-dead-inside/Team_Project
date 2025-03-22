#!/bin/sh
set -e

echo "Checking and creating RS256 keys if needed..."
python scripts/create_rs256_keys.py

# Set up database and run necessary scripts
echo "Setting up database..."
python scripts/setup_database.py

# Execute the main command
exec "$@"
