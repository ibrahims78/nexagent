# Changelog

## [1.2.0] - 2026-05-17

### Security
- Replace SSH AutoAddPolicy with TOFU (Trust On First Use) host key verification
- Remove shell=True from all subprocess calls; use shlex.split() instead
- Add Command Whitelist Layer (command_whitelist.py) — all commands validated before execution
- Add Path Traversal protection to file_manager.py and word_handler.py
- Block list for dangerous shell commands (format, rm -rf, reg delete, etc.)
- Persist blocked users to security_state.json (survives restarts)
- Add idle session timeout (30 min) alongside absolute timeout
- Fix stream server: require explicit password, no default fallback
- Fix stream server: bind to 127.0.0.1 instead of 0.0.0.0
- Fix HTTP server: bind to 127.0.0.1, add rate limiting (60 req/min), persist token
- Remove Windows password from Telegram args in autologon_enable
- Pass autologon password via subprocess stdin, not CLI args
- Encrypt Fernet key source configurable via NEXAGENT_SECRET_KEY env var
- Key file permissions set to 600 (owner read/write only)

### Bug Fixes
- Fix VisionHandler type mismatch (was receiving Handler object instead of api_key string)
- Fix socket leak in network_monitor.py and pre_login_agent.py (use context manager)
- Fix conversation_context memory leak (OrderedDict + LRU eviction + stale cleanup)
- Fix timezone hardcoded in task_scheduler.py — now reads from config general.timezone

### Improvements
- Add CommandType enum (command_types.py) — eliminate magic strings
- Logger refactored to use Python's built-in module caching
- word_handler.py: all file functions now guarded with is_safe_path()
- requirements.txt: use minimum version bounds instead of exact pins
- Add comprehensive test suite (test_commands.py, test_file_manager.py)
- Remove binary assets from repository (attached_assets/)

## [1.1.0] - 2025-01-01

### Initial Release
- Telegram bot for remote PC control
- AI integration (OpenAI GPT-4o, Google Gemini)
- Screen streaming via MJPEG
- File manager, process manager, system monitor
- Wake-on-LAN support
- AnyDesk integration
- Task scheduler
- Pre-login agent
