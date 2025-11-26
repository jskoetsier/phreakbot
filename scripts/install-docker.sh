#!/bin/bash
# PhreakBot Docker Installation Script
# This script sets up PhreakBot to run in Docker

# Text formatting
BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
RESET="\033[0m"

echo -e "${BOLD}PhreakBot Docker Installation${RESET}"
echo "============================"
echo

# Check if Docker is installed
echo -e "${BOLD}Checking Docker installation...${RESET}"
if ! command -v docker &>/dev/null; then
    echo -e "${RED}Error: Docker not found. Please install Docker first.${RESET}"
    echo "Visit https://docs.docker.com/get-docker/ for installation instructions."
    exit 1
fi
echo -e "${GREEN}Docker is installed.${RESET}"

# Check if Docker Compose is installed
echo -e "\n${BOLD}Checking Docker Compose installation...${RESET}"
if ! command -v docker-compose &>/dev/null; then
    # Try docker compose (newer version)
    if ! docker compose version &>/dev/null; then
        echo -e "${RED}Error: Docker Compose not found. Please install Docker Compose first.${RESET}"
        echo "Visit https://docs.docker.com/compose/install/ for installation instructions."
        exit 1
    fi
    DOCKER_COMPOSE_CMD="docker compose"
else
    DOCKER_COMPOSE_CMD="docker-compose"
fi
echo -e "${GREEN}Docker Compose is installed.${RESET}"

# Create config directory if it doesn't exist
echo -e "\n${BOLD}Creating directories...${RESET}"
mkdir -p config modules extra_modules logs
echo -e "${GREEN}Directories created.${RESET}"

# Prompt for configuration
echo -e "\n${BOLD}Bot Configuration${RESET}"
echo "================="

# IRC Server
read -p "IRC Server [irc.libera.chat]: " IRC_SERVER
IRC_SERVER=${IRC_SERVER:-irc.libera.chat}

# IRC Port
read -p "IRC Port [6667]: " IRC_PORT
IRC_PORT=${IRC_PORT:-6667}

# Bot Nickname
read -p "Bot Nickname [PhreakBot]: " IRC_NICKNAME
IRC_NICKNAME=${IRC_NICKNAME:-PhreakBot}

# IRC Channel
read -p "IRC Channel [#phreakbot]: " IRC_CHANNEL
IRC_CHANNEL=${IRC_CHANNEL:-#phreakbot}

# Owner Hostmask
echo -e "\n${BOLD}Setting up bot owner...${RESET}"
echo -e "Enter the owner's hostmask in the format ${BOLD}*!user@host${RESET}"
echo -e "Example: *!john@example.com or *!*@192.168.1.100"
read -p "Owner hostmask [*!user@host]: " OWNER_HOSTMASK
OWNER_HOSTMASK=${OWNER_HOSTMASK:-*!user@host}

# Database Configuration
echo -e "\n${BOLD}Database Configuration${RESET}"
echo "====================="

# Database User
read -p "Database User [phreakbot]: " DB_USER
DB_USER=${DB_USER:-phreakbot}

# Database Password
read -p "Database Password [phreakbot]: " DB_PASSWORD
DB_PASSWORD=${DB_PASSWORD:-phreakbot}

# Database Name
read -p "Database Name [phreakbot]: " DB_NAME
DB_NAME=${DB_NAME:-phreakbot}

# Create .env file
echo -e "\n${BOLD}Creating .env file...${RESET}"
cat > .env << EOF
# PhreakBot Docker environment configuration
IRC_SERVER=${IRC_SERVER}
IRC_PORT=${IRC_PORT}
IRC_NICKNAME=${IRC_NICKNAME}
IRC_CHANNEL=${IRC_CHANNEL}
OWNER_HOSTMASK=${OWNER_HOSTMASK}

# Database configuration
POSTGRES_USER=${DB_USER}
POSTGRES_PASSWORD=${DB_PASSWORD}
POSTGRES_DB=${DB_NAME}
EOF
echo -e "${GREEN}.env file created.${RESET}"

# Update docker-compose.yml to include owner parameter
echo -e "\n${BOLD}Updating docker-compose.yml...${RESET}"
cat > docker-compose.yml << EOF
version: '3'

services:
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
    environment:
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - DB_NAME=${DB_NAME}
    command: >
      sh -c "python install.py --server \${IRC_SERVER:-${IRC_SERVER}}
             --port \${IRC_PORT:-${IRC_PORT}}
             --nickname \${IRC_NICKNAME:-${IRC_NICKNAME}}
             --channel \${IRC_CHANNEL:-${IRC_CHANNEL}}
             --owner \${OWNER_HOSTMASK:-${OWNER_HOSTMASK}}
             --config /app/config/config.json &&
             python phreakbot.py --config /app/config/config.json"

  postgres:
    image: postgres:14-alpine
    restart: unless-stopped
    environment:
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=${DB_NAME}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./dbschema.psql:/docker-entrypoint-initdb.d/dbschema.psql:ro

volumes:
  postgres_data:
EOF
echo -e "${GREEN}docker-compose.yml updated.${RESET}"

# Build and start the containers
echo -e "\n${BOLD}Building and starting Docker containers...${RESET}"
echo -e "${YELLOW}This may take a few minutes...${RESET}"
$DOCKER_COMPOSE_CMD up -d --build

# Check if containers are running
if [ $? -eq 0 ]; then
    echo -e "\n${BOLD}${GREEN}Installation complete!${RESET}"
    echo -e "PhreakBot is now running in Docker."
    echo -e "\nTo view logs:"
    echo -e "  ${BOLD}$DOCKER_COMPOSE_CMD logs -f phreakbot${RESET}"
    echo -e "\nTo stop the bot:"
    echo -e "  ${BOLD}$DOCKER_COMPOSE_CMD down${RESET}"
    echo -e "\nTo start the bot again:"
    echo -e "  ${BOLD}$DOCKER_COMPOSE_CMD up -d${RESET}"
    echo -e "\nBot owner: ${BOLD}${OWNER_HOSTMASK}${RESET}"
else
    echo -e "\n${RED}Error: Failed to start Docker containers.${RESET}"
    echo -e "Please check the logs for more information:"
    echo -e "  ${BOLD}$DOCKER_COMPOSE_CMD logs${RESET}"
    exit 1
fi
