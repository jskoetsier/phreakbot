#!/bin/sh
# PhreakBot Docker startup script

# Print environment variables for debugging
echo "Starting PhreakBot with the following configuration:"
echo "IRC Server: $IRC_SERVER"
echo "IRC Port: $IRC_PORT"
echo "IRC Nickname: $IRC_NICKNAME"
echo "IRC Channel: $IRC_CHANNEL"
echo "Owner Hostmask: $OWNER_HOSTMASK"
echo "Database: $DB_HOST:$DB_PORT/$DB_NAME"

# Run the installation script
python install.py \
  --server "$IRC_SERVER" \
  --port "$IRC_PORT" \
  --nickname "$IRC_NICKNAME" \
  --channel "$IRC_CHANNEL" \
  --owner "$OWNER_HOSTMASK" \
  --config /app/config/config.json

# Start the bot
python phreakbot.py --config /app/config/config.json
