#!/bin/bash
# Script to set the bot owner in the database
# Usage: ./set-owner.sh <hostmask>
# Example: ./set-owner.sh "*!user@host"

# Check if hostmask parameter is provided
if [ -z "$1" ]; then
  echo "Error: No hostmask provided"
  echo "Usage: ./set-owner.sh <hostmask>"
  echo "Example: ./set-owner.sh \"*!user@host\""
  exit 1
fi

HOSTMASK="$1"
OWNER_USERNAME="owner"

echo "Setting owner with hostmask: $HOSTMASK"

# SQL commands to add owner
SQL_COMMANDS="
-- Check if owner user already exists, if not create it
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM phreakbot_users WHERE username = '$OWNER_USERNAME') THEN
    INSERT INTO phreakbot_users (username) VALUES ('$OWNER_USERNAME');
  END IF;
END \$\$;

-- Get the owner user ID
WITH owner_user AS (
  SELECT id FROM phreakbot_users WHERE username = '$OWNER_USERNAME'
)
-- Delete any existing hostmask for this user to avoid conflicts
DELETE FROM phreakbot_hostmasks
WHERE users_id = (SELECT id FROM owner_user);

-- Add the hostmask for the owner
WITH owner_user AS (
  SELECT id FROM phreakbot_users WHERE username = '$OWNER_USERNAME'
)
INSERT INTO phreakbot_hostmasks (users_id, hostmask)
VALUES ((SELECT id FROM owner_user), '$HOSTMASK');

-- Delete any existing permissions for this user to avoid conflicts
WITH owner_user AS (
  SELECT id FROM phreakbot_users WHERE username = '$OWNER_USERNAME'
)
DELETE FROM phreakbot_perms
WHERE users_id = (SELECT id FROM owner_user);

-- Add admin permission for the owner (global permission with empty channel)
WITH owner_user AS (
  SELECT id FROM phreakbot_users WHERE username = '$OWNER_USERNAME'
)
INSERT INTO phreakbot_perms (users_id, permission, channel)
VALUES
  ((SELECT id FROM owner_user), 'admin', ''),
  ((SELECT id FROM owner_user), 'owner', '');
"

# Execute the SQL commands in the PostgreSQL container
echo "Executing SQL commands in the database..."
docker-compose exec -T postgres psql -U postgres -d phreakbot -c "$SQL_COMMANDS"

if [ $? -eq 0 ]; then
  echo "Owner successfully set to $HOSTMASK"
  echo "The owner now has admin and owner permissions"
else
  echo "Failed to set owner. Make sure the database and containers are running."
  exit 1
fi
