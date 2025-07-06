#!/bin/bash
# Script to update PhreakBot on the remote server

# Set variables
REMOTE_SERVER="root@vuurstorm.nl"
REMOTE_DIR="/opt/phreakbot"

# Display header
echo "===== PhreakBot Remote Update Script ====="
echo "This script will update PhreakBot on the remote server."
echo "Remote server: $REMOTE_SERVER"
echo "Remote directory: $REMOTE_DIR"
echo ""

# Connect to remote server and perform update
echo "Connecting to remote server..."
ssh $REMOTE_SERVER << 'EOF'
    cd /opt/phreakbot

    echo "===== Pulling latest changes from GitHub ====="
    git pull

    echo "===== Stopping containers ====="
    docker-compose down

    echo "===== Rebuilding PhreakBot container ====="
    docker-compose build --no-cache phreakbot

    echo "===== Starting containers ====="
    docker-compose up -d

    echo "===== Waiting for containers to start ====="
    sleep 5

    echo "===== Container status ====="
    docker-compose ps

    echo "===== Recent logs ====="
    docker-compose logs --tail 20 phreakbot
EOF

echo ""
echo "===== Update complete ====="
echo "Check the logs above for any errors."
echo "To view more logs, run: ssh $REMOTE_SERVER \"cd $REMOTE_DIR && docker-compose logs --tail 50 phreakbot\""
