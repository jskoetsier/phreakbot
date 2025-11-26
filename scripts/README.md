# PhreakBot Scripts

This directory contains all utility scripts for PhreakBot installation, deployment, and maintenance.

## Installation Scripts

### install-docker.sh
Installs Docker on Linux systems (Debian/Ubuntu-based).
```bash
./scripts/install-docker.sh
```

### install-docker.bat
Installs Docker on Windows systems.
```cmd
scripts\install-docker.bat
```

### install-pydle.sh
Installs the pydle IRC library and dependencies.
```bash
./scripts/install-pydle.sh
```

## Database Scripts

### init-db.sh
Initializes the PostgreSQL database with the required schema.
```bash
./scripts/init-db.sh
```

### direct-init.sh
Direct database initialization script used by Docker Compose.
```bash
./scripts/direct-init.sh
```

### fix-db.sh
Fixes database connection issues and repairs the schema.
```bash
./scripts/fix-db.sh
```

## Runtime Scripts

### startup.sh
Main entrypoint script for starting PhreakBot in Docker containers.
```bash
./scripts/startup.sh
```

## Usage Notes

- All scripts should be executable (`chmod +x scripts/*.sh`)
- Most scripts require proper environment variables to be set
- Database scripts assume PostgreSQL is running and accessible
- Docker scripts should be run with appropriate permissions
