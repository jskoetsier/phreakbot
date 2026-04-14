# Changelog

## 0.1.32 (2026-04-14)

### Documentation
- Updated `README.md` — version to v0.1.31, added `.env` configuration instructions, updated Docker setup
- Updated `docs/SECURITY.md` — version to 0.1.31, removed references to removed features (`_validate_sql_safety`, `allow_special_chars`, `dangerous_patterns`), added SSRF protection section, updated defense-in-depth diagram
- Updated `docs/COMMAND_REFERENCE.md` — version to 0.1.31, removed `!exec` command section and references
- Updated `docs/ADMIN_HANDBOOK.md` — version to 0.1.31, replaced `!exec` section with removal note
- Updated `docs/MIGRATION_GUIDE.md` — version to 0.1.31, added migration instructions for v0.1.31
- Updated `tests/README.md` — version to 0.1.31, removed `allow_special_chars` test example

## 0.1.31 (2026-04-14)

### Fixed - Medium Priority Issues

- **Moved `import traceback` to module level in all files**
  - `phreakbot.py`, `lockdown.py`, `meet.py`, `testminus.py`, `frysix.py`, `snarf.py`, `massmeet.py`, `help.py`
  - Previously, `import traceback` was inside `except` blocks (14 occurrences), causing unnecessary re-imports on every error

- **Replaced bare `except:` with `except Exception:`**
  - `phreakbot.py` (DB reconnect), `roa.py`, `asn.py`, `snarf.py`, `urls.py`, `modules.py`
  - Bare `except:` catches `SystemExit` and `KeyboardInterrupt`, preventing clean shutdown

- **Downgraded verbose per-message logging from INFO to DEBUG**
  - ~30+ `logger.info()` calls in `phreakbot.py` that fire on every message/event downgraded to `logger.debug()`
  - Kept INFO for startup, connection, module lifecycle, and significant state changes
  - Prevents log flooding and hostmask/IP information leakage in normal operation

- **Fixed `sys.modules` pollution in module loader**
  - Changed `sys.modules[module_name]` to `sys.modules[f"phreakbot.modules.{module_name}"]`
  - Prevents a module named `os`, `sys`, or `requests` from shadowing Python builtins

- **Added `db_connection.rollback()` to all modules missing it**
  - 10 modules had `commit()` without `rollback()` in error handlers: `testminus.py`, `auto-op.py`, `birthday.py`, `merge.py`, `autovoice.py`, `perm.py`, `deluser.py`, `massmeet.py`, `meet.py`, `quotes.py`
  - Without rollback, a failed DB operation leaves the connection in an error state, causing subsequent queries to fail

- **Removed debug output in production snarf module**
  - Removed `bot.add_response("DEBUG: !@ command processed")` that was visible to IRC users

### Known Limitations
- Module `run()` functions are still synchronous and block the event loop during DB/HTTP operations. Converting to async or using thread executors requires refactoring the shared `self.output` buffer — deferred to a future release.

### Documentation
- Updated all documentation to reflect v0.1.31
- Updated `SECURITY.md` — removed references to `_validate_sql_safety`, `allow_special_chars`, `dangerous_patterns`; added SSRF protection section
- Updated `COMMAND_REFERENCE.md` — removed `!exec` command documentation
- Updated `ADMIN_HANDBOOK.md` — replaced `!exec` section with removal note
- Updated `MIGRATION_GUIDE.md` — added migration instructions for v0.1.31
- Updated `tests/README.md` — removed `allow_special_chars` example
- Updated `README.md` — version, `.env` configuration, Docker setup instructions

## 0.1.30 (2026-04-14)

### Security - Critical Fixes

- **Removed `!exec` module (RCE vulnerability)**
  - Deleted `modules/exec.py` entirely — the module allowed arbitrary shell command execution by owner/admin users, providing a direct remote code execution vector if those accounts were compromised
  - No replacement; shell access should not be exposed through an IRC bot

