# PhreakBot Administrator Handbook

**Version**: 0.1.29
**Last Updated**: 2025-11-27

This handbook provides comprehensive guidance for PhreakBot administrators, covering installation, configuration, module management, user management, and security best practices.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Database Management](#database-management)
5. [User Management](#user-management)
6. [Permission System](#permission-system)
7. [Module Management](#module-management)
8. [Channel Management](#channel-management)
9. [Security Best Practices](#security-best-practices)
10. [Monitoring & Maintenance](#monitoring--maintenance)
11. [Troubleshooting](#troubleshooting)
12. [Backup & Recovery](#backup--recovery)
13. [Performance Optimization](#performance-optimization)
14. [Deployment Options](#deployment-options)

---

## Getting Started

### Prerequisites

Before installing PhreakBot, ensure you have:

- **Python 3.8+** (Python 3.11+ recommended)
- **PostgreSQL 12+** (14+ recommended for better performance)
- **Git** (for cloning the repository)
- **Root or sudo access** (for system-level installation)
- **Stable network connection** (for IRC connectivity)

### System Requirements

**Minimum**:
- CPU: 1 core
- RAM: 512 MB
- Disk: 1 GB
- Network: 1 Mbps

**Recommended**:
- CPU: 2+ cores
- RAM: 2 GB+
- Disk: 5 GB+ (for logs and database)
- Network: 10 Mbps+

---

## Installation

### Option 1: Docker/Podman Deployment (Recommended)

#### Using Docker Compose

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/phreakbot.git
   cd phreakbot
   ```

2. **Configure the bot**:
   ```bash
   cp config.json.pydle.example config/config.json
   nano config/config.json
   ```

3. **Start the bot**:
   ```bash
   docker-compose up -d
   ```

4. **View logs**:
   ```bash
   docker-compose logs -f
   ```

#### Using Podman Compose

Podman offers better security with rootless containers:

```bash
# Install podman (if not already installed)
sudo dnf install podman podman-compose  # Fedora/RHEL
sudo apt-get install podman podman-compose  # Ubuntu/Debian

# Start the bot
podman-compose up -d

# View logs
podman-compose logs -f
```

**See `/docs/PODMAN.md` for detailed Podman-specific instructions.**

---

### Option 2: Manual Installation

#### 1. Install Dependencies

**On Ubuntu/Debian**:
```bash
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv postgresql postgresql-contrib git
```

**On Fedora/RHEL/CentOS**:
```bash
sudo dnf install python3 python3-pip postgresql-server postgresql-contrib git
```

**On macOS**:
```bash
brew install python postgresql git
```

#### 2. Clone Repository

```bash
git clone https://github.com/yourusername/phreakbot.git
cd phreakbot
```

#### 3. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 4. Install Python Dependencies

```bash
pip install -r requirements.txt
```

#### 5. Setup PostgreSQL

**On Linux**:
```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres createuser -P phreakbot
sudo -u postgres createdb -O phreakbot phreakbot

# Initialize schema
psql -U phreakbot -d phreakbot -f dbschema.psql
```

**On macOS**:
```bash
brew services start postgresql

# Create database and user
createuser -P phreakbot
createdb -O phreakbot phreakbot
psql -U phreakbot -d phreakbot -f dbschema.psql
```

#### 6. Configure Bot

```bash
cp config.json.pydle.example config.json
nano config.json
```

#### 7. Start Bot

```bash
python3 phreakbot.py --config config.json
```

#### 8. Run as a Service (Optional)

Create a systemd service file `/etc/systemd/system/phreakbot.service`:

```ini
[Unit]
Description=PhreakBot IRC Bot
After=network.target postgresql.service

[Service]
Type=simple
User=phreakbot
WorkingDirectory=/opt/phreakbot
ExecStart=/opt/phreakbot/venv/bin/python3 /opt/phreakbot/phreakbot.py --config /opt/phreakbot/config.json
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable phreakbot
sudo systemctl start phreakbot
```

---

## Configuration

### Configuration File Structure

The `config.json` file contains all bot settings:

```json
{
    "server": "irc.libera.chat",
    "port": 6667,
    "nickname": "PhreakBot",
    "realname": "PhreakBot IRC Bot",
    "channels": ["#phreakbot", "#test"],
    "trigger": "!",
    "max_output_lines": 3,
    "use_tls": true,
    "tls_verify": true,
    "log_file": "phreakbot.log",
    "db_host": "localhost",
    "db_port": "5432",
    "db_user": "phreakbot",
    "db_password": "your_secure_password",
    "db_name": "phreakbot"
}
```

### Configuration Options

| Option | Type | Description | Default |
|--------|------|-------------|---------|
| `server` | string | IRC server hostname | Required |
| `port` | integer | IRC server port | 6667 |
| `nickname` | string | Bot's IRC nickname | Required |
| `realname` | string | Bot's real name | Required |
| `channels` | array | Channels to auto-join | `[]` |
| `trigger` | string | Command trigger character | `!` |
| `max_output_lines` | integer | Max lines per response | 3 |
| `use_tls` | boolean | Use TLS/SSL connection | false |
| `tls_verify` | boolean | Verify TLS certificates | true |
| `log_file` | string | Log file path | `phreakbot.log` |
| `db_host` | string | PostgreSQL hostname | `localhost` |
| `db_port` | string | PostgreSQL port | `5432` |
| `db_user` | string | Database username | Required |
| `db_password` | string | Database password | Required |
| `db_name` | string | Database name | Required |

### Security Recommendations

1. **Always use TLS** for production deployments:
   ```json
   "use_tls": true,
   "tls_verify": true
   ```

2. **Use strong database password**:
   ```bash
   # Generate secure password
   openssl rand -base64 32
   ```

3. **Restrict file permissions**:
   ```bash
   chmod 600 config.json
   ```

4. **Never commit `config.json` to version control**:
   ```bash
   # Already in .gitignore, but verify:
   git check-ignore config.json
   ```

---

## Database Management

### Database Schema

PhreakBot uses PostgreSQL with the following core tables:

- **users**: User accounts and metadata
- **hostmasks**: User authentication via IRC hostmasks
- **permissions**: Permission grants (global and channel-specific)
- **infoitems**: User-created information items
- **quotes**: Channel quotes
- **karma**: Karma tracking
- **karma_reasons**: Karma change reasons
- **birthdays**: User birthday tracking
- **autovoice**: Autovoice channel settings
- **autoop**: Auto-op user lists

### Common Database Tasks

#### View Database Connection Status

```bash
# Via docker/podman
docker exec phreakbot-postgres psql -U phreakbot -d phreakbot -c "\conninfo"

# Via local psql
psql -U phreakbot -d phreakbot -c "\conninfo"
```

#### List All Users

```sql
SELECT id, username, is_owner, is_admin, created_at
FROM users
ORDER BY created_at DESC;
```

#### List User Permissions

```sql
-- Global permissions
SELECT u.username, p.permission
FROM permissions p
JOIN users u ON p.user_id = u.id
WHERE p.channel IS NULL
ORDER BY u.username, p.permission;

-- Channel-specific permissions
SELECT u.username, p.channel, p.permission
FROM permissions p
JOIN users u ON p.user_id = u.id
WHERE p.channel IS NOT NULL
ORDER BY u.username, p.channel, p.permission;
```

#### Clean Up Old Data

```sql
-- Delete old karma reasons (older than 90 days)
DELETE FROM karma_reasons
WHERE created_at < NOW() - INTERVAL '90 days';

-- Delete quotes from channels bot no longer monitors
DELETE FROM quotes
WHERE channel NOT IN ('#phreaky', '#frys-ix');
```

#### Database Maintenance

```sql
-- Vacuum and analyze for performance
VACUUM ANALYZE;

-- Reindex all tables
REINDEX DATABASE phreakbot;

-- Check database size
SELECT pg_size_pretty(pg_database_size('phreakbot'));

-- Check table sizes
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## User Management

### Initial Setup: Claiming Ownership

When the bot first starts, no owner exists. The first user to claim ownership becomes the bot owner:

1. Join a channel with the bot
2. Use the command:
   ```irc
   !owner claim
   ```

3. Verify ownership:
   ```irc
   !whoami
   ```

**Important**: Only claim ownership once. After this, ownership can only be transferred via database.

### Registering Users

#### Single User Registration

```irc
!meet Alice
```

This will:
1. Create a user account for "Alice"
2. Perform a WHO lookup to capture their hostmask
3. Associate the hostmask with their account

#### Bulk User Registration

```irc
!massmeet
```

This will:
1. Scan all channels the bot is in
2. Register all unregistered users
3. Merge duplicate hostmasks
4. Provide statistics on registrations

**Best Practice**: Use `!massmeet` during initial setup, then use `!meet` for individual users.

### Managing Hostmasks

Users may connect from different locations with different hostmasks. Use merge to associate multiple hostmasks:

```irc
!merge Alice_laptop Alice
!merge Alice_phone Alice
```

**View user hostmasks**:
```sql
SELECT u.username, h.hostmask
FROM hostmasks h
JOIN users u ON h.user_id = u.id
WHERE u.username = 'Alice';
```

### Deleting Users

```irc
!deluser BadUser
```

**Warning**: This cascades and deletes:
- User account
- All hostmasks
- All permissions
- Associated data (karma given, quotes, etc.)

**Cannot be undone!** Consider revoking permissions instead:
```irc
!perm remove BadUser op meet join part
```

---

## Permission System

### Permission Hierarchy

1. **owner** - Highest privilege (unrestricted)
2. **admin** - Second-highest (most commands except ownership transfer)
3. **Custom permissions** - Specific command access
4. **user** - Registered user (read-only commands)
5. **public** - Anyone (very limited)

### Common Permissions

| Permission | Description |
|------------|-------------|
| `op` | Can op/deop/voice/kick/ban users |
| `meet` | Can register new users |
| `merge` | Can merge user hostmasks |
| `deluser` | Can delete users |
| `join` | Can make bot join channels |
| `part` | Can make bot leave channels |
| `modules` | Can load/reload/unload modules |
| `exec` | Can execute shell commands (DANGEROUS) |
| `topic` | Can change channel topics |
| `autovoice` | Can manage autovoice settings |
| `autoop` | Can manage auto-op lists |
| `perm` | Can grant/revoke permissions |
| `botnick` | Can change bot's nickname |

### Granting Permissions

#### Global Permissions

```irc
!perm add Alice op meet merge
!perm add Bob join part topic
```

#### Channel-Specific Permissions

```irc
!perm add Alice op #phreaky
!perm add Bob topic #test
```

### Revoking Permissions

```irc
!perm remove Alice op
!perm remove Bob topic #test
```

### Auditing Permissions

```irc
# Who has a specific permission?
!whocan op
!whocan meet #phreaky

# What permissions does a user have?
!whois Alice
```

### Permission Best Practices

1. **Principle of Least Privilege**: Only grant necessary permissions
2. **Use Channel-Specific Permissions**: Restrict sensitive commands to trusted channels
3. **Regular Audits**: Periodically review who has what permissions
4. **Avoid Granting `exec`**: Only give to absolutely trusted users
5. **Document Permission Changes**: Keep a log of permission grants/revokes

### Managing Admins

**Add admin**:
```irc
!admin add Alice
```

**Remove admin**:
```irc
!admin remove Bob
```

**List admins**:
```irc
!admin list
```

**Note**: Only the owner can add/remove admins.

---

## Module Management

### Module Architecture

PhreakBot uses a modular system:

- **Core modules**: Located in `/modules/`
- **Extra modules**: Located in `/phreakbot_core/extra_modules/`
- **Hot-reload**: Modules can be loaded/unloaded without restarting

### Listing Modules

```irc
!avail
```

This shows all currently loaded modules.

### Loading Modules

```irc
!load modules/karma.py
!load modules/custom/mymodule.py
```

**Requirements**:
- Module file must exist
- Module must have valid Python syntax
- Module must follow PhreakBot module structure

### Reloading Modules

After editing a module:

```irc
!reload modules/karma.py
```

This will:
1. Unload the current module
2. Re-read the module file
3. Load the updated module
4. Re-register commands and events

**Use case**: Update module code without bot restart.

### Unloading Modules

```irc
!unload karma
```

**Note**: Use module name, not file path, when unloading.

### Creating Custom Modules

See `/docs/MODULE_DEVELOPMENT_GUIDE.md` for detailed module development instructions.

**Basic module structure**:

```python
"""
Module: example.py
Description: Example module for PhreakBot
"""

def setup(bot):
    """Called when module is loaded"""
    bot.logger.info("Example module loaded")

def command_hello(bot, event):
    """
    !hello - Say hello
    """
    bot.output.append(f"Hello, {event['nick']}!")

# Export commands
COMMANDS = {
    "hello": command_hello
}

# Export events (optional)
EVENTS = {}

# Help text
HELP = """Example Module
Commands:
  !hello - Say hello
"""
```

### Module Troubleshooting

**Module fails to load**:
1. Check syntax: `python3 -m py_compile modules/mymodule.py`
2. Check logs: `tail -f phreakbot.log`
3. Verify module structure (setup function, COMMANDS dict)

**Module doesn't respond to commands**:
1. Verify command is exported in `COMMANDS` dict
2. Check permissions required for command
3. Verify trigger character matches config

---

## Channel Management

### Joining Channels

**Manual**:
```irc
!join #channel-name
```

**Auto-join** (add to config.json):
```json
"channels": ["#phreaky", "#test", "#networking"]
```

**Invited** (automatic if inviter is owner/admin):
```
/invite PhreakBot #private-channel
```

### Leaving Channels

```irc
!part
!part #channel-name
```

### Channel Lockdown

In case of spam attack or security incident:

```irc
!lockdown
```

This will:
1. Set channel to invite-only (+i)
2. Set channel to moderated (+m)
3. Kick all unregistered users

**Unlock**:
```irc
!unlock
```

### Auto-Op Configuration

**Add user to auto-op**:
```irc
!autoop Alice
!autoop Bob #phreaky
```

**Remove from auto-op**:
```irc
!deautoop Alice
```

**List auto-op users**:
```irc
!listautoop
!listautoop #phreaky
```

### Autovoice Configuration

Autovoice automatically gives voice (+v) to registered users:

**Enable**:
```irc
!autovoice on
!autovoice on #phreaky
```

**Disable**:
```irc
!autovoice off
```

**Check status**:
```irc
!autovoice status
```

**Note**: Enabling autovoice also sets channel to moderated (+m).

---

## Security Best Practices

### 1. Access Control

- **Never share owner account**: Only one owner should exist
- **Limit admin count**: 2-3 trusted admins maximum
- **Audit permissions monthly**: Review who has what access
- **Remove inactive users**: Clean up old accounts
- **Use channel-specific permissions**: Don't grant global permissions unnecessarily

### 2. Database Security

- **Strong passwords**: Use complex, unique database password
- **Restrict network access**: Bind PostgreSQL to localhost if bot runs locally
- **Regular backups**: Automated daily backups (see [Backup & Recovery](#backup--recovery))
- **Encrypt backups**: Use GPG to encrypt backup files
- **Update PostgreSQL**: Keep database software up-to-date

### 3. IRC Security

- **Use TLS**: Always enable TLS for IRC connections
- **Verify certificates**: Set `tls_verify: true`
- **NickServ registration**: Register bot's nickname with NickServ
- **Use SASL** (if supported): Configure SASL authentication
- **Monitor logs**: Watch for unauthorized access attempts

### 4. System Security

- **Run as non-root**: Never run bot as root user
- **Use systemd hardening**: Apply security restrictions in service file
- **File permissions**: Restrict config files (chmod 600)
- **Firewall**: Only open necessary ports
- **Keep updated**: Regularly update OS and dependencies

### 5. Rate Limiting (Built-in)

PhreakBot has built-in rate limiting:

- **Per-user**: 10 commands/minute, 5 commands/10 seconds
- **Global**: 20 commands/second
- **Auto-ban**: 5-minute ban for violators

**Monitor bans**:
```python
# In phreakbot shell
print(bot.rate_limit["banned_users"])
```

### 6. Input Sanitization (Built-in)

All user inputs are sanitized for:
- SQL injection
- Shell injection
- Null bytes
- Invalid channel/nickname characters

**See `/docs/SECURITY.md` for detailed security information.**

### 7. Dangerous Commands

**`!exec` permission**:
- ⚠️ **EXTREMELY DANGEROUS**
- Only grant to fully trusted users
- All executions are logged
- Has 10-second timeout
- Output limited to 5 lines

**Recommendation**: Don't grant `exec` permission except in emergency.

---

## Monitoring & Maintenance

### Log Monitoring

**View logs in real-time**:
```bash
# Docker/Podman
docker-compose logs -f
podman-compose logs -f

# Manual installation
tail -f phreakbot.log
```

**Log rotation** (logrotate configuration `/etc/logrotate.d/phreakbot`):
```
/opt/phreakbot/phreakbot.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 phreakbot phreakbot
    postrotate
        systemctl reload phreakbot
    endscript
}
```

### Performance Monitoring

**Monitor bot status**:
```irc
!version
!avail
```

**Database performance**:
```sql
-- Active connections
SELECT count(*) FROM pg_stat_activity
WHERE datname = 'phreakbot';

-- Query performance
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;

-- Cache hit ratio (should be >90%)
SELECT
    sum(heap_blks_read) as heap_read,
    sum(heap_blks_hit) as heap_hit,
    sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) AS ratio
FROM pg_statio_user_tables;
```

**System resources**:
```bash
# CPU and memory usage
docker stats phreakbot

# Disk usage
docker exec phreakbot df -h
```

### Performance Script

PhreakBot includes a monitoring script:

```bash
./scripts/monitor-performance.sh
```

This tracks:
- Response times
- Database query performance
- Memory usage
- Connection stability

**See `/docs/PERFORMANCE_REPORT_v0.1.26.md` for performance optimization details.**

### Health Checks

Create a health check script `/opt/phreakbot/health-check.sh`:

```bash
#!/bin/bash

# Check if bot process is running
if ! pgrep -f "phreakbot.py" > /dev/null; then
    echo "ERROR: PhreakBot process not running"
    systemctl restart phreakbot
    exit 1
fi

# Check database connectivity
if ! psql -U phreakbot -d phreakbot -c "SELECT 1" > /dev/null 2>&1; then
    echo "ERROR: Cannot connect to database"
    exit 1
fi

# Check IRC connectivity (requires netcat)
if ! echo "PING" | nc -w 2 irc.libera.chat 6667 > /dev/null 2>&1; then
    echo "WARNING: Cannot reach IRC server"
fi

echo "OK: All checks passed"
exit 0
```

**Schedule with cron**:
```cron
*/5 * * * * /opt/phreakbot/health-check.sh >> /var/log/phreakbot-health.log 2>&1
```

---

## Troubleshooting

### Bot Won't Connect to IRC

**Symptoms**: Bot starts but doesn't join channels

**Solutions**:
1. Check network connectivity:
   ```bash
   ping irc.libera.chat
   telnet irc.libera.chat 6667
   ```

2. Verify IRC server/port in config:
   ```json
   "server": "irc.libera.chat",
   "port": 6667
   ```

3. Check TLS settings:
   ```json
   "use_tls": true,
   "tls_verify": true
   ```

4. Check firewall:
   ```bash
   sudo ufw allow out 6667/tcp
   sudo ufw allow out 6697/tcp  # For TLS
   ```

5. Review logs:
   ```bash
   tail -100 phreakbot.log | grep -i error
   ```

### Database Connection Failures

**Symptoms**: "Cannot connect to database" errors

**Solutions**:
1. Verify PostgreSQL is running:
   ```bash
   systemctl status postgresql
   docker ps | grep postgres
   ```

2. Test connection manually:
   ```bash
   psql -U phreakbot -h localhost -d phreakbot
   ```

3. Check credentials in config.json:
   ```json
   "db_host": "localhost",
   "db_port": "5432",
   "db_user": "phreakbot",
   "db_password": "correct_password",
   "db_name": "phreakbot"
   ```

4. Verify PostgreSQL accepts connections:
   ```bash
   # Edit pg_hba.conf
   sudo nano /etc/postgresql/14/main/pg_hba.conf

   # Add line:
   host    phreakbot    phreakbot    127.0.0.1/32    md5

   # Restart PostgreSQL
   sudo systemctl restart postgresql
   ```

### Commands Not Working

**Symptoms**: Bot doesn't respond to commands

**Solutions**:
1. Verify trigger character:
   ```irc
   !version  # Check if bot responds
   ```

2. Check if you're registered:
   ```irc
   !whoami
   ```

3. Verify permissions:
   ```irc
   !whoami  # Shows your permissions
   ```

4. Check module is loaded:
   ```irc
   !avail
   ```

5. Enable debug logging:
   ```irc
   !debug on
   ```

### Module Not Loading

**Symptoms**: `!load` fails with error

**Solutions**:
1. Check Python syntax:
   ```bash
   python3 -m py_compile modules/mymodule.py
   ```

2. Verify file path:
   ```bash
   ls -la modules/mymodule.py
   ```

3. Check logs for details:
   ```bash
   tail -50 phreakbot.log
   ```

4. Verify module structure (must have `setup()` function and `COMMANDS` dict)

### High Memory Usage

**Symptoms**: Bot using excessive memory

**Solutions**:
1. Check cache size:
   ```python
   # In bot console
   print(len(bot.cache['user_permissions']))
   print(len(bot.cache['user_info']))
   ```

2. Clear old cache entries:
   ```python
   # Cache cleanup is automatic, but can be forced
   bot.cache['user_permissions'].clear()
   bot.cache['user_info'].clear()
   ```

3. Reduce cache TTL in phreakbot.py:
   ```python
   "cache_ttl": 180,  # Reduce from 300 to 180 seconds
   ```

4. Check for memory leaks in custom modules

5. Restart bot weekly:
   ```cron
   0 3 * * 0 systemctl restart phreakbot
   ```

### Permission Denied Errors

**Symptoms**: "Permission denied" when running commands

**Solutions**:
1. Check if you're registered:
   ```irc
   !whoami
   ```

2. Verify required permission:
   ```irc
   !help <module>  # Shows required permissions
   ```

3. Ask admin to grant permission:
   ```irc
   !perm add YourNick <permission>
   ```

4. Check if you're banned from rate limiting:
   ```python
   # In bot console
   print(bot.rate_limit["banned_users"])
   ```

---

## Backup & Recovery

### Database Backups

#### Automated Daily Backups

Create backup script `/opt/phreakbot/backup-db.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/opt/phreakbot/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/phreakbot_$TIMESTAMP.sql.gz"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Dump database
PGPASSWORD="your_db_password" pg_dump \
    -U phreakbot \
    -h localhost \
    -d phreakbot \
    | gzip > "$BACKUP_FILE"

# Keep only last 30 days
find "$BACKUP_DIR" -name "phreakbot_*.sql.gz" -mtime +30 -delete

# Encrypt backup (optional but recommended)
gpg --encrypt --recipient admin@example.com "$BACKUP_FILE"
rm "$BACKUP_FILE"

echo "Backup completed: ${BACKUP_FILE}.gpg"
```

Make executable and schedule:
```bash
chmod +x /opt/phreakbot/backup-db.sh

# Add to crontab (daily at 2 AM)
crontab -e
0 2 * * * /opt/phreakbot/backup-db.sh >> /var/log/phreakbot-backup.log 2>&1
```

#### Docker/Podman Backups

```bash
# Backup database
docker exec phreakbot-postgres pg_dump -U phreakbot phreakbot | gzip > backup_$(date +%Y%m%d).sql.gz

# Backup volumes
docker run --rm -v phreakbot_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_volume_$(date +%Y%m%d).tar.gz -C /data .
```

### Configuration Backups

```bash
# Backup config and modules
tar czf phreakbot_config_$(date +%Y%m%d).tar.gz \
    config.json \
    modules/ \
    phreakbot_core/extra_modules/

# Encrypt
gpg --encrypt --recipient admin@example.com phreakbot_config_*.tar.gz
```

### Restore from Backup

#### Database Restore

```bash
# Decompress
gunzip phreakbot_20251127.sql.gz

# Decrypt (if encrypted)
gpg --decrypt phreakbot_20251127.sql.gz.gpg > phreakbot_20251127.sql.gz
gunzip phreakbot_20251127.sql.gz

# Restore
psql -U phreakbot -d phreakbot < phreakbot_20251127.sql

# Or for Docker/Podman
cat phreakbot_20251127.sql | docker exec -i phreakbot-postgres psql -U phreakbot -d phreakbot
```

#### Configuration Restore

```bash
# Decrypt
gpg --decrypt phreakbot_config_20251127.tar.gz.gpg > phreakbot_config_20251127.tar.gz

# Extract
tar xzf phreakbot_config_20251127.tar.gz

# Restart bot
systemctl restart phreakbot
```

### Disaster Recovery Plan

1. **Daily**: Automated database backups
2. **Weekly**: Configuration backups
3. **Monthly**: Test restore procedure
4. **Quarterly**: Full system backup (including OS)

**Recovery Time Objective (RTO)**: 1 hour
**Recovery Point Objective (RPO)**: 24 hours

---

## Performance Optimization

### Database Optimization

#### Indexes

PhreakBot v0.1.26+ includes optimized indexes:

```sql
-- Verify indexes exist
SELECT tablename, indexname
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- Add missing indexes if needed
CREATE INDEX IF NOT EXISTS idx_hostmasks_user_id ON hostmasks(user_id);
CREATE INDEX IF NOT EXISTS idx_permissions_user_id ON permissions(user_id);
CREATE INDEX IF NOT EXISTS idx_permissions_channel ON permissions(channel);
CREATE INDEX IF NOT EXISTS idx_karma_channel_item ON karma(channel, item);
```

#### Connection Pooling

PhreakBot v0.1.26+ uses connection pooling for better performance:

```python
# Configuration in phreakbot.py (automatic)
self.db_pool = psycopg2.pool.ThreadedConnectionPool(
    minconn=2,    # Minimum connections
    maxconn=10,   # Maximum connections
    ...
)
```

**Tune pool size** based on load:
- Light load (< 10 users): `minconn=1, maxconn=5`
- Medium load (10-50 users): `minconn=2, maxconn=10` (default)
- Heavy load (50+ users): `minconn=5, maxconn=20`

#### Query Optimization

```sql
-- Enable query statistics (requires pg_stat_statements extension)
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Find slow queries
SELECT
    mean_time,
    calls,
    query
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

### Caching

PhreakBot v0.1.26+ includes intelligent caching:

- **User Permissions**: Cached for 5 minutes
- **User Info**: Cached for 5 minutes
- **Automatic Cleanup**: Expires old cache entries

**Monitor cache**:
```python
# In bot console
print(f"Permissions cached: {len(bot.cache['user_permissions'])}")
print(f"User info cached: {len(bot.cache['user_info'])}")
```

**Adjust cache TTL** (in phreakbot.py):
```python
self.cache = {
    ...
    "cache_ttl": 300,  # Change to 180 for faster expiry, 600 for longer
}
```

### Network Optimization

- **Use TLS**: Reduces packet inspection overhead
- **Local database**: Host database on same server
- **Fast DNS**: Use reliable DNS servers (Google 8.8.8.8, Cloudflare 1.1.1.1)

---

## Deployment Options

### Production Deployment Checklist

- [ ] Use TLS for IRC connections
- [ ] Strong database password (32+ characters)
- [ ] File permissions: `chmod 600 config.json`
- [ ] Regular automated backups
- [ ] Monitoring/alerting configured
- [ ] Firewall configured (only necessary ports open)
- [ ] Log rotation enabled
- [ ] Health checks configured
- [ ] systemd service enabled (auto-start on boot)
- [ ] Documentation reviewed by team

### Docker Deployment

**See main documentation** for Docker deployment details.

**Key advantages**:
- Consistent environment
- Easy updates
- Isolated from host system
- Simplified backup/restore

### Podman Deployment

**See `/docs/PODMAN.md`** for Podman-specific deployment.

**Key advantages**:
- Rootless containers (better security)
- No daemon required
- SELinux support
- Pod management
- Direct systemd integration

### Cloud Deployment

PhreakBot can be deployed on any cloud provider:

**AWS EC2**:
```bash
# Launch t3.small or larger
# Install dependencies
sudo yum install docker git
sudo systemctl start docker
sudo systemctl enable docker

# Clone and deploy
git clone https://github.com/yourusername/phreakbot.git
cd phreakbot
sudo docker-compose up -d
```

**DigitalOcean Droplet**:
```bash
# Use Docker marketplace image or install manually
# Minimum: 1 GB RAM, 1 vCPU
git clone https://github.com/yourusername/phreakbot.git
cd phreakbot
docker-compose up -d
```

**Google Cloud Platform**:
```bash
# Use Compute Engine
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Deploy
git clone https://github.com/yourusername/phreakbot.git
cd phreakbot
docker-compose up -d
```

### Bare Metal Deployment

For maximum performance and control:

1. Install on dedicated server
2. Use systemd for process management
3. Configure PostgreSQL for performance
4. Set up monitoring (Prometheus, Grafana)
5. Configure backups to external storage

---

## Additional Resources

### Documentation

- **Command Reference**: `/docs/COMMAND_REFERENCE.md`
- **Module Development**: `/docs/MODULE_DEVELOPMENT_GUIDE.md`
- **Security Guide**: `/docs/SECURITY.md`
- **Performance Report**: `/docs/PERFORMANCE_REPORT_v0.1.26.md`
- **Roadmap**: `/docs/ROADMAP.md`
- **Changelog**: `/docs/CHANGELOG.md`
- **Podman Guide**: `/docs/PODMAN.md`
- **Migration Guide**: `/docs/MIGRATION_GUIDE.md`

### Community

- **GitHub Repository**: https://github.com/yourusername/phreakbot
- **Issue Tracker**: https://github.com/yourusername/phreakbot/issues
- **IRC Channel**: #phreaky on IRCnet

### Support

For assistance:

1. **Check Documentation**: Review `/docs/` directory
2. **Search Issues**: Look for similar problems in GitHub Issues
3. **Ask in IRC**: Join #phreaky on IRCnet
4. **Create Issue**: Open a GitHub issue with details

---

## Appendix

### Sample systemd Service with Hardening

`/etc/systemd/system/phreakbot.service`:

```ini
[Unit]
Description=PhreakBot IRC Bot
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=phreakbot
Group=phreakbot
WorkingDirectory=/opt/phreakbot
ExecStart=/opt/phreakbot/venv/bin/python3 /opt/phreakbot/phreakbot.py --config /opt/phreakbot/config.json
Restart=always
RestartSec=10

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/phreakbot
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictRealtime=true
RestrictNamespaces=true
LockPersonality=true
MemoryDenyWriteExecute=true
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX
SystemCallFilter=@system-service
SystemCallErrorNumber=EPERM

[Install]
WantedBy=multi-user.target
```

### Database Maintenance Cron Jobs

```cron
# Daily backup at 2 AM
0 2 * * * /opt/phreakbot/backup-db.sh >> /var/log/phreakbot-backup.log 2>&1

# Weekly vacuum at 3 AM Sunday
0 3 * * 0 psql -U phreakbot -d phreakbot -c "VACUUM ANALYZE;" >> /var/log/phreakbot-vacuum.log 2>&1

# Health check every 5 minutes
*/5 * * * * /opt/phreakbot/health-check.sh >> /var/log/phreakbot-health.log 2>&1

# Log rotation (handled by logrotate, but can verify)
0 4 * * * /usr/sbin/logrotate /etc/logrotate.d/phreakbot

# Clean old karma reasons (90 days) - weekly
0 4 * * 1 psql -U phreakbot -d phreakbot -c "DELETE FROM karma_reasons WHERE created_at < NOW() - INTERVAL '90 days';" >> /var/log/phreakbot-cleanup.log 2>&1
```

### Quick Reference Card

**Essential Commands**:
```bash
# Start bot
systemctl start phreakbot
docker-compose up -d

# Stop bot
systemctl stop phreakbot
docker-compose down

# Restart bot
systemctl restart phreakbot
docker-compose restart

# View logs
journalctl -u phreakbot -f
docker-compose logs -f

# Database backup
pg_dump -U phreakbot phreakbot | gzip > backup.sql.gz

# Database restore
gunzip < backup.sql.gz | psql -U phreakbot -d phreakbot
```

**Essential IRC Commands**:
```irc
!whoami                  # Check your identity
!owner claim             # Claim ownership (first time only)
!meet <nick>             # Register user
!perm add <nick> <perm>  # Grant permission
!admin add <nick>        # Add admin
!join #channel           # Join channel
!avail                   # List modules
!version                 # Bot version
```

---

**Document Version**: 1.0
**PhreakBot Version**: 0.1.29
**Last Updated**: 2025-11-27
**Maintainer**: PhreakBot Administration Team

**For emergencies, consult `/docs/TROUBLESHOOTING.md` or join #phreaky on IRCnet.**
