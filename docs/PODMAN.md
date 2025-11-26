# Using PhreakBot with Podman

PhreakBot is fully compatible with both Docker and Podman. This guide shows you how to run PhreakBot using Podman and podman-compose.

## What is Podman?

Podman is a daemonless container engine for developing, managing, and running OCI Containers on your Linux system. It's a drop-in replacement for Docker that offers:

- **Daemonless architecture**: No root-running daemon required
- **Rootless containers**: Run containers without root privileges
- **Better security**: Improved isolation and security features
- **Docker compatibility**: Compatible with most Docker commands and Dockerfiles

## Prerequisites

### Installing Podman

#### Fedora/RHEL/CentOS
```bash
sudo dnf install podman podman-compose
```

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install podman podman-compose
```

#### macOS
```bash
brew install podman podman-compose
```

#### Arch Linux
```bash
sudo pacman -S podman podman-compose
```

## Running PhreakBot with Podman

### Using podman-compose (Recommended)

The `docker-compose.yml` file is fully compatible with podman-compose:

```bash
# Start PhreakBot
podman-compose up -d

# View logs
podman-compose logs -f

# Stop PhreakBot
podman-compose down

# Rebuild containers
podman-compose build
podman-compose up -d
```

### Using Podman directly

If you prefer to use Podman without podman-compose:

#### 1. Create a network
```bash
podman network create phreakbot-network
```

#### 2. Start PostgreSQL
```bash
podman run -d \
  --name phreakbot-postgres \
  --network phreakbot-network \
  -e POSTGRES_USER=phreakbot \
  -e POSTGRES_PASSWORD=phreakbot \
  -e POSTGRES_DB=phreakbot \
  -v postgres_data:/var/lib/postgresql/data:Z \
  docker.io/postgres:14-alpine
```

#### 3. Initialize the database
```bash
# Wait a few seconds for PostgreSQL to start
sleep 5

podman run --rm \
  --network phreakbot-network \
  -v ./scripts/direct-init.sh:/direct-init.sh:Z \
  -v ./dbschema.psql:/dbschema.psql:Z \
  -e PGPASSWORD=phreakbot \
  -e PGHOST=phreakbot-postgres \
  -e PGUSER=phreakbot \
  -e PGDATABASE=phreakbot \
  docker.io/postgres:14-alpine \
  /direct-init.sh
```

#### 4. Build and run PhreakBot
```bash
# Build the image
podman build -t phreakbot .

# Run PhreakBot
podman run -d \
  --name phreakbot \
  --network phreakbot-network \
  -v ./config:/app/config:Z \
  -v ./modules:/app/modules:Z \
  -v ./extra_modules:/app/extra_modules:Z \
  -v ./logs:/app/logs:Z \
  -e DB_HOST=phreakbot-postgres \
  -e DB_PORT=5432 \
  -e DB_USER=phreakbot \
  -e DB_PASSWORD=phreakbot \
  -e DB_NAME=phreakbot \
  phreakbot
```

## Podman-Specific Features

### SELinux Compatibility

The `:Z` flag in volume mounts ensures proper SELinux labeling for systems with SELinux enabled (like Fedora, RHEL, CentOS):

```yaml
volumes:
  - ./config:/app/config:Z
```

This is handled automatically in the `docker-compose.yml` file and works seamlessly on both SELinux and non-SELinux systems.

### Rootless Mode

Podman can run in rootless mode, which means containers run without requiring root privileges:

```bash
# Check if running rootless
podman info | grep rootless

# Run rootless containers (default for non-root users)
podman-compose up -d
```

### Container Management

```bash
# List running containers
podman ps

# View logs
podman logs phreakbot

# Execute commands in container
podman exec -it phreakbot /bin/sh

# Stop containers
podman stop phreakbot

# Remove containers
podman rm phreakbot

# View images
podman images

# Remove images
podman rmi phreakbot
```

### Pod Management

Podman also supports pods (similar to Kubernetes):

```bash
# List pods created by podman-compose
podman pod list

# View pod details
podman pod inspect phreakbot_phreakbot
```

## Troubleshooting

### Permission Issues

If you encounter permission issues with volumes:

```bash
# Fix permissions for config directory
chmod -R 755 ./config ./modules ./extra_modules ./logs

# Or run with appropriate user ID
podman-compose up -d
```

### Network Issues

If containers can't communicate:

```bash
# Recreate the network
podman network rm phreakbot-network
podman network create phreakbot-network

# Restart containers
podman-compose down
podman-compose up -d
```

### Database Connection Issues

If the bot can't connect to the database:

```bash
# Check if PostgreSQL is running
podman ps | grep postgres

# Check PostgreSQL logs
podman logs phreakbot-postgres

# Test database connection
podman exec -it phreakbot-postgres psql -U phreakbot -d phreakbot
```

### Volume Persistence

Named volumes are stored differently in Podman:

```bash
# List volumes
podman volume ls

# Inspect volume
podman volume inspect postgres_data

# Backup volume
podman volume export postgres_data > postgres_backup.tar
```

## Differences from Docker

While Podman is mostly compatible with Docker, there are some differences:

1. **No daemon**: Podman doesn't use a background daemon
2. **Rootless by default**: Better security with rootless containers
3. **SELinux support**: Built-in SELinux labeling with `:Z` and `:z` flags
4. **Pod support**: Native support for Kubernetes-style pods
5. **Systemd integration**: Easy systemd service generation

## Systemd Integration

You can generate systemd service files for automatic startup:

```bash
# Generate systemd service for rootless user
podman generate systemd --name phreakbot --files

# Move to user systemd directory
mkdir -p ~/.config/systemd/user/
mv container-phreakbot.service ~/.config/systemd/user/

# Enable and start service
systemctl --user enable container-phreakbot.service
systemctl --user start container-phreakbot.service

# Enable lingering (start on boot)
loginctl enable-linger $USER
```

## Migration from Docker

If you're migrating from Docker to Podman:

1. Stop Docker containers:
   ```bash
   docker-compose down
   ```

2. Export Docker volumes (if needed):
   ```bash
   docker volume ls
   docker run --rm -v postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .
   ```

3. Import to Podman:
   ```bash
   podman volume create postgres_data
   podman run --rm -v postgres_data:/data -v $(pwd):/backup:Z alpine tar xzf /backup/postgres_backup.tar.gz -C /data
   ```

4. Start with Podman:
   ```bash
   podman-compose up -d
   ```

## Additional Resources

- [Podman Documentation](https://docs.podman.io/)
- [Podman Compose](https://github.com/containers/podman-compose)
- [Transitioning from Docker to Podman](https://developers.redhat.com/blog/2020/11/19/transitioning-from-docker-to-podman)
