#!/bin/bash
# PhreakBot Database Fix Script
# This script provides a definitive fix for the database initialization issue

# Create a direct database initialization script
cat > direct-init.sh << 'EOF'
#!/bin/bash
set -e

echo "Waiting for PostgreSQL to start..."
until pg_isready -h postgres -U phreakbot; do
  sleep 1
done

echo "PostgreSQL is ready. Creating database schema..."
psql -h postgres -U phreakbot -d phreakbot << 'SQL'
DROP TABLE IF EXISTS phreakbot_quotes;
DROP TABLE IF EXISTS phreakbot_karma_who;
DROP TABLE IF EXISTS phreakbot_karma_why;
DROP TABLE IF EXISTS phreakbot_karma;
DROP TABLE IF EXISTS phreakbot_infoitems;
DROP TABLE IF EXISTS phreakbot_perms;
DROP TABLE IF EXISTS phreakbot_hostmasks;
DROP TABLE IF EXISTS phreakbot_users;
DROP TYPE IF EXISTS phreakbot_karma_direction;

CREATE TABLE phreakbot_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    dob DATE,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    is_owner BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE phreakbot_hostmasks (
    id SERIAL,
    users_id INT NOT NULL,
    hostmask VARCHAR(255) NOT NULL,
    PRIMARY KEY (id, users_id, hostmask),
    UNIQUE (hostmask),
    CONSTRAINT phreakbot_users_id_fkey FOREIGN KEY (users_id)
      REFERENCES phreakbot_users (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION
);

CREATE TABLE phreakbot_perms (
    id SERIAL,
    users_id INT NOT NULL,
    permission VARCHAR(50) NOT NULL,
    channel VARCHAR(150) NOT NULL DEFAULT '',
    PRIMARY KEY (id, users_id, permission, channel),
    UNIQUE (users_id, permission, channel),
    CONSTRAINT phreakbot_perms_users_id_fkey FOREIGN KEY (users_id)
      REFERENCES phreakbot_users (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION
);

CREATE TABLE phreakbot_infoitems (
    id SERIAL,
    users_id INT NOT NULL,
    item TEXT NOT NULL,
    value TEXT NOT NULL,
    channel VARCHAR(150) NOT NULL,
    insert_time timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE (item, value, channel),
    CONSTRAINT phreakbot_infoitems_users_id_fkey FOREIGN KEY (users_id)
      REFERENCES phreakbot_users (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION
);

CREATE TABLE phreakbot_karma (
    id SERIAL UNIQUE,
    item TEXT NOT NULL,
    karma INT NOT NULL DEFAULT 0,
    channel VARCHAR(150) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (item, channel)
);

CREATE TYPE phreakbot_karma_direction AS ENUM ('up', 'down');

CREATE TABLE phreakbot_karma_why (
    id SERIAL,
    karma_id INT NOT NULL,
    direction phreakbot_karma_direction NOT NULL,
    reason TEXT NOT NULL,
    channel VARCHAR(150) NOT NULL,
    update_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, direction, reason, channel),
    UNIQUE (karma_id, direction, reason, channel),
    CONSTRAINT phreakbot_karma_why_karma_id_fkey FOREIGN KEY (karma_id)
      REFERENCES phreakbot_karma (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION
);

CREATE TABLE phreakbot_karma_who (
    id SERIAL,
    karma_id INT NOT NULL,
    users_id INT NOT NULL,
    direction phreakbot_karma_direction NOT NULL,
    amount INT NOT NULL,
    update_time timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, karma_id),
    UNIQUE (karma_id, users_id, direction),
    CONSTRAINT phreakbot_karma_who_karma_id_fkey FOREIGN KEY (karma_id)
      REFERENCES phreakbot_karma (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION,
    CONSTRAINT phreakbot_karma_who_users_id_fkey FOREIGN KEY (users_id)
      REFERENCES phreakbot_users (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION
);

CREATE TABLE phreakbot_quotes (
    id SERIAL,
    users_id INT NOT NULL,
    quote TEXT NOT NULL,
    channel VARCHAR(150) NOT NULL,
    insert_time timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT phreakbot_quotes_users_id_fkey FOREIGN KEY (users_id)
      REFERENCES phreakbot_users (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION
);

INSERT INTO phreakbot_users (username) VALUES ('phreakbot_import_user');
INSERT INTO phreakbot_hostmasks (users_id, hostmask) VALUES (1, 'phreakbot_import_user');

SELECT 'Database schema created successfully!' AS result;
SQL

echo "Verifying tables were created:"
psql -h postgres -U phreakbot -d phreakbot -c "\dt"

echo "Database initialization complete!"
EOF

# Update docker-compose.yml to use a different approach
cat > docker-compose.yml << 'EOF'
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

  db-init:
    image: postgres:14-alpine
    depends_on:
      - postgres
    volumes:
      - ./direct-init.sh:/direct-init.sh
    command: /direct-init.sh
    environment:
      - PGPASSWORD=phreakbot

  phreakbot:
    build: .
    restart: unless-stopped
    depends_on:
      - db-init
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
EOF

# Make the initialization script executable
chmod +x direct-init.sh

echo "Database fix script created. Push these changes to the repository and run the following commands on the server:"
echo "cd /opt/phreakbot"
echo "git pull"
echo "docker-compose down -v"
echo "docker-compose up -d"
