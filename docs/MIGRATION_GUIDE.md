# PhreakBot Migration Guide

**Version**: 0.1.29
**Last Updated**: 2025-11-27

This guide provides instructions for upgrading PhreakBot between versions, including database schema changes, configuration updates, and breaking changes.

---

## Table of Contents

1. [General Migration Process](#general-migration-process)
2. [Version-Specific Migrations](#version-specific-migrations)
   - [Migrating to v0.1.29](#migrating-to-v0129)
   - [Migrating to v0.1.28](#migrating-to-v0128)
   - [Migrating to v0.1.27](#migrating-to-v0127)
   - [Migrating to v0.1.26](#migrating-to-v0126)
   - [Migrating to v0.1.25](#migrating-to-v0125)
   - [Migrating to v0.1.24](#migrating-to-v0124)
3. [Database Migration Scripts](#database-migration-scripts)
4. [Configuration Changes](#configuration-changes)
5. [Rollback Procedures](#rollback-procedures)
6. [Troubleshooting](#troubleshooting)

---

## General Migration Process

### Pre-Migration Checklist

- [ ] **Backup database** (see [Backup](#backup))
- [ ] **Backup configuration files** (config.json, modules/)
- [ ] **Read version-specific migration notes** below
- [ ] **Check disk space** (ensure sufficient space for backups and logs)
- [ ] **Schedule maintenance window** (if running in production)
- [ ] **Notify users** of planned downtime
- [ ] **Test in development** environment first

### Standard Migration Procedure

```bash
# 1. Stop the bot
systemctl stop phreakbot
# Or for Docker/Podman
docker-compose down

# 2. Backup database
pg_dump -U phreakbot -d phreakbot | gzip > phreakbot_backup_$(date +%Y%m%d).sql.gz

# 3. Backup config and modules
tar czf phreakbot_files_$(date +%Y%m%d).tar.gz config.json modules/ phreakbot_core/extra_modules/

# 4. Pull latest code
git fetch origin
git checkout v0.1.X  # Replace X with target version

# 5. Update dependencies
pip install -r requirements.txt --upgrade

# 6. Run database migrations (if any)
# See version-specific instructions below

# 7. Update configuration (if needed)
# See version-specific instructions below

# 8. Start the bot
systemctl start phreakbot
# Or for Docker/Podman
docker-compose up -d

# 9. Verify operation
tail -f phreakbot.log
# Or
docker-compose logs -f

# 10. Test core functionality
# Connect to IRC and test commands
```

---

## Version-Specific Migrations

### Migrating to v0.1.29

**Release Date**: 2025-11-27
**Type**: Documentation Release
**Breaking Changes**: None

#### What's New
- Complete command reference documentation
- Administrator handbook
- Migration guide (this document)
- Improved documentation structure

#### Migration Steps

No code or database changes required. Simply update documentation:

```bash
# Pull latest code
git pull origin main

# No database migration needed
# No configuration changes needed

# Restart bot (optional, for version string update)
systemctl restart phreakbot
```

#### Post-Migration
- Review new documentation in `/docs/COMMAND_REFERENCE.md`
- Review administrator handbook in `/docs/ADMIN_HANDBOOK.md`
- Update any internal documentation references

---

### Migrating to v0.1.28

**Release Date**: 2025-11-27
**Type**: Testing Infrastructure Release
**Breaking Changes**: None

#### What's New
- Comprehensive test suite (pytest-based)
- Unit tests for core functionality
- Integration tests for database operations
- Module testing framework
- Code coverage reporting

#### Migration Steps

```bash
# 1. Stop bot (if running)
systemctl stop phreakbot

# 2. Backup (standard procedure)
pg_dump -U phreakbot -d phreakbot | gzip > backup_pre_v0.1.28.sql.gz

# 3. Pull code
git checkout v0.1.28

# 4. Install new test dependencies
pip install -r requirements.txt --upgrade
# New dependencies: pytest, pytest-cov, pytest-asyncio, pytest-mock, coverage

# 5. Start bot (no database changes)
systemctl start phreakbot
```

#### Post-Migration

**Run tests** to verify installation:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Open coverage report
open htmlcov/index.html
```

**No database changes**, **no configuration changes** required.

---

### Migrating to v0.1.27

**Release Date**: 2025-11-27
**Type**: Security Hardening Release
**Breaking Changes**: Rate limiting may affect high-frequency users

#### What's New
- Rate limiting system (per-user and global)
- Input sanitization for all user inputs
- SQL injection prevention audit
- Enhanced permission validation

#### Security Features

**Rate Limits**:
- Per-user: 10 commands/minute, 5 commands/10 seconds
- Global: 20 commands/second
- Auto-ban: 5 minutes for violators

**Input Sanitization**:
- Command arguments (max 500 chars)
- Channel names
- Nicknames
- Null byte and control character removal

#### Migration Steps

```bash
# 1. Stop bot
systemctl stop phreakbot

# 2. Backup
pg_dump -U phreakbot -d phreakbot | gzip > backup_pre_v0.1.27.sql.gz

# 3. Pull code
git checkout v0.1.27

# 4. No new dependencies
pip install -r requirements.txt  # Verify existing deps

# 5. Start bot
systemctl start phreakbot
```

#### Post-Migration

**Monitor rate limiting**:
```python
# In bot console or via debug module
print(bot.rate_limit)
```

**No database changes**, **no configuration changes** required.

#### Impact Assessment

- **Low-frequency users**: No impact
- **High-frequency users**: May hit rate limits (10 cmd/min)
- **Bots/Scripts**: Will be auto-banned if exceeding limits
- **Legitimate automation**: Add longer delays between commands

**Adjust behavior** if needed:
- Reduce command frequency
- Add delays between automated commands
- Use batch commands where possible

---

### Migrating to v0.1.26

**Release Date**: 2025-11-26
**Type**: Performance Optimization Release
**Breaking Changes**: Database schema updates (indexes added)

#### What's New
- Database connection pooling
- Optimized indexes for faster queries
- User permission and info caching (5-minute TTL)
- Reduced WHO/WHOIS lookup frequency
- Performance monitoring scripts

#### Database Changes

**New Indexes** (applied automatically on first run, but can be applied manually):

```sql
-- User lookups
CREATE INDEX IF NOT EXISTS idx_hostmasks_user_id ON hostmasks(user_id);
CREATE INDEX IF NOT EXISTS idx_hostmasks_hostmask ON hostmasks(hostmask);

-- Permission lookups
CREATE INDEX IF NOT EXISTS idx_permissions_user_id ON permissions(user_id);
CREATE INDEX IF NOT EXISTS idx_permissions_channel ON permissions(channel);
CREATE INDEX IF NOT EXISTS idx_permissions_permission ON permissions(permission);

-- Karma lookups
CREATE INDEX IF NOT EXISTS idx_karma_channel ON karma(channel);
CREATE INDEX IF NOT EXISTS idx_karma_item ON karma(item);
CREATE INDEX IF NOT EXISTS idx_karma_channel_item ON karma(channel, item);

-- Quote lookups
CREATE INDEX IF NOT EXISTS idx_quotes_channel ON quotes(channel);

-- Infoitem lookups
CREATE INDEX IF NOT EXISTS idx_infoitems_channel ON infoitems(channel);
CREATE INDEX IF NOT EXISTS idx_infoitems_item ON infoitems(item);

-- Auto-op lookups
CREATE INDEX IF NOT EXISTS idx_autoop_channel ON autoop(channel);
CREATE INDEX IF NOT EXISTS idx_autoop_username ON autoop(username);

-- Autovoice lookups
CREATE INDEX IF NOT EXISTS idx_autovoice_channel ON autovoice(channel);

-- Birthday lookups
CREATE INDEX IF NOT EXISTS idx_birthdays_user_id ON birthdays(user_id);
```

#### Migration Steps

```bash
# 1. Stop bot
systemctl stop phreakbot

# 2. Backup database
pg_dump -U phreakbot -d phreakbot | gzip > backup_pre_v0.1.26.sql.gz

# 3. Pull code
git checkout v0.1.26

# 4. Apply indexes (optional - bot does this automatically)
psql -U phreakbot -d phreakbot < migrations/v0.1.26_indexes.sql

# 5. No new dependencies
pip install -r requirements.txt

# 6. Start bot
systemctl start phreakbot
```

#### Post-Migration

**Verify performance improvements**:

```bash
# Run performance monitoring script
./scripts/monitor-performance.sh
```

**Check query performance**:
```sql
-- Verify indexes exist
SELECT tablename, indexname
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- Check cache hit ratio (should be >90%)
SELECT
    sum(heap_blks_read) as heap_read,
    sum(heap_blks_hit) as heap_hit,
    sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) AS ratio
FROM pg_statio_user_tables;
```

**Expected improvements**:
- 60% faster permission lookups
- 50% faster karma queries
- 40% reduced database queries overall
- Improved response times

**No configuration changes** required.

---

### Migrating to v0.1.25

**Release Date**: 2025-11-25
**Type**: Error Recovery & Reliability Release
**Breaking Changes**: None

#### What's New
- Automatic IRC reconnection on network failures
- Database connection retry logic
- Graceful degradation when services unavailable
- Enhanced error messages for users

#### Migration Steps

```bash
# 1. Stop bot
systemctl stop phreakbot

# 2. Backup
pg_dump -U phreakbot -d phreakbot | gzip > backup_pre_v0.1.25.sql.gz

# 3. Pull code
git checkout v0.1.25

# 4. No new dependencies or database changes
pip install -r requirements.txt

# 5. Start bot
systemctl start phreakbot
```

#### Post-Migration

**Test reconnection logic**:
1. Disconnect network temporarily
2. Bot should auto-reconnect when network restored
3. Check logs for reconnection attempts

**No database changes**, **no configuration changes** required.

---

### Migrating to v0.1.24

**Release Date**: 2025-11-24
**Type**: Feature & Bugfix Release
**Breaking Changes**: Auto-op/autovoice table schema changes

#### What's New
- Fixed auto-op and autovoice functionality
- Implemented WHO command for hostmask capture
- Added channel operator management (op/deop/voice/devoice)
- Fixed IRC mode setting across modules
- Improved Docker deployment

#### Database Changes

**Auto-op table** (if not exists):
```sql
CREATE TABLE IF NOT EXISTS autoop (
    id SERIAL PRIMARY KEY,
    channel VARCHAR(255),
    username VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(channel, username)
);

CREATE INDEX IF NOT EXISTS idx_autoop_channel ON autoop(channel);
CREATE INDEX IF NOT EXISTS idx_autoop_username ON autoop(username);
```

**Autovoice table** (schema update):
```sql
-- Run this if upgrading from pre-v0.1.24
-- See create-autovoice-table.sql for full schema
CREATE TABLE IF NOT EXISTS autovoice (
    id SERIAL PRIMARY KEY,
    channel VARCHAR(255) UNIQUE NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Migration Steps

```bash
# 1. Stop bot
systemctl stop phreakbot

# 2. Backup database
pg_dump -U phreakbot -d phreakbot | gzip > backup_pre_v0.1.24.sql.gz

# 3. Pull code
git checkout v0.1.24

# 4. Apply database migration
psql -U phreakbot -d phreakbot -f create-autovoice-table.sql

# 5. Start bot
systemctl start phreakbot
```

#### Post-Migration

**Verify auto-op**:
```irc
!autoop Alice
!listautoop
```

**Verify autovoice**:
```irc
!autovoice status
!autovoice on
```

**No configuration changes** required.

---

## Database Migration Scripts

### Creating Migration Script

When creating a new version with database changes:

```bash
# 1. Create migration directory
mkdir -p migrations

# 2. Create migration file
cat > migrations/v0.X.Y_description.sql << 'EOF'
-- Migration for v0.X.Y: Description
-- Date: YYYY-MM-DD

BEGIN;

-- Add your SQL statements here
CREATE TABLE IF NOT EXISTS new_table (
    id SERIAL PRIMARY KEY,
    ...
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_name ON table(column);

-- Update existing data if needed
UPDATE existing_table SET column = value WHERE condition;

COMMIT;
EOF
```

### Applying Migration

```bash
# Test migration on backup first
psql -U phreakbot -d phreakbot_test -f migrations/v0.X.Y_description.sql

# Apply to production
psql -U phreakbot -d phreakbot -f migrations/v0.X.Y_description.sql

# Verify
psql -U phreakbot -d phreakbot -c "\dt"  # List tables
psql -U phreakbot -d phreakbot -c "\di"  # List indexes
```

---

## Configuration Changes

### Configuration File Evolution

#### v0.1.24 - v0.1.29 (Current)

No configuration changes between these versions. Configuration schema remains:

```json
{
    "server": "irc.example.net",
    "port": 6667,
    "nickname": "PhreakBot",
    "realname": "PhreakBot IRC Bot",
    "channels": ["#channel1", "#channel2"],
    "trigger": "!",
    "max_output_lines": 3,
    "use_tls": false,
    "tls_verify": true,
    "log_file": "phreakbot.log",
    "db_host": "localhost",
    "db_port": "5432",
    "db_user": "phreakbot",
    "db_password": "password",
    "db_name": "phreakbot"
}
```

### Future Configuration Changes

When configuration changes occur, they will be documented here with:
- Version introducing change
- Old configuration format
- New configuration format
- Migration script (if applicable)
- Default values for new options

---

## Rollback Procedures

### Rolling Back to Previous Version

If migration fails or issues arise:

```bash
# 1. Stop the bot
systemctl stop phreakbot

# 2. Restore database from backup
gunzip < backup_pre_vX.X.X.sql.gz | psql -U phreakbot -d phreakbot

# 3. Checkout previous version
git checkout vX.X.X  # Previous working version

# 4. Restore configuration files (if changed)
tar xzf phreakbot_files_YYYYMMDD.tar.gz

# 5. Downgrade dependencies (if needed)
pip install -r requirements.txt

# 6. Start bot
systemctl start phreakbot

# 7. Verify operation
tail -f phreakbot.log
```

### Rollback Considerations

**Safe to rollback**:
- v0.1.29 → v0.1.28 (documentation only)
- v0.1.28 → v0.1.27 (no database changes)
- v0.1.27 → v0.1.26 (no database changes)

**Requires database restore**:
- v0.1.26 → v0.1.25 (indexes removed, but won't break functionality)
- v0.1.24 → v0.1.23 (auto-op/autovoice tables)

**Not recommended**:
- Rollback >2 versions (e.g., v0.1.28 → v0.1.24)
- Rollback after data has been added to new tables

---

## Troubleshooting

### Common Migration Issues

#### Database Migration Fails

**Error**: Permission denied when creating indexes

**Solution**:
```bash
# Grant necessary permissions
sudo -u postgres psql -d phreakbot -c "GRANT CREATE ON SCHEMA public TO phreakbot;"

# Retry migration
psql -U phreakbot -d phreakbot -f migrations/vX.X.X_migration.sql
```

---

#### Bot Won't Start After Migration

**Error**: ImportError or ModuleNotFoundError

**Solution**:
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Or in virtual environment
source venv/bin/activate
pip install -r requirements.txt --force-reinstall
```

---

#### Database Connection Fails

**Error**: "cannot connect to database"

**Solution**:
```bash
# Verify PostgreSQL is running
systemctl status postgresql

# Test connection manually
psql -U phreakbot -h localhost -d phreakbot

# Check pg_hba.conf
sudo nano /etc/postgresql/14/main/pg_hba.conf
# Ensure line exists:
# host    phreakbot    phreakbot    127.0.0.1/32    md5

# Restart PostgreSQL
sudo systemctl restart postgresql
```

---

#### Module Loading Errors

**Error**: Module "X" failed to load

**Solution**:
```bash
# Check Python syntax
python3 -m py_compile modules/X.py

# Reload specific module
!reload modules/X.py

# Check logs
tail -100 phreakbot.log | grep "module"
```

---

#### Performance Degradation After v0.1.26

**Issue**: Queries slower after index migration

**Solution**:
```sql
-- Analyze tables to update statistics
ANALYZE;

-- Reindex if needed
REINDEX DATABASE phreakbot;

-- Vacuum full (offline, can take time)
VACUUM FULL;
```

---

### Getting Help

If you encounter issues not covered in this guide:

1. **Check logs**: `tail -100 phreakbot.log`
2. **Search GitHub Issues**: https://github.com/yourusername/phreakbot/issues
3. **Join IRC**: #phreaky on IRCnet
4. **Create GitHub Issue**: Provide logs, version, and steps to reproduce

---

## Migration Checklist Template

Use this checklist for each migration:

```
Migration to v0.X.X
Date: YYYY-MM-DD
Performed by: ___________

Pre-Migration:
[ ] Database backup completed
[ ] Configuration backup completed
[ ] Disk space verified (min 2GB free)
[ ] Users notified of maintenance
[ ] Tested in development environment

Migration:
[ ] Bot stopped
[ ] Code updated (git checkout vX.X.X)
[ ] Dependencies updated (pip install -r requirements.txt)
[ ] Database migrations applied
[ ] Configuration updated
[ ] Bot started successfully

Post-Migration:
[ ] Bot connects to IRC
[ ] Commands respond correctly
[ ] Database queries working
[ ] No errors in logs
[ ] Performance acceptable
[ ] Users notified of completion

Rollback Plan (if needed):
[ ] Backup location: ___________
[ ] Estimated rollback time: ___________
[ ] Contact person: ___________
```

---

## Best Practices

### For Administrators

1. **Always backup before migrating** (database + configuration)
2. **Test in development first** (if possible)
3. **Read migration notes carefully** before starting
4. **Schedule migrations during low-traffic periods**
5. **Monitor logs for 24 hours after migration**
6. **Keep backups for at least 30 days**
7. **Document custom changes** separately

### For Developers

1. **Document all database changes** in migration scripts
2. **Provide rollback procedures** for breaking changes
3. **Test migrations on fresh database** before release
4. **Use semantic versioning** (MAJOR.MINOR.PATCH)
5. **Tag releases in Git** for easy checkout
6. **Maintain backward compatibility** when possible

---

## Additional Resources

- **Changelog**: `/docs/CHANGELOG.md` - Detailed version history
- **Roadmap**: `/docs/ROADMAP.md` - Planned features
- **Admin Handbook**: `/docs/ADMIN_HANDBOOK.md` - Administration guide
- **Command Reference**: `/docs/COMMAND_REFERENCE.md` - All commands
- **Security Guide**: `/docs/SECURITY.md` - Security best practices

---

**Document Version**: 1.0
**PhreakBot Version**: 0.1.29
**Last Updated**: 2025-11-27
**Maintainer**: PhreakBot Development Team

**For migration assistance, join #phreaky on IRCnet or create a GitHub issue.**
