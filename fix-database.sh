#!/bin/bash
# PhreakBot Database Fix Script
# This script fixes the database initialization issue

# SSH into the server and execute the fix
ssh root@vuurstorm.nl << 'EOF'
cd /opt/phreakbot

echo "===== Stopping all containers and removing volumes ====="
docker-compose down -v

echo "===== Creating initialization script ====="
cat > init-db.sh << 'SCRIPT'
#!/bin/bash
# PostgreSQL initialization script
set -e

# Create the database schema
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f /docker-entrypoint-initdb.d/dbschema.psql

# Verify tables were created
echo "Verifying tables were created:"
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -c "\dt"

echo "Database initialization complete!"
SCRIPT

echo "===== Making initialization script executable ====="
chmod +x init-db.sh

echo "===== Updating docker-compose.yml ====="
cat > docker-compose.yml << 'YAML'
version: '3'

services:
  postgres:
    image: postgres:14-alpine
    restart: unless-stopped
    environment:
      - POSTGRES_USER=phreakbot
      - POSTGRES_PASSWORD=phreakbot
      - POSTGRES_DB=phreakbot
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./dbschema.psql:/docker-entrypoint-initdb.d/dbschema.psql:ro
      - ./init-db.sh:/docker-entrypoint-initdb.d/init-db.sh:ro

  phreakbot:
    build: .
    restart: unless-stopped
    depends_on:
      - postgres
    volumes:
      - ./config:/app/config
      - ./modules:/app/modules
      - ./extra_modules:/app/extra_modules
      - ./logs:/app/logs
      - ./startup.sh:/app/startup.sh
    environment:
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_USER=phreakbot
      - DB_PASSWORD=phreakbot
      - DB_NAME=phreakbot
      - IRC_SERVER=${IRC_SERVER:-irc.libera.chat}
      - IRC_PORT=${IRC_PORT:-6667}
      - IRC_NICKNAME=${IRC_NICKNAME:-PhreakBot}
      - IRC_CHANNEL=${IRC_CHANNEL:-#phreakbot}
      - OWNER_HOSTMASK=${OWNER_HOSTMASK:-*!user@host}
    command: /app/startup.sh

volumes:
  postgres_data:
YAML

echo "===== Starting PostgreSQL container only ====="
docker-compose up -d postgres

echo "===== Waiting for PostgreSQL to initialize (30 seconds) ====="
sleep 30

echo "===== PostgreSQL logs ====="
docker-compose logs postgres | tail -50

echo "===== Checking if tables exist ====="
POSTGRES_CONTAINER=$(docker-compose ps -q postgres)
docker exec -i $POSTGRES_CONTAINER psql -U phreakbot -d phreakbot -c "\dt"

echo "===== Starting PhreakBot container ====="
docker-compose up -d phreakbot

echo "===== Waiting for PhreakBot to start (10 seconds) ====="
sleep 10

echo "===== PhreakBot logs ====="
docker-compose logs phreakbot | tail -50

echo "===== Fix complete ====="
echo "If you still see database errors, check the full logs with:"
echo "docker-compose logs -f"
EOF