- **Added SSRF protection to URL-fetching modules**
  - Created `phreakbot_core/url_safety.py` with `is_url_safe()` that blocks requests to private/blocked IP ranges
  - Blocked ranges: RFC 1918 (10/8, 172.16/12, 192.168/16), loopback (127/8), link-local (169.254/16), cloud metadata (169.254.169.254), carrier-grade NAT (100.64/10), IPv6 loopback (::1), IPv6 link-local (fe80::/10), IPv6 ULA (fc00::/7)
  - Applied to `modules/snarf.py` and `modules/urls.py` — attempts to fetch URLs resolving to blocked IPs are rejected with a clear message
  - Uses `netaddr` (already a dependency) for IP range checking and `socket.getaddrinfo` for DNS resolution

- **Simplified `_sanitize_input()` — removed ineffective SQL/shell pattern filtering**
  - Removed `allow_special_chars` parameter and the `dangerous_patterns` regex loop that stripped SQL keywords (`--`, `;DROP`, `;DELETE`, `;UPDATE`) and shell substitution patterns (`$()`, backticks)
  - SQL injection was already prevented by parameterized queries throughout the codebase; the pattern filtering was security theater that could break legitimate input (URLs with `--`, text with semicolons)
  - Shell injection is no longer a concern since the `!exec` module has been removed
  - The sanitizer now only: truncates to max length, removes null bytes, removes non-printable control characters, and strips whitespace
  - Removed `_validate_sql_safety()` method — also redundant with parameterized queries

- **Fixed owner claim race condition**
  - Added partial unique index `idx_users_single_owner` to `dbschema.psql` — database now enforces at most one `is_owner = TRUE` row, preventing concurrent `!owner claim` commands from both succeeding
  - Rewrote `_claim_ownership()` in `modules/owner.py` to use `SELECT ... FOR UPDATE` for row-level locking during the check-then-insert sequence
  - Added `psycopg2.errors.UniqueViolation` handling as a second layer of protection
  - Added `rollback()` calls in all error paths to prevent corrupted transaction state

- **Removed hardcoded credentials from docker-compose.yml**
  - Replaced hardcoded `POSTGRES_USER: phreakbot`, `POSTGRES_PASSWORD: phreakbot` etc. with `${POSTGRES_USER:-phreakbot}` variable references
  - Created `.env.example` with documented defaults and instructions to copy to `.env`
  - Created `.gitignore` to exclude `.env` from version control

### Changed
- `_sanitize_input()` no longer accepts `allow_special_chars` parameter
- `_validate_sql_safety()` method removed from PhreakBot class
- Tests updated to reflect simplified sanitizer (special chars now preserved)
- `_validate_sql_safety` tests removed from test suite

## 0.1.29 (2025-11-27)

### Added - Comprehensive Documentation Suite
- **User Documentation**
  - Complete command reference (`/docs/COMMAND_REFERENCE.md`)
    - 150+ commands documented with syntax, permissions, and examples
    - Organized by category (User Management, Channel Management, Information, Moderation, etc.)
    - Quick reference guide for common commands
    - Permission hierarchy explanation
    - Tips, best practices, and troubleshooting guide
    - Examples for every command

  - Administrator handbook (`/docs/ADMIN_HANDBOOK.md`)
    - Complete installation guide (Docker/Podman and manual)
    - Configuration management and security recommendations
    - Database management and maintenance
    - User and permission management
    - Module management and development
    - Channel management and security
    - Monitoring, maintenance, and health checks
    - Troubleshooting common issues
    - Backup and recovery procedures
    - Performance optimization guide
    - Deployment options (Docker, Podman, cloud, bare metal)
    - Production deployment checklist
    - Security best practices
    - Appendices with sample configs and cron jobs

  - Migration guide (`/docs/MIGRATION_GUIDE.md`)
    - General migration process
    - Version-specific migration instructions (v0.1.24-v0.1.29)
    - Database migration scripts and procedures
    - Configuration change tracking
    - Rollback procedures
    - Troubleshooting migration issues
    - Migration checklist template
    - Best practices for administrators and developers

- **Documentation Structure**
  - All documentation now in `/docs/` directory
  - Cross-referenced between documents
  - Consistent formatting and style
  - Code examples in all guides
  - Version-specific information

