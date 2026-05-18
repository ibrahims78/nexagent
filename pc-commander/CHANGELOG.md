# Changelog

## [1.2.2] - 2026-05-18

### Security
- Remove nexagent_config.ini and sshremote_config.ini from git tracking (prevent accidental credential exposure)
- Add Autologon.exe hash logging for future integrity pinning

### Bug Fixes
- Remove accidentally committed pip install log file (=20.7) from repository root
- Fix thread leak in screen stream session cleanup (duplicate threads on stream restart)
- Fix race condition in conversation_context cache (add threading.Lock)
- Fix memory leak in HTTP server rate limiter (add periodic cleanup thread)
- Fix expired PIN entries not being evicted proactively

### Improvements
- Add startup WARNING log when allowed_users is empty
- Move security_auth.py to src/security/auth.py for cleaner module layout
- CI: pre-install pyaudio via pipwin to prevent fragile wheel resolution
- Config directory now cross-platform (Linux/macOS via NEXAGENT_CONFIG_DIR env var)

## [1.2.1] - 2026-05-17

### Bug Fixes
- Add SpeechRecognition>=3.10.0 and pyaudio to requirements.txt (was causing ModuleNotFoundError on voice input)
- Sync APP_VERSION to 1.2.0 in settings_window.py and setup.iss
- Replace deprecated asyncio.new_event_loop() with asyncio.run() in watchdog.py, task_scheduler.py, network_monitor.py, wol_notifier.py, telegram_bot.py, and main_service.py
- Fix BLOCKED_CMD_PREFIXES to use regex word boundaries (prevents false positives like blocking "reformat" or "rmdir" in filenames)
- Untrack attached_assets/ from git index
- Add wol_config.json, sshremote_key.pub, and pre_login_config.json to .gitignore (both root and pc-commander)

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
