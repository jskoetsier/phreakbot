# Changelog

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
