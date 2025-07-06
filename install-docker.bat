@echo off
:: PhreakBot Docker Installation Script for Windows
:: This script sets up PhreakBot to run in Docker

echo PhreakBot Docker Installation
echo ============================
echo.

:: Check if Docker is installed
echo Checking Docker installation...
where docker >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: Docker not found. Please install Docker first.
    echo Visit https://docs.docker.com/get-docker/ for installation instructions.
    pause
    exit /b 1
)
echo Docker is installed.

:: Check if Docker Compose is installed
echo.
echo Checking Docker Compose installation...
where docker-compose >nul 2>&1
if %ERRORLEVEL% neq 0 (
    :: Try docker compose (newer version)
    docker compose version >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo Error: Docker Compose not found. Please install Docker Compose first.
        echo Visit https://docs.docker.com/compose/install/ for installation instructions.
        pause
        exit /b 1
    )
    set DOCKER_COMPOSE_CMD=docker compose
) else (
    set DOCKER_COMPOSE_CMD=docker-compose
)
echo Docker Compose is installed.

:: Create config directory if it doesn't exist
echo.
echo Creating directories...
if not exist config mkdir config
if not exist modules mkdir modules
if not exist extra_modules mkdir extra_modules
if not exist logs mkdir logs
echo Directories created.

:: Prompt for configuration
echo.
echo Bot Configuration
echo ===============

:: IRC Server
set /p IRC_SERVER="IRC Server [irc.libera.chat]: "
if "%IRC_SERVER%"=="" set IRC_SERVER=irc.libera.chat

:: IRC Port
set /p IRC_PORT="IRC Port [6667]: "
if "%IRC_PORT%"=="" set IRC_PORT=6667

:: Bot Nickname
set /p IRC_NICKNAME="Bot Nickname [PhreakBot]: "
if "%IRC_NICKNAME%"=="" set IRC_NICKNAME=PhreakBot

:: IRC Channel
set /p IRC_CHANNEL="IRC Channel [#phreakbot]: "
if "%IRC_CHANNEL%"=="" set IRC_CHANNEL=#phreakbot

:: Owner Hostmask
echo.
echo Setting up bot owner...
echo Enter the owner's hostmask in the format *!user@host
echo Example: *!john@example.com or *!*@192.168.1.100
set /p OWNER_HOSTMASK="Owner hostmask [*!user@host]: "
if "%OWNER_HOSTMASK%"=="" set OWNER_HOSTMASK=*!user@host

:: Database Configuration
echo.
echo Database Configuration
echo =====================

:: Database User
set /p DB_USER="Database User [phreakbot]: "
if "%DB_USER%"=="" set DB_USER=phreakbot

:: Database Password
set /p DB_PASSWORD="Database Password [phreakbot]: "
if "%DB_PASSWORD%"=="" set DB_PASSWORD=phreakbot

:: Database Name
set /p DB_NAME="Database Name [phreakbot]: "
if "%DB_NAME%"=="" set DB_NAME=phreakbot

:: Create .env file
echo.
echo Creating .env file...
(
echo # PhreakBot Docker environment configuration
echo IRC_SERVER=%IRC_SERVER%
echo IRC_PORT=%IRC_PORT%
echo IRC_NICKNAME=%IRC_NICKNAME%
echo IRC_CHANNEL=%IRC_CHANNEL%
echo OWNER_HOSTMASK=%OWNER_HOSTMASK%
echo.
echo # Database configuration
echo POSTGRES_USER=%DB_USER%
echo POSTGRES_PASSWORD=%DB_PASSWORD%
echo POSTGRES_DB=%DB_NAME%
) > .env
echo .env file created.

:: Update docker-compose.yml to include owner parameter
echo.
echo Updating docker-compose.yml...
(
echo version: '3'
echo.
echo services:
echo   phreakbot:
echo     build: .
echo     restart: unless-stopped
echo     depends_on:
echo       - postgres
echo     volumes:
echo       - ./config:/app/config
echo       - ./modules:/app/modules
echo       - ./extra_modules:/app/extra_modules
echo       - ./logs:/app/logs
echo     environment:
echo       - DB_HOST=postgres
echo       - DB_PORT=5432
echo       - DB_USER=%DB_USER%
echo       - DB_PASSWORD=%DB_PASSWORD%
echo       - DB_NAME=%DB_NAME%
echo     command: ^>
echo       sh -c "python install.py --server ${IRC_SERVER:-%IRC_SERVER%}
echo              --port ${IRC_PORT:-%IRC_PORT%}
echo              --nickname ${IRC_NICKNAME:-%IRC_NICKNAME%}
echo              --channel ${IRC_CHANNEL:-%IRC_CHANNEL%}
echo              --owner ${OWNER_HOSTMASK:-%OWNER_HOSTMASK%}
echo              --config /app/config/config.json ^&^&
echo              python phreakbot.py --config /app/config/config.json"
echo.
echo   postgres:
echo     image: postgres:14-alpine
echo     restart: unless-stopped
echo     environment:
echo       - POSTGRES_USER=%DB_USER%
echo       - POSTGRES_PASSWORD=%DB_PASSWORD%
echo       - POSTGRES_DB=%DB_NAME%
echo     volumes:
echo       - postgres_data:/var/lib/postgresql/data
echo       - ./dbschema.psql:/docker-entrypoint-initdb.d/dbschema.psql:ro
echo.
echo volumes:
echo   postgres_data:
) > docker-compose.yml
echo docker-compose.yml updated.

:: Build and start the containers
echo.
echo Building and starting Docker containers...
echo This may take a few minutes...
%DOCKER_COMPOSE_CMD% up -d --build

:: Check if containers are running
if %ERRORLEVEL% equ 0 (
    echo.
    echo Installation complete!
    echo PhreakBot is now running in Docker.
    echo.
    echo To view logs:
    echo   %DOCKER_COMPOSE_CMD% logs -f phreakbot
    echo.
    echo To stop the bot:
    echo   %DOCKER_COMPOSE_CMD% down
    echo.
    echo To start the bot again:
    echo   %DOCKER_COMPOSE_CMD% up -d
    echo.
    echo Bot owner: %OWNER_HOSTMASK%
) else (
    echo.
    echo Error: Failed to start Docker containers.
    echo Please check the logs for more information:
    echo   %DOCKER_COMPOSE_CMD% logs
    exit /b 1
)

pause
