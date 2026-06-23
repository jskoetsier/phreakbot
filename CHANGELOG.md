# Changelog

## [0.1.39] - 2026-06-23

### Security
- **SSRF via redirect**: Added `safe_get()` helper in `url_safety.py` that re-checks SSRF rules on every redirect hop. `snarf.py` and `urls.py` now use it instead of calling `requests.get` directly with `allow_redirects=True`.
- **Rate-limit DoS via WHOIS fallback**: Fallback hostmask (`nick!unknown@unknown`) is now cached so WHOIS is not retried on every message, preventing an attacker from exhausting another user's rate-limit bucket via forced WHOIS failures.
- **Permission allowlist**: `perm.py` now validates permission names against a fixed allowlist (`VALID_PERMISSIONS`) and rejects unknown values at write time.
- **Exception disclosure**: Raw exception strings (`str(e)`) are no longer sent to IRC in `snarf.py`, `asn.py`, `infoitems.py`, and `ip.py`. Full exceptions are logged server-side; a generic message is returned to the channel.
- **Internal DNS oracle**: `ip.py` now filters resolved addresses through `BLOCKED_NETWORKS` from `url_safety.py` before reporting, preventing enumeration of private/internal hosts.
- **Default DB password**: `config.json.pydle.example` no longer ships with a default password; `config.py` exits on startup if `db_password` is empty; Docker Compose uses `${POSTGRES_PASSWORD:?...}` to fail loudly if the variable is unset.
- **Cleartext HTTP**: `ip.py` now uses HTTPS for the ip-api.com geolocation endpoint.
- **TLS defaults**: Example config and Docker Compose now default to port 6697 with `use_tls: true`.
- **Backup file**: Removed `modules/infoitems.py.bak`; added `*.bak` to `.gitignore`.

## [0.1.38] - 2026-06-23

### Fixed
- `fix(channel)`: persist `!join` and `!part` across restarts

## [0.1.37] - 2026-06-23

### Fixed
- `fix(permissions)`: require registration for `user` permission
- `fix(urls)`: skip URL title fetch for unregistered users
- `fix`: reconnect to IRC on netsplit or server outage
- `fix`: validate channel prefix in auto-op and autovoice commands