### Updated
- **ROADMAP.md**
  - Marked "User Documentation" as completed ✅ (v0.1.29)
  - Removed video tutorials section (not planned)
  - Updated last modified date

- **VERSION**
  - Updated from 0.1.28 to 0.1.29

### Documentation Coverage
- **Command Reference**: 100% command coverage (41 modules, 150+ commands)
- **Admin Handbook**: 14 comprehensive sections covering all aspects of administration
- **Migration Guide**: 6 version migration paths documented

### Benefits
- **For Users**
  - Clear command reference with examples
  - Easy to find help for any command
  - Understand permission requirements
  - Quick troubleshooting

- **For Administrators**
  - Complete installation and setup guide
  - Security best practices
  - Performance optimization strategies
  - Disaster recovery procedures
  - Production deployment checklist

- **For Developers**
  - Clear migration paths between versions
  - Database schema documentation
  - Module development references
  - Contributing guidelines

### Technical Details
- Documentation format: Markdown
- Total pages: 3 major documentation files
- Lines of documentation: 2,000+
- Code examples: 100+
- SQL examples: 50+
- Shell script examples: 75+

### No Code Changes
- This release contains only documentation improvements
- No database migrations required
- No configuration changes needed
- No functional changes to bot behavior
- Fully backward compatible with v0.1.28

### Next Steps
See `/docs/ROADMAP.md` for upcoming features:
- Configuration Management (v0.2.0)
- Monitoring & Metrics (v0.2.0)
- Developer Documentation (future release)

## 0.1.28 (2025-11-27)

### Added - Comprehensive Test Suite
- **Testing Infrastructure**
  - Implemented comprehensive test suite using pytest
  - Added pytest, pytest-cov, pytest-asyncio, pytest-mock, and coverage dependencies
  - Created test directory structure with unit, integration, and fixtures directories
  - Configured pytest with custom markers for test categorization
  - Set up code coverage reporting with HTML, XML, and terminal output
  - Target code coverage: >80%

- **Unit Tests**
  - Core PhreakBot functionality tests (50+ test cases)
  - Input sanitization test suite
    - SQL injection pattern detection
    - Shell injection prevention
    - Null byte and control character removal
    - Channel name and nickname validation
    - Max length enforcement
  - Rate limiting test suite
    - Per-user rate limit enforcement
    - Global rate limit validation
    - Ban creation and automatic expiry
    - Timestamp cleanup verification
  - SQL safety validation tests
    - Parameterized query validation
    - Dangerous pattern detection
    - Query structure verification
  - Permission validation tests
    - Event structure validation
    - Banned user blocking
    - Permission structure type checking
    - Owner privilege testing
  - Caching system tests
    - Cache set/get operations
    - TTL expiry validation
    - Cache invalidation (specific and wildcard)

- **Module System Tests**
  - Module loading tests
    - Valid module loading
    - Invalid configuration handling
    - Syntax error detection
    - Missing config function handling
  - Module unloading tests
    - Successful unload verification
    - Nonexistent module handling
  - Module execution tests
    - Command execution
    - Event handling
    - Permission verification
  - Multiple module management tests
    - Concurrent module loading
    - Selective module unloading

- **Integration Tests**
  - Database connection tests
    - Connection pool creation
    - Connection retry logic
    - Connection validation
  - User information query tests
    - Cache hit/miss scenarios
    - Database query validation
  - SQL query safety tests
    - Parameterized query enforcement

- **Test Fixtures and Helpers**
  - Mock configuration fixture
  - Bot instance fixture with mocked database
  - Mock IRC event fixture
  - Mock database cursor fixture
  - Test module fixture
  - Shared pytest configuration with custom markers

- **Documentation**
  - Comprehensive test README with usage examples
  - Test writing guidelines and best practices
  - Coverage reporting instructions
  - Troubleshooting guide
  - Continuous integration setup examples

### Testing Features
- **Test Markers**: unit, integration, irc, module, slow, requires_db, requires_irc
- **Coverage Reports**: Terminal, HTML, and XML formats
- **Mocking**: Database, IRC, and external dependencies mocked for unit tests
- **Fixtures**: Reusable test fixtures for common test scenarios
- **Configuration**: Pytest.ini and .coveragerc for comprehensive test control

