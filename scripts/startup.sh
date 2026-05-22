#!/bin/sh
# PhreakBot Docker startup script

# Print environment variables for debugging
echo "Starting PhreakBot with the following configuration:"
echo "IRC Server: $IRC_SERVER"
echo "IRC Port: $IRC_PORT"
echo "IRC Nickname: $IRC_NICKNAME"
echo "IRC Channel: $IRC_CHANNEL"
echo "Database: $DB_HOST:$DB_PORT/$DB_NAME"
echo "Bot Version: ${BOT_VERSION:-standard}"

# Initialize the database and wait for PostgreSQL to be ready
python scripts/init_db.py

# Run the installation script
python install.py \
  --server "$IRC_SERVER" \
  --port "$IRC_PORT" \
  --nickname "$IRC_NICKNAME" \
  --channel "$IRC_CHANNEL" \
  --remote-ssh "${REMOTE_SSH_COMMAND:-}" \
  --remote-dir "${REMOTE_DIRECTORY:-/opt/phreakbot}" \
  --config /app/config/config.json \
  --db-host "$DB_HOST" \
  --db-port "$DB_PORT" \
  --db-user "$DB_USER" \
  --db-password "$DB_PASSWORD" \
  --db-name "$DB_NAME"

# Start the bot based on the BOT_VERSION environment variable
if [ "${BOT_VERSION}" = "pydle" ]; then
  echo "Starting PhreakBot with pydle version..."
  python phreakbot_pydle.py --config /app/config/config.json
else
  echo "Starting PhreakBot with standard version..."
  python phreakbot.py --config /app/config/config.json
fi
