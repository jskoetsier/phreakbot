# PhreakBot Command Reference

**Version**: 0.1.29
**Last Updated**: 2025-11-27

This comprehensive reference documents all PhreakBot commands, their syntax, required permissions, and usage examples.

---

## Table of Contents

1. [Command Syntax](#command-syntax)
2. [Permission Levels](#permission-levels)
3. [User Management](#user-management)
4. [Channel Management](#channel-management)
5. [Information & Lookup](#information--lookup)
6. [Moderation](#moderation)
7. [Channel Mode Management](#channel-mode-management)
8. [Utility & Fun](#utility--fun)
9. [Bot Administration](#bot-administration)
10. [Data Management](#data-management)
11. [Quick Reference](#quick-reference)

---

## Command Syntax

PhreakBot commands follow this general format:

```
!command [required_parameter] [optional_parameter]
```

- **`!`** - Default command trigger (configurable)
- **`command`** - The command name
- **`[required]`** - Required parameters
- **`[optional]`** - Optional parameters
- **`<nickname>`** - User nickname placeholder
- **`<channel>`** - Channel name placeholder

---

## Permission Levels

PhreakBot uses a hierarchical permission system:

| Level | Description | Can Do |
|-------|-------------|--------|
| **owner** | Bot owner (highest privilege) | Everything |
| **admin** | Bot administrators | Most commands except ownership transfer |
| **Custom** | Module-specific permissions | Command-specific actions (e.g., `meet`, `join`, `op`) |
| **user** | Registered users | Read-only and safe commands |
| **public** | Anyone (no registration required) | Public information commands |

**Permission Inheritance**: Higher levels inherit all lower level permissions.

---

## User Management

### Meet (User Registration)

Register a new user in the bot's database and associate their hostmask.

- **Command**: `!meet`
- **Syntax**: `!meet <nickname>`
- **Permission**: owner/admin/meet
- **Examples**:
  ```irc
  !meet Alice
  !meet Bob
  ```
- **Description**: Automatically performs WHO lookup to capture the user's full hostmask (nick!user@host) for authentication. The user must be present in a channel the bot is in.

---

### Mass Meet (Bulk Registration)

Automatically register all unregistered users across all channels.

- **Command**: `!massmeet`
- **Syntax**: `!massmeet`
- **Permission**: owner/admin
- **Examples**:
  ```irc
  !massmeet
  ```
- **Description**: Scans all channels, registers unregistered users, and merges duplicate hostmasks. Provides statistics on successful registrations, merges, and errors.
- **Note**: Useful for initial bot setup or bulk user imports.

---

### Merge (Hostmask Association)

Associate an IRC user's current hostmask with an existing database user.

- **Command**: `!merge`
- **Syntax**: `!merge <irc_nick> <db_username>`
- **Permission**: owner/admin/merge
- **Examples**:
  ```irc
  !merge Alice_work Alice
  !merge Bob bob_mobile
  ```
- **Description**: Allows users with multiple hostmasks (different devices, networks, ISPs) to be recognized as the same person. Preserves all permissions and karma.

---

### Delete User (User Removal)

Remove a user and all associated data from the database.

- **Command**: `!deluser`
- **Syntax**: `!deluser <nickname>`
- **Permission**: owner/admin/deluser
- **Examples**:
  ```irc
  !deluser SpamBot
  !deluser inactive_user
  ```
- **Description**: Cascades deletion to remove hostmasks, permissions, and other user data. **This action cannot be undone.**
- **Warning**: Use with caution. Consider using `!perm remove` to revoke permissions instead.

---

### Who Am I (Identity Check)

Display your current identity and permissions.

- **Command**: `!whoami` or `!test`
- **Syntax**: `!whoami`
- **Permission**: user
- **Examples**:
  ```irc
  !whoami
  !test
  ```
- **Response Example**:
  ```
  You are: Alice!~alice@host.example.com
  Registered as: Alice (owner)
  Permissions: owner, admin, op, meet, join, part
  ```
- **Description**: Shows your IRC nickname, hostmask, registered username, role (owner/admin/user), and global permissions.

---

### Whois (User Information)

Display detailed information about any user in the channel.

- **Command**: `!whois`
- **Syntax**: `!whois <nickname>`
- **Permission**: user
- **Examples**:
  ```irc
  !whois Alice
  !whois Bob
  ```
- **Response Example**:
  ```
  User: Alice!~alice@host.example.com
  Registered: Yes (alice)
  Role: admin
  Global Permissions: admin, op, meet
  Channel Permissions (#phreaky): op, voice
  Hostmasks: 2 registered
  ```
- **Description**: Shows comprehensive user information including all hostmasks, global and channel-specific permissions, and owner/admin status.

---

### User Info (Simplified Whois)

Display basic user information (simpler alternative to whois).

- **Command**: `!userinfo`
- **Syntax**: `!userinfo <nickname>`
- **Permission**: user
- **Examples**:
  ```irc
  !userinfo Alice
  ```
- **Description**: Provides condensed user information, searching across all channels if the user isn't in the current channel.

---

## Channel Management

### Join (Channel Membership)

Make the bot join a channel.

- **Command**: `!join`
- **Syntax**: `!join <channel>`
- **Permission**: owner/admin/join
- **Examples**:
  ```irc
  !join #phreaky
  !join #networking
  ```
- **Auto-feature**: Bot automatically joins when invited by owner/admin users.
- **Description**: Bot will join the specified channel and remain there until told to leave.

---

### Part (Channel Leave)

Make the bot leave a channel.

- **Command**: `!part`
- **Syntax**: `!part [channel]`
- **Permission**: owner/admin/part
- **Examples**:
  ```irc
  !part
  !part #off-topic
  ```
- **Description**: Bot leaves the specified channel. If no channel is provided, leaves the current channel. Uses configurable part message.

---

### Lockdown (Channel Security)

Lock down a channel to prevent unregistered users from participating.

- **Commands**: `!lockdown`, `!unlock`
- **Syntax**:
  - `!lockdown` - Enable lockdown
  - `!unlock` - Disable lockdown
- **Permission**: admin/owner
- **Examples**:
  ```irc
  !lockdown
  !unlock
  ```
- **Description**:
  - **Lockdown**: Sets channel to invite-only (+i) and moderated (+m), then kicks all unregistered users.
  - **Unlock**: Removes invite-only and moderated modes, allowing normal operation.
- **Use Case**: Emergency measure during spam attacks or security incidents.

---

### Topic Management

View and manage channel topics.

- **Commands**: `!topic`, `!settopic`, `!addtopic`
- **Syntax**:
  - `!topic [channel]` - View current topic
  - `!settopic <new_topic>` - Replace entire topic
  - `!addtopic <text>` - Append text to topic
- **Permission**: topic
- **Examples**:
  ```irc
  !topic
  !topic #phreaky
  !settopic Welcome to #phreaky | Be excellent to each other
  !addtopic | Meeting tonight at 20:00 UTC
  ```
- **Description**: Manage channel topics. If no channel is specified, uses current channel.

---

### Autovoice (Automatic Voice Mode)

Automatically voice registered users when they join.

- **Command**: `!autovoice`
- **Syntax**: `!autovoice on|off|status [channel]`
- **Permission**: owner/admin/autovoice
- **Examples**:
  ```irc
  !autovoice on
  !autovoice off
  !autovoice status
  !autovoice on #phreaky
  ```
- **Description**:
  - **on**: Enable autovoice (also sets channel to moderated +m)
  - **off**: Disable autovoice (removes moderated mode +m)
  - **status**: Check current autovoice state
- **Use Case**: Combine with moderated mode to allow only registered users to speak.

---

### Auto-Op (Automatic Operator)

Automatically grant operator status to specific users on join.

- **Commands**: `!autoop`, `!deautoop`, `!listautoop`
- **Syntax**:
  - `!autoop <nickname> [channel]` - Add to auto-op list
  - `!deautoop <nickname> [channel]` - Remove from auto-op list
  - `!listautoop [channel]` - List auto-op users
- **Permission**: owner/admin/autoop
- **Examples**:
  ```irc
  !autoop Alice
  !autoop Bob #phreaky
  !deautoop Charlie
  !listautoop
  !listautoop #phreaky
  ```
- **Description**: Users on the auto-op list receive operator status (+o) automatically when joining the channel. Can be global or channel-specific.

---

## Information & Lookup

### IP Lookup

Look up information about an IP address or hostname.

- **Command**: `!ip`
- **Syntax**: `!ip <hostname|IP_address>`
- **Permission**: user
- **Examples**:
  ```irc
  !ip 8.8.8.8
  !ip google.com
  !ip 2001:4860:4860::8888
  ```
- **Response Includes**:
  - IP type (IPv4/IPv6)
  - Private/Public status
  - Geolocation (country, region, city)
  - ISP/Organization
  - ASN (Autonomous System Number)
- **Description**: Comprehensive IP address information using multiple data sources.

---

### ASN Lookup

Look up Autonomous System Number (ASN) information.

- **Command**: `!asn`
- **Syntax**:
  - `!asn <IP_address>` - Find ASN for an IP
  - `!asn AS<number>` - Look up ASN details
- **Permission**: user
- **Examples**:
  ```irc
  !asn 8.8.8.8
  !asn AS15169
  ```
- **Response Includes**:
  - Organization name
  - Country
  - Registration date
  - Location details
- **Description**: Network operator and routing information for IPs and AS numbers.

---

### MAC Address Lookup

Look up MAC address vendor information.

- **Command**: `!mac`
- **Syntax**: `!mac <address>`
- **Permission**: user
- **Supported Formats**:
  - `00:11:22:33:44:55`
  - `001122334455`
  - `00-11-22-33-44-55`
  - `0011.2233.4455`
- **Examples**:
  ```irc
  !mac 00:11:22:33:44:55
  !mac 001122
  ```
- **Response Includes**:
  - Vendor name
  - Vendor address
  - Block type (MA-L, MA-M, MA-S)
- **Description**: Identifies network equipment manufacturer from MAC address.

---

### Country Lookup

Look up country information for a hostname or IP.

- **Command**: `!country`
- **Syntax**: `!country <hostname|IP>`
- **Permission**: user
- **Examples**:
  ```irc
  !country 8.8.8.8
  !country google.com
  ```
- **Description**: Returns country information based on IP geolocation.
- **Note**: Placeholder implementation in current version.

---

### IRR Explorer (Routing Info)

Check routing information using IRRExplorer.

- **Commands**: `!irr`, `!irrexplorer`, `!roa`
- **Syntax**: `!irr <IP_or_prefix>`
- **Permission**: user
- **Examples**:
  ```irc
  !irr 8.8.8.0/24
  !roa 2001:4860::/32
  ```
- **Response Includes**:
  - ✅ Success (valid routing)
  - ⚠️ Warning (issues found)
  - ❌ Danger (invalid/hijacked)
- **Description**: Validates BGP routing using Internet Routing Registry data and RPKI.

---

### ROA Validation (RPKI)

Check Route Origin Authorization (RPKI) status.

- **Command**: `!rpki-old`
- **Syntax**: `!rpki-old <IP_or_prefix>`
- **Permission**: user
- **Examples**:
  ```irc
  !rpki-old 8.8.8.0/24
  ```
- **Description**: **[DEPRECATED]** Use `!roa` or `!irr` instead for current RPKI validation.

---

### RBL/Blacklist Lookup

Check if a domain or IP is listed in RBLs (Real-time Blackhole Lists).

- **Commands**: `!rbl`, `!blacklist`
- **Syntax**: `!rbl <domain|IP>`
- **Permission**: user
- **Examples**:
  ```irc
  !rbl example.com
  !rbl 192.0.2.1
  !blacklist spammer.net
  ```
- **Checks Against**:
  - Spamhaus (ZEN, DBL)
  - SpamCop
  - SORBS
  - Other major RBLs
- **Description**: Useful for checking email server reputation or identifying spam sources.

---

### Frys-IX Peering Information

Display Frys-IX Internet Exchange member information.

- **Commands**: `!member`, `!frysix`, `!ix`, `!ixmember`, `!members`
- **Syntax**:
  - `!member <ASN>` - Show member info
  - `!frysix` - Show Frys-IX information
  - `!members` - Show member count
- **Permission**: user
- **Examples**:
  ```irc
  !member AS15169
  !frysix
  !members
  ```
- **Response Includes**:
  - Website
  - Join date
  - Peering policy
  - Port speed
  - IPv4/IPv6 addresses
  - Max prefixes
- **Description**: Information about Frys-IX peering exchange members and their technical details.

---

### Tweakers.net News

Fetch latest articles from tweakers.net.

- **Commands**: `!tweakers`, `!tw`
- **Syntax**: `!tweakers`
- **Permission**: user
- **Examples**:
  ```irc
  !tweakers
  !tw
  ```
- **Response**: 5 most recent article titles with URLs
- **Description**: Dutch technology news aggregator. Results cached for 5 minutes to avoid excessive fetching.

---

### URL Fetching & Title Snarfing

#### Manual URL Fetching

- **Commands**: `!url`, `!snarf`, `!at`, `!@`
- **Syntax**: `!url <url>`
- **Permission**: user
- **Examples**:
  ```irc
  !url https://example.com
  !@ https://github.com/phreakbot/phreakbot
  ```
- **Response**: Webpage title and meta description
- **Description**: Extracts Open Graph, Twitter Card, and standard meta tag information.

#### Automatic URL Detection

- **Trigger**: URLs in public messages
- **Examples**:
  ```irc
  <Alice> Check out https://example.com
  <PhreakBot> [URL] Example Domain | Example meta description
  ```
- **Description**: Automatically detects and displays titles for URLs posted in chat. Only processes the first URL per message.
- **Note**: Can be disabled per channel if needed.

---

### Birthday Management

Track and celebrate user birthdays.

- **Commands**: `!bd`, `!bd-set`, `!bd-today`, `!age`
- **Syntax**:
  - `!bd` - List upcoming birthdays (30 days)
  - `!bd <nickname>` - Show user's birthday
  - `!bd-set DD-MM-YYYY` - Set your birthday
  - `!bd-today` - Show today's birthdays
  - `!age` - Show your age
  - `!age <nickname>` - Show someone's age
- **Permission**: user
- **Examples**:
  ```irc
  !bd-set 15-03-1990
  !bd
  !bd Alice
  !age Bob
  ```
- **Features**:
  - Automatic birthday announcements
  - Age calculation in years/weeks/days
  - Upcoming birthday notifications (30-day window)
- **Description**: Birthday tracking with automatic celebration messages.

---

## Moderation

### Kick User

Kick a user from the channel.

- **Command**: `!kick`
- **Syntax**: `!kick <nickname> [reason]`
- **Permission**: owner/admin/op
- **Examples**:
  ```irc
  !kick Spammer
  !kick Troll Stop trolling
  ```
- **Default Reason**: "Kicked by operator"
- **Description**: Removes user from channel. They can rejoin immediately unless banned.
- **Requirement**: Bot must have operator status in channel.

---

### Kick & Ban

Kick and ban a user with optional auto-unban timer.

- **Command**: `!kickban`
- **Syntax**: `!kickban <nickname> [minutes] [reason]`
- **Permission**: owner/admin/op
- **Examples**:
  ```irc
  !kickban Spammer
  !kickban Troll 60 Timeout for trolling
  !kickban BadBot 1440 Spam bot - 24 hour ban
  ```
- **Features**:
  - Generates hostname-based ban mask (*!*@hostname)
  - Optional auto-unban after specified minutes
  - If no minutes specified, ban is permanent until manually removed
- **Description**: Kicks user and sets channel ban. More effective than kick alone.
- **Requirement**: Bot must have operator status in channel.

---

### Unban User

Manually remove a ban from the channel.

- **Command**: `!unban`
- **Syntax**: `!unban <hostmask>`
- **Permission**: owner/admin/op
- **Examples**:
  ```irc
  !unban *!*@spam.example.com
  !unban *!user@host.net
  ```
- **Description**: Removes mode -b for the specified hostmask. Use `/mode #channel +b` to see current bans.
- **Requirement**: Bot must have operator status in channel.

---

## Channel Mode Management

### Operator Mode

Give operator status to a user.

- **Command**: `!op`
- **Syntax**: `!op <nickname>`
- **Permission**: owner/admin/op
- **Examples**:
  ```irc
  !op Alice
  !op Bob
  ```
- **Description**: Grants operator status (+o), allowing the user to manage the channel.
- **Requirement**: Bot must have operator status in channel.

---

### Deoperator Mode

Remove operator status from a user.

- **Command**: `!deop`
- **Syntax**: `!deop <nickname>`
- **Permission**: owner/admin/op
- **Examples**:
  ```irc
  !deop Alice
  !deop Bob
  ```
- **Protection**: Bot will not deop itself.
- **Description**: Removes operator status (-o).
- **Requirement**: Bot must have operator status in channel.

---

### Voice Mode

Give voice to a user (allows speaking in moderated channels).

- **Command**: `!voice`
- **Syntax**: `!voice <nickname>`
- **Permission**: owner/admin/op
- **Examples**:
  ```irc
  !voice Alice
  !voice Guest123
  ```
- **Description**: Grants voice (+v), allowing user to speak in moderated channels (+m).
- **Requirement**: Bot must have operator status in channel.

---

### Devoice Mode

Remove voice from a user.

- **Command**: `!devoice`
- **Syntax**: `!devoice <nickname>`
- **Permission**: owner/admin/op
- **Examples**:
  ```irc
  !devoice Alice
  !devoice Guest123
  ```
- **Description**: Removes voice (-v).
- **Requirement**: Bot must have operator status in channel.

---

## Utility & Fun

### Quotes Management

Store and retrieve memorable quotes from chat.

- **Commands**: `!quote` / `!q`, `!addquote` / `!aq`, `!delquote` / `!dq`, `!searchquote` / `!sq`
- **Syntax**:
  - `!quote [id]` - Show random or specific quote
  - `!addquote <text>` - Add new quote
  - `!delquote <id>` - Delete quote (owner/admin only)
  - `!searchquote <text>` - Search quotes
- **Permission**: user (add/search), owner/admin (delete)
- **Examples**:
  ```irc
  !addquote <Alice> PhreakBot is awesome!
  !quote
  !quote 42
  !searchquote awesome
  !delquote 123
  ```
- **Features**:
  - Per-channel quote storage
  - Duplicate detection
  - Random selection
  - Full-text search
- **Description**: Community quote database for preserving memorable moments.

---

### Karma System

Track reputation of items, people, or topics.

- **Inline Commands**: `!item++`, `!item--`
- **Query Commands**: `!karma`, `!topkarma`
- **Syntax**:
  - `!item++` - Increase karma
  - `!item--` - Decrease karma
  - `!item++ #reason` - With reason
  - `!karma <item>` - Show karma and reasons
  - `!topkarma [limit]` - Show top positive and negative (default 5, max 10)
- **Permission**: user
- **Examples**:
  ```irc
  !google++
  !google++ #amazing search engine
  !google--
  !google-- #too much tracking
  !karma google
  !topkarma
  !topkarma 10
  ```
- **Features**:
  - Prevents self-voting
  - Tracks reasons for karma changes
  - Shows recent karma modifications
  - Per-channel tracking
- **Description**: Community-driven reputation system for anything.

---

### Info Items (Custom Database)

User-created key-value information database.

- **Commands**: `!infoitem`, `!info`, `!forget`
- **Inline Syntax**: `!item = value`, `!item?`
- **Command Syntax**:
  - `!infoitem add <item> <value>` - Add info item
  - `!infoitem del <id>` - Delete by ID
  - `!infoitem list [<item>]` - List items
  - `!item = value` - Shorthand to add
  - `!item?` - Shorthand to query
  - `!forget <item> <value>` - Delete by name and value
- **Permission**: user
- **Examples**:
  ```irc
  !bot = PhreakBot is an IRC bot
  !bot?
  !wiki = https://github.com/phreakbot/phreakbot/wiki
  !infoitem list bot
  !forget bot PhreakBot is an IRC bot
  ```
- **Features**:
  - Per-channel storage
  - Multiple values per item
  - Full-text search
  - Supports URLs, descriptions, facts
- **Description**: Community knowledge base. Great for FAQs, links, and channel information.

---

### Choice/Random Selection

Randomly select from provided options.

- **Commands**: `!choice`, `!choose`
- **Syntax**: `!choice <option1> <option2> <option3>...`
- **Permission**: user
- **Examples**:
  ```irc
  !choice pizza tacos sushi
  !choose red blue green
  !choice "option with spaces" simple third
  ```
- **Description**: Let the bot make a decision for you. Use quotes for options with spaces.

---

## Bot Administration

### Permissions Management

Grant or revoke user permissions.

- **Commands**: `!perm`, `!perms`
- **Syntax**:
  - `!perm add <nick> <perm1> [<perm2>...] [<channel>]`
  - `!perm remove <nick> <perm1> [<perm2>...] [<channel>]`
- **Permission**: owner/admin/perm
- **Examples**:
  ```irc
  !perm add Alice op meet
  !perm add Bob join part #phreaky
  !perm remove Charlie op
  ```
- **Features**:
  - Global or channel-specific permissions
  - Multiple permissions per command
  - Immediate effect (no restart required)
- **Common Permissions**:
  - `op` - Can op/deop/voice/kick/ban
  - `meet` - Can register new users
  - `join` - Can make bot join channels
  - `part` - Can make bot leave channels
  - `modules` - Can load/reload/unload modules
  - `exec` - Can execute shell commands (DANGEROUS)
  - `topic` - Can change channel topics
  - `autovoice` - Can manage autovoice
  - `autoop` - Can manage auto-op lists

---

### Owner & Admin Management

Manage bot ownership and administrator roles.

- **Commands**: `!owner`, `!admin`
- **Syntax**:
  - `!owner` - Show current owner
  - `!owner claim` - Claim ownership (if no owner exists)
  - `!admin list` - List all admins
  - `!admin add <username>` - Add admin (owner only)
  - `!admin remove <username>` - Remove admin (owner only)
- **Permission**: user (show), owner (modify)
- **Examples**:
  ```irc
  !owner
  !owner claim
  !admin list
  !admin add Alice
  !admin remove Bob
  ```
- **Description**:
  - **Owner**: Highest privilege level, can do everything
  - **Admin**: Second-highest level, can manage most aspects except ownership
- **Security**: Owner role can only be claimed if no owner exists. Otherwise, must be transferred via database.

---

### Module Management

Dynamically manage bot modules without restarting.

- **Commands**: `!load`, `!reload`, `!unload`, `!avail`
- **Syntax**:
  - `!avail` - List all loaded modules
  - `!load <module_path>` - Load a module
  - `!reload <module_path>` - Reload a module
  - `!unload <module_name>` - Unload a module
- **Permission**: owner/admin/modules
- **Examples**:
  ```irc
  !avail
  !load modules/karma.py
  !reload modules/infoitems.py
  !unload karma
  ```
- **Features**:
  - Hot-reload capability (update code without bot restart)
  - Dependency checking
  - Error reporting if module fails to load
- **Description**: Manage bot functionality on-the-fly. Useful for testing new modules or updating existing ones.
- **Module Paths**: Use relative path from bot base directory (e.g., `modules/custom.py`).

---

### Bot Nickname

Change the bot's IRC nickname.

- **Command**: `!botnick`
- **Syntax**: `!botnick <new_nickname>`
- **Permission**: owner/admin/botnick
- **Examples**:
  ```irc
  !botnick PhreakBot2
  !botnick PB
  ```
- **Description**: Changes bot's nickname on the IRC network. Nickname must not be in use.
- **Note**: Does not update config file; change is temporary until bot restart.

---

### Shell Command Execution

Execute shell commands on the system running the bot.

- **Command**: `!exec`
- **Syntax**: `!exec <command>`
- **Permission**: owner/admin/exec
- **Examples**:
  ```irc
  !exec uptime
  !exec df -h
  !exec ps aux | grep python
  ```
- **Features**:
  - 10-second timeout per command
  - Output limited to first 5 lines
  - All executions logged
- **Security**:
  - ⚠️ **EXTREMELY DANGEROUS** - Only grant to fully trusted users
  - Can execute ANY system command
  - Has full permissions of the bot process user
  - Sanitization is applied but should still be used with extreme caution
- **Description**: System administration tool. Use for diagnostics, updates, or emergency operations.

---

### Help & Documentation

View module help and command documentation.

- **Commands**: `!help`, `!avail`
- **Syntax**:
  - `!help <module>` - Show help for a module
  - `!avail` - List all available modules
- **Permission**: user
- **Examples**:
  ```irc
  !help karma
  !help infoitems
  !avail
  ```
- **Description**: Built-in help system. Each module can provide its own help text.

---

### Version Information

Display bot version and system information.

- **Command**: `!version`
- **Syntax**: `!version`
- **Permission**: user
- **Examples**:
  ```irc
  !version
  /CTCP PhreakBot VERSION
  ```
- **Response Example**:
  ```
  PhreakBot v0.1.29 - Running on Python 3.11.5
  ```
- **Description**: Also responds to CTCP VERSION requests.

---

### Debug Module

Enable or disable debug logging.

- **Command**: `!debug`
- **Syntax**: `!debug on|off`
- **Permission**: owner/admin
- **Examples**:
  ```irc
  !debug on
  !debug off
  ```
- **Description**: When enabled, logs all IRC events to help troubleshoot issues. Can generate large log files; disable when not needed.

---

## Data Management

### Permission Lookup

List all users with a specific permission.

- **Command**: `!whocan`
- **Syntax**: `!whocan <permission> [channel]`
- **Permission**: user
- **Examples**:
  ```irc
  !whocan op
  !whocan meet #phreaky
  !whocan admin
  ```
- **Description**: Shows global or channel-specific permission grants. Useful for auditing permissions.

---

## Quick Reference

### Information Commands
`!ip`, `!asn`, `!mac`, `!country`, `!irr`, `!rbl`, `!member`, `!whoami`, `!whois`, `!userinfo`, `!bd`, `!age`, `!tweakers`, `!version`

### User Management
`!meet`, `!merge`, `!deluser`, `!massmeet`, `!whoami`, `!whois`, `!userinfo`

### Channel Management
`!join`, `!part`, `!topic`, `!settopic`, `!addtopic`, `!lockdown`, `!unlock`, `!autovoice`, `!autoop`, `!deautoop`, `!listautoop`

### Moderation
`!kick`, `!kickban`, `!unban`, `!op`, `!deop`, `!voice`, `!devoice`

### Fun & Community
`!quote`, `!addquote`, `!searchquote`, `!karma`, `!topkarma`, `!infoitem`, `!choice`, `!url`, `!bd`, `!age`

### Bot Administration
`!perm`, `!owner`, `!admin`, `!avail`, `!load`, `!reload`, `!unload`, `!botnick`, `!exec`, `!debug`, `!help`, `!whocan`

---

## Command Count Summary

- **Total Modules**: 41
- **Total Commands**: 150+ (including aliases)
- **Permission Levels**: 5 (owner, admin, custom, user, public)
- **Event Types Monitored**: join, part, pubmsg, privmsg, CTCP, invite, kick, ban

---

## Tips & Best Practices

### For Users

1. **Register Early**: Use `!whoami` to check if you're registered. If not, ask an admin to `!meet` you.
2. **Check Permissions**: Use `!whoami` to see your current permissions.
3. **Use Aliases**: Many commands have shorter aliases (e.g., `!q` for `!quote`, `!tw` for `!tweakers`).
4. **Read Help**: Use `!help <module>` to learn about specific modules.

### For Admins

1. **Grant Minimal Permissions**: Only give users the permissions they need.
2. **Use Channel-Specific Permissions**: Restrict sensitive commands to specific channels.
3. **Regular Audits**: Use `!whocan` to audit who has specific permissions.
4. **Backup Configuration**: Regularly backup the database.
5. **Monitor Logs**: Check logs for unusual activity.
6. **Be Cautious with !exec**: Only grant exec permission to absolutely trusted users.

### For Developers

1. **Test in Development**: Use `!load` to test new modules without restarting.
2. **Check Module Help**: Provide comprehensive help text in your modules.
3. **Follow Naming Conventions**: Use clear, descriptive command names.
4. **Document Permissions**: Clearly document which permissions your module requires.
5. **Handle Errors Gracefully**: Provide helpful error messages to users.

---

## Troubleshooting

### Common Issues

**Q: Bot doesn't respond to my commands**
- Check if you're using the correct trigger (default: `!`)
- Verify you're registered (`!whoami`)
- Ensure you have the required permissions
- Check if the bot is in the channel

**Q: "Permission denied" error**
- Ask an admin to grant you the required permission using `!perm add`
- Use `!whoami` to check your current permissions

**Q: Module not loading**
- Check module syntax for errors
- Verify module path is correct
- Check bot logs for error messages
- Ensure module dependencies are installed

**Q: Bot can't op/voice users**
- Ensure bot has operator status in the channel
- Check if the target user is in the channel
- Verify you have the `op` permission

---

## Additional Resources

- **Main Documentation**: `/docs/README.md`
- **Module Development**: `/docs/MODULE_DEVELOPMENT_GUIDE.md`
- **Security Guide**: `/docs/SECURITY.md`
- **Roadmap**: `/docs/ROADMAP.md`
- **Changelog**: `/docs/CHANGELOG.md`
- **Deployment**: `/docs/PODMAN.md`

---

## Support

For questions, bug reports, or feature requests:

1. **IRC**: Join #phreaky on IRCnet
2. **GitHub Issues**: https://github.com/yourusername/phreakbot/issues
3. **Documentation**: Check `/docs/` directory

---

**Document Version**: 1.0
**PhreakBot Version**: 0.1.29
**Last Updated**: 2025-11-27
**Maintainer**: PhreakBot Development Team