### Test Execution
```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit
pytest -m integration
pytest -m module

# Run with coverage
pytest --cov=. --cov-report=html

# Skip slow/external tests
pytest -m "not slow and not requires_db"
```

### Technical Details
- Test framework: pytest 7.4.3+
- Coverage tool: coverage 7.3.3+
- Async testing: pytest-asyncio 0.23.2+
- Mock framework: pytest-mock 3.12.0+, unittest.mock
- Test isolation: Each test uses fresh fixtures
- Database mocking: psycopg2 connection pool mocked
- IRC mocking: Event objects mocked for testing

## 0.1.27 (2025-11-27)

### Added - Security Hardening
- **Rate Limiting System**
  - Implemented comprehensive rate limiting to prevent command abuse
  - Per-user rate limits: 10 commands per minute, 5 commands per 10 seconds
  - Global rate limit: 20 commands per second across all users
  - Automatic temporary bans for users exceeding rate limits (5 minute ban duration)
  - Automatic unbanning when ban period expires
  - Real-time rate limit tracking with timestamp cleanup
  - User-friendly rate limit exceeded notifications

- **Input Sanitization**
  - Added comprehensive input sanitization for all user inputs
  - Sanitize command arguments (max 500 characters)
  - Sanitize channel names to prevent injection attacks
  - Sanitize nicknames to allow only safe IRC characters
  - Remove null bytes and control characters
  - Filter out dangerous SQL and shell command patterns
  - Prevent command injection attempts

- **SQL Injection Prevention**
  - Audited all SQL queries across codebase
  - Verified parameterized queries used throughout (using %s placeholders)
  - Added SQL safety validation method `_validate_sql_safety()`
  - Detection of dangerous SQL patterns in queries
  - Validation that parameters match placeholders
  - All database operations use safe parameterized queries

- **Enhanced Permission Validation**
  - Added security checks to validate event object structure
  - Verify required fields present before processing
  - Block temporarily banned users from executing commands
  - Enhanced owner detection with multiple validation methods
  - Validate permissions structure in user_info
  - Added detailed permission check logging
  - Protection against malformed permission data

### Security Features
- **Defense in Depth**: Multiple layers of security controls
- **Fail Secure**: Invalid inputs rejected safely
- **Audit Logging**: All security events logged for analysis
- **Rate Limiting**: Prevents abuse and DoS attacks
- **Input Validation**: Blocks injection attacks and malicious inputs
- **Permission Checks**: Enhanced authorization with multiple validations

### Technical Details
- Rate limit tracking uses `collections.defaultdict` for efficient timestamp management
- Banned users tracked with unban timestamps for automatic release
- Input sanitization uses regex patterns to detect and remove dangerous sequences
- SQL safety checks validate query structure before execution
- Permission validation includes type checking and structure validation
- All security checks integrated into existing message handling flow

## 0.1.26 (2025-11-27)

### Added - Performance Optimization
- **Database Indexing**
  - Added comprehensive indexes for frequently queried columns
  - Index on `phreakbot_hostmasks(hostmask)` for fast authentication lookups
  - Index on `phreakbot_hostmasks(users_id)` for user-to-hostmask queries
  - Index on `phreakbot_users(username)` for username lookups
  - Composite indexes on `phreakbot_perms(users_id, channel)` for permission checks
  - Indexes on karma, infoitems, quotes, autoop, and autovoice tables
  - Significant performance improvement for database queries (up to 10x faster on large datasets)

- **Connection Pooling**
  - Implemented `psycopg2.pool.ThreadedConnectionPool` for database connections
  - Pool configured with 5 minimum and 20 maximum connections
  - Automatic connection management and reuse
  - Reduced database connection overhead
  - Better handling of concurrent requests

- **Intelligent Caching System**
  - Added multi-tier caching for user information and permissions
  - Cache user info by hostmask with 5-minute TTL (configurable)
  - Cache timestamps tracked automatically
  - Automatic cache invalidation on expiry
  - Cache hit logging for performance monitoring
  - Significant reduction in database queries (estimated 70-80% reduction)

