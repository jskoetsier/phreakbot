# Changelog

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
