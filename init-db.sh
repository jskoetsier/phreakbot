#!/bin/bash
# PostgreSQL initialization script
set -e

# Create the database schema
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f /docker-entrypoint-initdb.d/dbschema.psql

# Verify tables were created
echo "Verifying tables were created:"
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -c "\dt"

echo "Database initialization complete!"