- **Optimized WHO/WHOIS Lookups**
  - Check cached hostmasks before making WHOIS queries
  - Reduced unnecessary network calls to IRC server
  - Improved message processing speed (up to 50% faster)
  - Better logging for cache hits vs misses

### Improved
- Database query performance through strategic indexing
- Overall bot responsiveness and latency
- Resource utilization (CPU and network bandwidth)
- Scalability for larger user bases and channels
- Debug logging for cache operations

### Technical Details
- All indexes use `IF NOT EXISTS` for safe re-application
- Cache invalidation methods support both specific and wildcard deletion
- Connection pool provides thread-safe database access
- User info cached includes permissions, hostmasks, and all user data
- Hostmask cache populated from JOIN events and first WHOIS lookup
- Performance gains most noticeable in busy channels with many users

## 0.1.25 (2025-11-27)

### Added
- **Enhanced Error Recovery and Resilience**
  - Added database connection retry logic with configurable attempts (default: 3 retries with 5-second delays)
  - Implemented automatic database reconnection with `ensure_db_connection()` method
  - Added connection health checks before all database operations
  - Added 10-second connection timeout to prevent hanging
  - Database operations now gracefully degrade when DB is unavailable
  - Bot continues running with limited functionality when database is down

- **Improved Network Error Handling**
  - Added `on_disconnect()` handler to log disconnections and track expected vs unexpected disconnects
  - Enhanced `on_connect()` with per-channel error handling for join operations
  - Added comprehensive error wrapping in `on_message()` to prevent crashes
  - Better user-facing error messages with exception type information

- **ASN Module Improvements**
  - Switched to reliable ipinfo.io API for IP address lookups
  - Switched to RIPE NCC API for ASN number lookups
  - Added registration date display for ASN lookups
  - Added country of origin for ASN lookups
  - Removed prefix counts, now shows: ASN name, country, and registration date
  - Example output: `ASN Lookup for AS8315: Ziggo B.V. | Country: NL | Registered: 2001-02-14T10:47:32Z`

### Fixed
- **Fixed async/await issues in module execution**
  - Removed incorrect `await` keywords from synchronous module `run()` function calls
  - Modules now execute synchronously as designed (non-async by default)
  - Fixed TypeError: "object NoneType can't be used in 'await' expression"
  - Fixed TypeError: "object bool can't be used in 'await' expression"

- **Fixed massmeet module**
  - Converted from async to synchronous execution
  - Now uses cached hostmasks from `bot.user_hostmasks` instead of WHOIS calls
  - Removed hardcoded test users
  - Added proper channel user enumeration using `bot.channels[channel]["users"]`
  - Better error handling and skipped user tracking
  - Users without cached hostmasks are logged and counted in statistics

- **Fixed channel operations**
  - Added `#frys-ix` channel to remote server configuration
  - Improved channel joining with individual error handling per channel

### Improved
- Enhanced logging throughout error recovery and database operations
- Better error context in log messages (attempt numbers, retry delays, etc.)
- Improved user feedback for command errors
- Database unavailability now logs at appropriate levels (warning vs error)
- Module execution errors now provide exception type to users

### Technical Details
- Database connection pooling happens at bot initialization with retry logic
- `ensure_db_connection()` validates connection before each operation
- Distinguishes between `psycopg2.OperationalError` (connection) and other DB errors
- Module `run()` functions are synchronous by default, not async coroutines
- Massmeet relies on hostmask caching from recent user activity (joins/messages)
- ASN lookups now query multiple APIs for comprehensive information

## 0.1.24 (2025-11-26)

### Added
- **New chanop module** - Channel operator management commands
  - Added `.op <nickname>` command to give operator status (+o)
  - Added `.deop <nickname>` command to remove operator status (-o)
  - Added `.voice <nickname>` command to give voice (+v)
  - Added `.devoice <nickname>` command to remove voice (-v)
  - All commands require owner/admin/op permissions
  - Added validation to check if user is in channel before mode change
  - Added protection to prevent bot from deopping itself

