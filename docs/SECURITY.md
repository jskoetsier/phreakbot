# PhreakBot Security Documentation

## Version 0.1.27 - Security Hardening

This document describes the comprehensive security measures implemented in PhreakBot v0.1.27 to protect against abuse, injection attacks, and unauthorized access.

---

## Table of Contents

1. [Security Overview](#security-overview)
2. [Rate Limiting](#rate-limiting)
3. [Input Sanitization](#input-sanitization)
4. [SQL Injection Prevention](#sql-injection-prevention)
5. [Permission Validation](#permission-validation)
6. [Security Configuration](#security-configuration)
7. [Monitoring and Logging](#monitoring-and-logging)
8. [Best Practices](#best-practices)

---

## Security Overview

PhreakBot implements a **defense-in-depth** security strategy with multiple layers of protection:

```
┌─────────────────────────────────────────────────────────┐
│              User Input (IRC Messages)                   │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│  Layer 1: Rate Limiting                                  │
│  - Per-user command limits                               │
│  - Global rate limits                                    │
│  - Automatic temporary bans                              │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│  Layer 2: Input Sanitization                             │
│  - Remove dangerous characters                           │
│  - Truncate to max length                                │
│  - Filter SQL/shell injection patterns                   │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│  Layer 3: Permission Validation                          │
│  - Event object structure validation                     │
│  - Ban status checking                                   │
│  - Database permission verification                      │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│  Layer 4: SQL Safety                                     │
│  - Parameterized queries only                            │
│  - Query pattern validation                              │
│  - Parameter/placeholder matching                        │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│              Command Execution                           │
└─────────────────────────────────────────────────────────┘
```

### Security Principles

- **Fail Secure**: Invalid inputs are rejected safely
- **Least Privilege**: Users only have necessary permissions
- **Audit Logging**: All security events are logged
- **Rate Limiting**: Prevents abuse and DoS attacks
- **Input Validation**: Blocks injection attacks

---

## Rate Limiting

### Overview

Rate limiting prevents command abuse and protects against DoS attacks by restricting the number of commands users can execute within specific time windows.

### Rate Limit Tiers

PhreakBot implements three tiers of rate limiting:

#### 1. Per-User Per-Minute Limit
- **Limit**: 10 commands per user per minute
- **Action**: Temporary ban (5 minutes) if exceeded
- **Purpose**: Prevent individual user abuse

#### 2. Per-User Per-10-Seconds Limit
- **Limit**: 5 commands per user per 10 seconds
- **Action**: Reject command (no ban)
- **Purpose**: Prevent rapid command spamming

#### 3. Global Per-Second Limit
- **Limit**: 20 commands per second across all users
- **Action**: Reject command (no ban)
- **Purpose**: Protect bot from distributed abuse

### Rate Limit Configuration

```python
self.rate_limit = {
    "user_commands": defaultdict(list),
    "max_commands_per_minute": 10,           # Configurable
    "max_commands_per_10_seconds": 5,        # Configurable
    "global_commands": [],
    "max_global_commands_per_second": 20,    # Configurable
    "banned_users": {},
    "ban_duration": 300,                     # 5 minutes, configurable
}
```

### How Rate Limiting Works

1. **Command Received**: User sends a command
2. **Ban Check**: Check if user is currently banned
3. **Timestamp Cleanup**: Remove old timestamps (>1 minute)
4. **Limit Checks**:
   - Check commands in last minute
   - Check commands in last 10 seconds
   - Check global commands in last second
5. **Action**:
   - If limits exceeded: Reject or ban
   - If within limits: Record timestamp and proceed

### Automatic Unbanning

Users are automatically unbanned when their ban period expires:

```python
if current_time < unban_time:
    # Still banned
    return False
else:
    # Unban the user
    del self.rate_limit["banned_users"][hostmask]
    return True
```

### User Notifications

When rate limited, users receive a friendly message:

```
<user>: Rate limit exceeded. Please slow down.
```

Banned users do not receive additional messages to prevent spam.

### Logging

All rate limit events are logged:

```
[WARNING] Rate limit exceeded: user@host has sent 11 commands in the last minute
[WARNING] Rate limit: User user@host is banned for 287 more seconds
[INFO] Rate limit: User user@host has been unbanned
```

---

## Input Sanitization

### Overview

Input sanitization removes or neutralizes potentially dangerous characters and patterns from user input to prevent injection attacks.

### Sanitization Functions

#### 1. General Input Sanitization

```python
def _sanitize_input(self, input_str, max_length=500, allow_special_chars=False):
    """Sanitize user input to prevent injection attacks and abuse"""
```

**Features**:
- Truncates to maximum length (default: 500 chars)
- Removes null bytes (`\x00`)
- Removes non-printable control characters
- Optionally removes dangerous SQL/shell patterns

**Dangerous Patterns Filtered** (when `allow_special_chars=False`):
- `--` - SQL comments
- `; DROP`, `; DELETE`, `; UPDATE` - SQL injection
- `$(` - Shell command substitution
- `` ` `` - Shell command substitution

#### 2. Channel Name Sanitization

```python
def _sanitize_channel_name(self, channel):
    """Sanitize channel name to prevent injection"""
```

**Rules**:
- Must start with `#` or `&`
- Only alphanumeric, hyphen, and underscore allowed
- Maximum length: 50 characters
- Default fallback: `#unknown`

#### 3. Nickname Sanitization

```python
def _sanitize_nickname(self, nickname):
    """Sanitize nickname to prevent injection"""
```

**Allowed Characters**:
- Alphanumeric: `a-z A-Z 0-9`
- IRC special: `- _ [ ] \ ` ^ { } |`
- Maximum length: 30 characters
- Default fallback: `unknown`

### Where Sanitization is Applied

```python
async def _handle_message(self, source, channel, message, is_private):
    # Sanitize all inputs at entry point
    source = self._sanitize_nickname(source)
    channel = self._sanitize_channel_name(channel) if not is_private else source
    message = self._sanitize_input(message, max_length=500, allow_special_chars=True)

    # Later: Sanitize command arguments
    event_obj["command_args"] = self._sanitize_input(
        match.group(2) or "", max_length=500, allow_special_chars=True
    )
```

### Example: Before and After Sanitization

| Input Type | Before | After |
|------------|--------|-------|
| SQL Injection | `'; DROP TABLE users--` | `' TABLE users` |
| Shell Injection | `$(rm -rf /)` | `rm -rf /` |
| Channel Name | `#test';DROP--` | `#testDROP` |
| Nickname | `user$(whoami)` | `userwhoami` |
| Null Bytes | `test\x00admin` | `testadmin` |

---

## SQL Injection Prevention

### Overview

PhreakBot uses **parameterized queries exclusively** to prevent SQL injection attacks. All database operations use placeholders (`%s`) instead of string concatenation.

### SQL Safety Validation

```python
def _validate_sql_safety(self, query, params):
    """Validate that SQL query uses parameterized queries properly"""
```

**Checks**:
1. Ensures parameters match placeholders
2. Detects dangerous patterns in the query itself
3. Validates query structure

**Dangerous Patterns Detected**:
- `' OR '1'='1` - Classic SQL injection
- `'; DROP` - Drop table attacks
- `--` at end of query - SQL comments

### Parameterized Query Examples

#### ✅ CORRECT - Parameterized Query

```python
# Good: Uses %s placeholder
cur.execute(
    "SELECT * FROM phreakbot_users WHERE username = %s",
    (username,)
)

# Good: Multiple parameters
cur.execute(
    "INSERT INTO phreakbot_infoitems (item, value, channel) VALUES (%s, %s, %s)",
    (item, value, channel)
)
```

#### ❌ INCORRECT - String Concatenation

```python
# BAD: Never do this!
cur.execute(f"SELECT * FROM users WHERE username = '{username}'")

# BAD: String formatting
cur.execute("SELECT * FROM users WHERE username = '%s'" % username)
```

### Audited Components

All SQL queries in the following files have been audited and verified to use parameterized queries:

- ✅ `phreakbot.py` - Core bot
- ✅ `modules/karma.py`
- ✅ `modules/quotes.py`
- ✅ `modules/auto-op.py`
- ✅ `modules/autovoice.py`
- ✅ `modules/massmeet.py`
- ✅ `modules/whois.py`

### Database Connection Security

- Uses PostgreSQL connection pooling (psycopg2)
- Connection timeout: 10 seconds
- Automatic reconnection on connection loss
- Thread-safe connection pool (5-20 connections)

---

## Permission Validation

### Overview

Enhanced permission validation ensures only authorized users can execute privileged commands and prevents banned users from executing any commands.

### Validation Layers

#### 1. Event Object Structure Validation

```python
# Ensure all required fields are present
required_fields = ["nick", "hostmask", "channel", "trigger"]
for field in required_fields:
    if field not in event:
        self.logger.error(f"Security: Invalid event object missing field '{field}'")
        return False
```

**Purpose**: Prevent processing of malformed events that could bypass security checks.

#### 2. Ban Status Checking

```python
# Check if user is temporarily banned
if event["hostmask"] in self.rate_limit["banned_users"]:
    self.logger.warning(f"Security: Banned user {event['hostmask']} attempted to execute command")
    return False
```

**Purpose**: Ensure banned users cannot execute commands even if they try to bypass rate limiting.

#### 3. Permission Structure Validation

```python
# Validate permissions structure
if not isinstance(event["user_info"]["permissions"], dict):
    self.logger.error("Security: Invalid permissions structure in user_info")
    return False
```

**Purpose**: Prevent permissions bypass through malformed database data.

#### 4. Database Permission Verification

```python
# Check global permissions
if "global" in event["user_info"]["permissions"]:
    for perm in required_permissions:
        if perm in event["user_info"]["permissions"]["global"]:
            return True

# Check channel-specific permissions
if event["channel"] in event["user_info"]["permissions"]:
    for perm in required_permissions:
        if perm in event["user_info"]["permissions"][event["channel"]]:
            return True
```

**Purpose**: Verify user has required permissions from database.

### Permission Levels

1. **Owner**: Has all permissions globally
2. **Admin**: Configurable permissions per channel or globally
3. **User**: Basic permissions (default for all authenticated users)

### Special Cases

#### Owner Claim Command

```python
# Always allow the owner claim command without permissions
if (event["trigger"] == "command" and
    event["command"] == "owner" and
    event["command_args"] == "claim"):
    return True
```

#### Bot Self-Commands

```python
# Skip permission checks for the bot itself
if event["nick"] == self.nickname:
    return True
```

---

## Security Configuration

### Rate Limit Configuration

To modify rate limits, edit `phreakbot.py`:

```python
self.rate_limit = {
    "max_commands_per_minute": 10,          # Increase for high-traffic bots
    "max_commands_per_10_seconds": 5,       # Decrease for stricter limits
    "max_global_commands_per_second": 20,   # Increase for busy channels
    "ban_duration": 300,                    # Increase for longer bans (seconds)
}
```

### Input Sanitization Configuration

To modify sanitization rules, edit the `_sanitize_input()` method:

```python
# Add more dangerous patterns
dangerous_patterns = [
    r"--",              # SQL comment
    r";\s*DROP",        # SQL drop
    r";\s*DELETE",      # SQL delete
    r";\s*UPDATE",      # SQL update
    r"\$\(",            # Shell substitution
    r"`",               # Shell substitution
    r"<script>",        # XSS (if applicable)
]
```

### Logging Configuration

Security events are logged at appropriate levels:

- **ERROR**: SQL safety violations, invalid events
- **WARNING**: Rate limit exceeded, banned users, connection issues
- **INFO**: Successful unbans, permission grants, cache hits
- **DEBUG**: Cache operations, sanitization details

---

## Monitoring and Logging

### Security Log Examples

#### Rate Limiting
```
[2025-11-27 03:05:12] WARNING - Rate limit exceeded: phreak!~phreak@host has sent 11 commands in the last minute
[2025-11-27 03:05:12] WARNING - Rate limit: User phreak!~phreak@host is banned for 287 more seconds
[2025-11-27 03:10:12] INFO - Rate limit: User phreak!~phreak@host has been unbanned
```

#### Input Sanitization
```
[2025-11-27 03:05:15] DEBUG - Sanitized input: 'test'; DROP TABLE users--' → 'test TABLE users'
[2025-11-27 03:05:16] DEBUG - Sanitized channel: '#test$(rm)' → '#testrm'
```

#### Permission Validation
```
[2025-11-27 03:05:20] WARNING - Security: Banned user user@host attempted to execute command
[2025-11-27 03:05:21] ERROR - Security: Invalid event object missing field 'hostmask'
[2025-11-27 03:05:22] ERROR - Security: Invalid permissions structure in user_info
```

#### SQL Safety
```
[2025-11-27 03:05:25] ERROR - SQL Safety: Query has parameters but no placeholders: SELECT * FROM users
[2025-11-27 03:05:26] ERROR - SQL Safety: Dangerous pattern found in query: '; DROP
```

### Monitoring Commands

Use the performance monitoring script to track security events:

```bash
# Monitor error rates (includes security events)
./scripts/monitor-performance.sh --errors

# View recent logs
podman logs phreakbot | grep -E "WARNING|ERROR" | tail -50

# Monitor rate limiting
podman logs phreakbot | grep "Rate limit" | tail -20

# Monitor SQL safety
podman logs phreakbot | grep "SQL Safety" | tail -20
```

---

## Best Practices

### For Bot Administrators

1. **Monitor Logs Regularly**
   - Check for repeated rate limit violations
   - Investigate SQL safety warnings immediately
   - Monitor permission denied attempts

2. **Configure Rate Limits Appropriately**
   - Higher limits for trusted channels
   - Lower limits for public channels
   - Adjust based on channel activity

3. **Review Permissions**
   - Use least privilege principle
   - Grant channel-specific permissions when possible
   - Regularly audit user permissions

4. **Keep Updated**
   - Update to latest PhreakBot version
   - Review security advisories
   - Apply security patches promptly

### For Module Developers

1. **Always Use Parameterized Queries**
   ```python
   # Good
   cur.execute("SELECT * FROM table WHERE id = %s", (user_id,))

   # Bad
   cur.execute(f"SELECT * FROM table WHERE id = {user_id}")
   ```

2. **Sanitize User Input**
   ```python
   # Use bot's sanitization methods
   item = self._sanitize_input(user_input, max_length=100)
   ```

3. **Check Permissions**
   ```python
   # Let the bot check permissions
   # Don't implement custom permission checks
   ```

4. **Handle Errors Gracefully**
   ```python
   try:
       # Database operations
   except Exception as e:
       self.logger.error(f"Error: {e}")
       bot.add_response("Command failed. Please try again.")
   ```

### For Users

1. **Don't Abuse Commands**
   - Respect rate limits
   - Don't spam commands
   - Use commands responsibly

2. **Report Security Issues**
   - Report suspicious behavior
   - Report unexpected permission grants
   - Contact bot administrator for issues

3. **Understand Permissions**
   - Know what commands you can use
   - Don't attempt to bypass permissions
   - Request permissions if needed

---

## Security Incident Response

### If Rate Limit Abuse Detected

1. **Check Logs**: `podman logs phreakbot | grep "Rate limit"`
2. **Identify User**: Check which hostmask is being banned repeatedly
3. **Take Action**:
   - Temporary: Wait for automatic unban
   - Permanent: Add to channel ban list
   - Moderate: Adjust rate limits if legitimate use case

### If SQL Injection Attempted

1. **Immediate**: Check logs for SQL safety warnings
2. **Investigate**: Identify the source of the attack
3. **Mitigate**: Ensure all queries are parameterized
4. **Report**: Document the attempt
5. **Ban**: Consider permanent ban for malicious actors

### If Permission Bypass Attempted

1. **Verify**: Check permission structure in database
2. **Fix**: Correct any malformed permissions
3. **Audit**: Review permission grants
4. **Monitor**: Watch for repeated attempts

---

## Security Audit Checklist

Use this checklist when auditing PhreakBot security:

- [ ] All SQL queries use parameterized queries
- [ ] Input sanitization applied to all user inputs
- [ ] Rate limiting configured appropriately
- [ ] Permission validation includes all layers
- [ ] Logs monitored for security events
- [ ] No hardcoded credentials in code
- [ ] Database connection uses secure authentication
- [ ] Error messages don't leak sensitive information
- [ ] Module permissions are least-privilege
- [ ] Security patches are up to date

---

## Compliance and Standards

PhreakBot v0.1.27 security features comply with:

- **OWASP Top 10**: Protection against injection, broken authentication, and security misconfiguration
- **CWE-89**: SQL Injection Prevention
- **CWE-79**: Input Validation and Sanitization
- **CWE-307**: Rate Limiting and Brute Force Protection

---

## Reporting Security Vulnerabilities

If you discover a security vulnerability in PhreakBot:

1. **DO NOT** create a public GitHub issue
2. **DO** contact the maintainer privately
3. **DO** provide details:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if available)

---

## Conclusion

PhreakBot v0.1.27 implements comprehensive security hardening with multiple layers of protection. By following the security principles of defense-in-depth, fail-secure design, and comprehensive logging, PhreakBot provides a secure IRC bot platform for both administrators and users.

For additional security resources and updates, see:
- `docs/CHANGELOG.md`
- `docs/ROADMAP.md`
- `docs/README.md`

---

**Document Version**: 1.0
**Last Updated**: 2025-11-27
**PhreakBot Version**: 0.1.27
