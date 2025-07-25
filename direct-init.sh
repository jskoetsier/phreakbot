#!/bin/bash
set -e

echo "Waiting for PostgreSQL to start..."
until pg_isready -h postgres -U phreakbot; do
  sleep 1
done

echo "PostgreSQL is ready. Checking if database schema exists..."

# Check if the phreakbot_users table exists
TABLE_EXISTS=$(psql -h postgres -U phreakbot -d phreakbot -t -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'phreakbot_users')")

if [[ $TABLE_EXISTS == *"t"* ]]; then
  echo "Database schema already exists. Skipping initialization."
else
  echo "Creating database schema..."
  psql -h postgres -U phreakbot -d phreakbot << 'SQL'

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

-- Only insert the import user if it doesn't exist
INSERT INTO phreakbot_users (username)
SELECT 'phreakbot_import_user'
WHERE NOT EXISTS (SELECT 1 FROM phreakbot_users WHERE username = 'phreakbot_import_user');

-- Only insert the hostmask if it doesn't exist
INSERT INTO phreakbot_hostmasks (users_id, hostmask)
SELECT 1, 'phreakbot_import_user'
WHERE NOT EXISTS (SELECT 1 FROM phreakbot_hostmasks WHERE hostmask = 'phreakbot_import_user');

SELECT 'Database schema created successfully!' AS result;
SQL

  echo "Verifying tables were created:"
  psql -h postgres -U phreakbot -d phreakbot -c "\dt"
fi

echo "Database initialization complete!"