### Fixed
- **Critical: Fixed auto-op and autovoice not working**
  - Removed permission checks for passive events (join, part, quit)
  - Events are now always processed by all listening modules
  - Modules handle their own internal logic and validation
  - Only commands now check permissions, not passive events

- **Fixed IRC mode setting across all modules**
  - Corrected `set_mode()` syntax from `set_mode(channel, "+o nick")` to `set_mode(channel, "+o", nick)`
  - Fixed auto-op module to properly grant operator status on join
  - Fixed autovoice module to properly grant voice and set moderated mode
  - Fixed kickban module to properly set/unset ban modes
  - Fixed chanop module mode commands to work correctly

- **Fixed hostmask capture for user registration**
  - Removed broken WHOIS-based caching approach (WHOIS hangs on IRCnet)
  - Implemented WHO command lookup to fetch real hostmasks on-demand
  - Added WHO support to meet.py, whois.py, and userinfo.py modules
  - Bot now captures real hostmasks like `user!ident@host` instead of placeholders
  - Fixed RuntimeError: dictionary changed during iteration in module reloading

- **Fixed Docker deployment issues**
  - Identified that phreakbot.py is baked into Docker image at build time
  - Updated deployment process to rebuild Docker image when core files change
  - Fixed Python bytecode caching issues by rebuilding containers
  - Modules directory properly mounted as volume for hot-reloading

### Improved
- Enhanced logging throughout hostmask capture and mode setting operations
- Better error handling in WHO command responses
- Improved module event routing with clearer separation of commands vs events
- Added fallback hostmask handling when WHO doesn't return results

### Technical Details
- Pydle's `set_mode()` expects mode and parameters as separate arguments
- WHO command populates pydle's internal `users` cache with real hostmask data
- Event handlers (join/part/quit) should not check permissions - only commands should
- Docker image must be rebuilt when phreakbot.py changes, not just restarted

## 0.1.23 (2025-11-26)
- Reorganized all documentation into `docs/` directory for better project structure
- Moved PODMAN.md, MODULE_DEVELOPMENT_GUIDE.md, and CHANGELOG.md to docs/
- Created comprehensive docs/README.md with documentation index and quick links
- Updated all documentation references in README.md
- Improved documentation discoverability and organization

## 0.1.22 (2025-11-26)
- Added full Podman/podman-compose compatibility
- Updated docker-compose.yml with Podman-specific features:
  - Added SELinux volume labels (`:Z`) for better security
  - Added explicit container names for easier management
  - Added health checks for PostgreSQL
  - Added proper service dependencies with conditions
  - Added explicit network configuration
  - Updated to use `docker.io/` registry prefix for better compatibility
  - Added more environment variables for database initialization
- Created comprehensive PODMAN.md documentation with:
  - Installation instructions for various Linux distributions
  - Usage examples for both podman-compose and podman CLI
  - Troubleshooting guide
  - Systemd integration examples
  - Migration guide from Docker to Podman
- Updated README.md to highlight Docker/Podman support
- Improved container orchestration with explicit dependencies

## 0.1.21 (2025-11-26)
- Updated all dependencies to latest stable versions:
  - irc>=20.5.0 (was 20.0.0)
  - requests>=2.32.3 (was 2.28.0)
  - psycopg2>=2.9.9 (was 2.8.0)
  - iso3166>=2.1.1 (was 2.0.2)
  - pycurl>=7.45.3 (was 7.43.0)
  - beautifulsoup4>=4.13.4 (was 4.9.0)
  - netaddr>=1.3.0 (was 0.8.0)
  - dnspython>=2.7.0 (was 2.2.0)
  - pydle>=1.0.1 (was 1.0.0)
- Improved code quality by removing duplicate karma handling logic
- Consolidated all utility scripts into scripts/ directory for better organization
- Updated Dockerfile and docker-compose.yml to reference new script locations
- Added comprehensive scripts/README.md to document all utility scripts
- Updated main README.md to reference scripts directory

## 0.1.20 (2025-07-15)
- Fixed karma minus pattern handling for all !item-- commands
- Improved command routing for karma patterns
- Enhanced logging for better troubleshooting
- Removed redundant karma modules after consolidation
- Added comprehensive test coverage for karma commands

## 0.1.19 (2025-07-15)
- Consolidate karma functionality into a single module
- Fix karma pattern routing for both ++ and -- patterns
- Improve karma pattern detection and handling
- Add support for reasons with #reason syntax
- Add topkarma command to show items with highest and lowest karma

## 0.1.18 (2025-07-15)
- Add karma module with ++ and -- support
- Fix karma minus pattern detection
- Improved regex pattern matching for karma commands
- Added extensive logging for better troubleshooting
- Fixed command parsing to prevent karma patterns from being misinterpreted as commands
- Added protection against self-karma in all karma modules

## [v0.1.17] - 2025-07-12
- Added karma module with ++ and -- support
- Added support for karma reasons with #reason syntax
- Added !karma command to show karma for specific items
- Added !topkarma command to show items with highest and lowest karma
- Implemented database tracking of who gave karma and why
- Added protection against self-karma

## [v0.1.16] - 2025-07-11
- Consolidated all code to use a single pydle-based implementation
- Removed redundant infoitems modules (infoitems2.py, infoitems3.py, infoitems4.py)
- Removed factoids.py module to eliminate conflicts
- Fixed CTCP VERSION handling to properly use pydle library
- Fixed infoitems module to correctly handle custom commands (!item = value, !item?)
- Removed direct infoitem handling in main bot code to prevent conflicts
- Improved module routing for better command handling
- Updated documentation to reflect the consolidated implementation
- Streamlined codebase by removing duplicate functionality

## [v0.1.15] - 2025-07-10
- Added new pydle-based version of PhreakBot for improved stability and performance
- Created phreakbot_pydle.py as an alternative implementation using the pydle IRC library
- Added infoitems_pydle.py module optimized for the pydle version
- Enhanced custom command handling for infoitems with better pattern matching
- Added extensive debugging and logging for better troubleshooting
- Improved error handling throughout the application
- Updated requirements.txt to include pydle dependency
- Updated documentation to explain the benefits of the pydle version

## [v0.1.14] - 2025-07-10
- Added infoitems module for storing and retrieving information items
- Added support for custom commands with !item = value syntax for adding info
- Added support for !item? syntax for retrieving stored information
- Added infoitem list command to show all available info items
- Added infoitem delete command for admins to remove specific info items
- Enhanced message handling to support custom command patterns
- Improved database integration for storing persistent information

## [v0.1.13] - 2025-07-09
- Added MAC address lookup module for vendor identification
- Added massmeet module for bulk user registration and hostmask merging
- Enhanced Frys-IX module to display port speed, IP, and max prefix information
- Removed location information from Frys-IX module output
- Improved API data extraction in Frys-IX module
- Added detailed logging for better troubleshooting
- Fixed error handling in various modules

## [v0.1.12] - 2025-07-08
- Added Frys-IX module for peering LAN member information
- Added IRRExplorer module for better routing information and ROA validation
- Deprecated old ROA module in favor of IRRExplorer
- Enhanced kickban module to use hostname-based banning
- Added userinfo module as a more reliable alternative to whois
- Simplified lockdown module to use direct channel user lookup
- Fixed whois module to correctly detect users in channels
- Added detailed logging for joins and parts

- Added join/part tracking for better user management

- Added userinfo module as a more reliable alternative to whois
- Added comprehensive join/part tracking for better user management
- Added detailed debugging and error logging throughout the application

## [v0.1.10] - 2025-07-08
- Added kickban module with kick, kickban, and unban commands
- Added auto-unban timer functionality for temporary bans
- Added IRRExplorer module for checking routing information and ROA status
- Enhanced lockdown module to kick unregistered users who joined in the last 5 minutes
- Added join/part tracking for better user management
- Improved hostname-based banning in kickban module
- Added userinfo module as a more reliable alternative to whois
- Added on_namreply event handler to properly track channel users

## [v0.1.9] - 2025-07-15
- Enhanced lockdown module with unlock command to remove lockdown
- Added confirmation before executing lockdown
- Added voice for all registered users during lockdown
- Added delays between operations to ensure proper processing
- Improved error handling and logging in lockdown module
- Added display of current channel modes during lockdown operations

## [v0.1.8] - 2025-07-14
- Added lockdown module for emergency channel security
- Enhanced channel security with comprehensive lockdown features
- Added ability to kick unregistered users during security incidents
- Added automatic operator status for admins and owners during lockdown
- Added channel key setting for additional security during incidents

## [v0.1.7] - 2025-07-13
- Added autovoice module to automatically give voice status to users when they join
- Added IP lookup module with detailed information about IP addresses and hostnames
- Added ASN lookup module for network information
- Updated database schema to include phreakbot_autovoice table
- Improved error handling in network-related modules

## [v0.1.6] - 2025-07-12
- Added birthday module with comprehensive birthday tracking and management
- Added !bd-set command to allow users to set their birthday in DD-MM-YYYY format
- Added !bd command to list upcoming birthdays or show a specific user's birthday
- Added !age command to calculate and display a person's age in years, weeks, and days
- Added automatic birthday congratulations when the bot joins a channel
- Fixed reload command to properly handle module paths
- Fixed parameter naming consistency in the snarf module
- Added comprehensive Module Development Guide with examples

## [v0.1.5] - 2025-07-11
- Added auto-op functionality to automatically give operator status to users
- Fixed database schema to include phreakbot_autoop table
- Enhanced error handling in database operations
- Fixed transaction handling to prevent aborted transactions
- Improved module compatibility with the IRC library

## [v0.1.4] - 2025-07-10
- Fixed meet module to properly handle user registration
- Improved user detection in channels
- Added robust error handling for IRC library interactions
- Fixed snarf module to support direct !@ command for URL descriptions
- Enhanced logging throughout the application for better debugging

## [v0.1.3] - 2025-07-09
- Added snarf module to fetch descriptions from URLs
- Added multiple command aliases (!at, !url, !snarf) for URL description fetching
- Improved error handling in modules
- Fixed compatibility issues between modules

## [v0.1.2] - 2025-07-08
- Renamed all references to wcb to pb in the modules directory
- Removed deploy.py module
- Fixed CTCP version issue to reflect the name Phreakbot + current version
- Synced to git repo with a oneliner
- Added pull and restart functionality for remote server

## [v0.1.1] - 2025-07-07
- Fixed CTCP VERSION reply to show PhreakBot version instead of Python irc.bot

## [v0.1.0] - 2025-07-07
- Initial version with database-based owner system
- Added admin flag for owner
- Added ability to add additional admins
- Code cleanup
- Fixed permission issues in various modules
- Added database persistence
- Improved version module to read from VERSION file
- Updated CTCP VERSION reply to include GitHub URL
- Added detailed logging throughout the application
- Fixed topic module to work with the IRC library
- Added command aliases for quotes module (q, aq, dq, sq)
- Added beautifulsoup4 dependency for URLs module
- Fixed help module to handle errors when displaying module help
- Added version tracking system

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-07-07

### Added
- Database-based owner system replacing hardcoded username in config
- Admin flag for the owner and ability to add additional admins
- Persistent database storage using Docker volumes
- Version tracking system
- Detailed logging for debugging and troubleshooting
- Command aliases for quotes module (q, aq, dq, sq)

### Changed
- Rewrote all modules to follow new module structure
- Moved modules from phreakbot_core/modules to modules directory
- Improved permission system with better checks
- Enhanced help module to handle errors gracefully
- Updated topic module to work with IRC library
- Modified owner claiming process to be more user-friendly
- Improved database initialization to only create schema if needed

### Fixed
- Permission issues in help, quotes, topic, and channel modules
- Hostmask format handling in event processing
- Command routing and permission checking
- Topic setting functionality
- Database persistence between container restarts
- Error handling in various modules
- Owner detection by checking username in addition to hostmask

### Removed
- Old deploy.py module
- Hardcoded owner from config
- Redundant code and unused functions
