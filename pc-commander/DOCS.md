# NexAgent — Complete Documentation

**Version:** 1.1.0  
**Updated:** 2026

---

## 1. PROJECT OVERVIEW

NexAgent is a Telegram bot that lets you control a Windows PC through natural Arabic (or English) language commands. It uses an AI provider (OpenAI GPT-4o or Google Gemini) to interpret free-form messages and map them to concrete system actions: taking screenshots, opening applications, managing files, monitoring hardware, and more.

**Key design goals:**
- Single authorised user (or a small whitelist) controls one Windows machine.
- Minimal setup — one config file, one executable.
- Layered security: whitelist → block list → rate limit → PIN → session token.
- Resilient: a Watchdog thread restarts the bot automatically if it crashes.

---

## 2. DIRECTORY STRUCTURE

```
pc-commander/
├── main.py                      Entry point (GUI + tray icon)
├── requirements.txt             Python dependencies
├── build.bat                    Build & package script
├── create_icon.py               Generates assets/icon.ico
├── VERSION                      Monotonic build counter
├── DOCS.md                      This file
├── INSTALL_AR.txt               Arabic installation guide
├── INSTALL_EN.txt               English installation guide
├── LICENSE.txt
│
├── installer/
│   └── setup.iss                Inno Setup script (GUI installer)
│
├── scripts/
│   └── bump_version.py          Increments VERSION
│
├── src/
│   ├── main_service.py          Service orchestrator (starts all subsystems)
│   │
│   ├── ai/
│   │   ├── openai_handler.py    GPT-4o integration
│   │   ├── gemini_handler.py    Gemini 1.5 Flash integration
│   │   └── vision_handler.py   GPT-4o Vision (screen analysis)
│   │
│   ├── bot/
│   │   ├── telegram_bot.py      PCCommanderBot class + all handlers
│   │   └── commands.py          Command dispatcher (execute_command)
│   │
│   ├── gui/
│   │   ├── settings_window.py   CustomTkinter settings UI
│   │   └── tray_icon.py         System-tray icon (pystray)
│   │
│   ├── pc_control/
│   │   ├── screenshot.py        Screen capture
│   │   ├── process_manager.py   Open/close apps, shutdown, volume
│   │   ├── file_manager.py      List/delete/open/search files
│   │   ├── system_monitor.py    CPU/RAM/disk/temp metrics
│   │   ├── smart_executor.py    Multi-step AI-vision executor
│   │   ├── visual_control.py    Mouse/keyboard automation
│   │   ├── word_handler.py      Read/write Word documents
│   │   ├── anydesk.py           AnyDesk control
│   │   ├── wake_on_lan.py       WoL magic packet
│   │   └── autologon.py         Windows auto-login registry
│   │
│   ├── scheduler/
│   │   └── task_scheduler.py    Daily report scheduler (APScheduler)
│   │
│   ├── security/
│   │   └── __init__.py
│   │
│   ├── server/
│   │   └── http_server.py       Flask local HTTP server (port 5000)
│   │
│   ├── streaming/
│   │   └── screen_stream.py     WebSocket screen streaming
│   │
│   ├── tunnel/
│   │   ├── cloudflare_handler.py Cloudflare Tunnel
│   │   └── ngrok_handler.py     ngrok tunnel
│   │
│   └── utils/
│       ├── config.py            Config load/save with Fernet encryption
│       ├── logger.py            Rotating file logger
│       ├── security_auth.py     Whitelist, PIN, session, rate-limit
│       ├── watchdog.py          Bot/internet health monitor
│       ├── network_monitor.py   Proactive network checks
│       ├── startup.py           Windows startup registration
│       └── wol_notifier.py      WoL Telegram notification helper
│
├── tests/
│   ├── test_config.py
│   ├── test_security_auth.py
│   ├── test_watchdog.py
│   └── test_commands.py
│
└── pre_login/
    ├── pre_login_agent.py       Runs before Windows login (SYSTEM task)
    ├── install_pre_login.bat
    └── uninstall_pre_login.bat
```

---

## 3. CONFIGURATION REFERENCE

Config file location: `%APPDATA%\PCCommander\config.json`  
Sensitive fields are Fernet-encrypted at rest (key stored in `secret.key`).

| Section | Key | Type | Default | Description |
|---------|-----|------|---------|-------------|
| telegram | bot_token | str | "" | BotFather token (encrypted) |
| telegram | allowed_users | list[int] | [] | Telegram user IDs allowed to use the bot |
| ai | provider | str | "openai" | "openai" or "gemini" |
| ai | openai_key | str | "" | OpenAI API key (encrypted) |
| ai | gemini_key | str | "" | Google Gemini API key (encrypted) |
| ai | model_openai | str | "gpt-4o" | OpenAI model name |
| ai | model_gemini | str | "gemini-1.5-flash" | Gemini model name |
| tunnel | provider | str | "cloudflare" | "cloudflare" or "ngrok" |
| tunnel | ngrok_token | str | "" | ngrok auth token (encrypted) |
| general | language | str | "ar" | UI language |
| general | start_with_windows | bool | false | Register in Windows startup |
| general | do_not_disturb | bool | false | Suppress command execution |
| general | daily_report_time | str | "08:00" | HH:MM for scheduled report |
| monitoring | cpu_alert_threshold | int | 90 | CPU % alert level |
| monitoring | ram_alert_threshold | int | 90 | RAM % alert level |
| monitoring | temp_alert_threshold | int | 80 | CPU °C alert level |
| monitoring | disk_alert_threshold | int | 90 | Disk % alert level |
| anydesk | path | str | "C:\\...\\AnyDesk.exe" | Path to AnyDesk executable |
| wol | mac_address | str | "" | Target PC MAC address |
| wol | broadcast_ip | str | "255.255.255.255" | WoL broadcast address |
| wol | pc_ip | str | "" | Target PC local IP (for status check) |
| security | require_pin | bool | false | Enforce PIN before each session |
| security | session_pin | str | "" | PIN value (encrypted) |
| security | watchdog_enabled | bool | true | Enable bot watchdog |
| security | log_commands | bool | true | Write command log to disk |
| stream | enabled | bool | false | Enable WebSocket screen streaming |
| stream | port | int | 8765 | Streaming port |
| stream | password | str | "pccommander" | Stream password (encrypted) |

---

## 4. BOT COMMANDS REFERENCE

| Command (internal) | Description | Example Arabic trigger |
|--------------------|-------------|------------------------|
| screenshot | Capture current screen | خذ لقطة شاشة |
| open_app [name] | Launch an application | افتح المتصفح |
| close_app [name] | Kill a process | أغلق الوورد |
| list_processes | Show running processes | البرامج النشطة |
| run_cmd [cmd] | Execute a shell command | نفّذ ipconfig |
| shutdown [min] | Shut down PC | أغلق الحاسب بعد 10 دقائق |
| restart [min] | Restart PC | أعد التشغيل |
| cancel_shutdown | Cancel pending shutdown | ألغِ الإغلاق |
| lock | Lock the screen | اقفل الشاشة |
| volume [0-100] | Set system volume | اجعل الصوت 50 |
| list_files [path] | Browse directory | اعرض ملفات المستندات |
| delete_file [path] | Delete a file | احذف ملف كذا |
| open_file [path] | Open a file | افتح ملف كذا |
| search_files [dir] [pattern] | Search files | ابحث عن ملفات pdf |
| read_word [path] | Read Word document | اقرأ ملف التقرير |
| edit_word [path] [text] | Append text to Word | أضف نصاً للتقرير |
| create_word [path] [title] [body] | Create Word file | أنشئ ملف وورد |
| system_status | CPU/RAM/disk summary | حالة الحاسب |
| daily_report | Full system report | تقرير يومي |
| anydesk_start | Launch AnyDesk | شغّل AnyDesk |
| anydesk_stop | Stop AnyDesk | أوقف AnyDesk |
| anydesk_id | Get AnyDesk ID | رقم AnyDesk |
| wol_start | Send WoL magic packet | شغّل الحاسب |
| wol_status | Check if PC is online | هل الحاسب يعمل؟ |
| vision_do [cmd] | AI vision + action | اضغط على زر الموافقة |
| vision_describe | Describe current screen | صف لي الشاشة |
| vision_find_click [el] | Find element and click | انقر على أيقونة الإعدادات |
| vision_task [task] | Multi-step AI task | افتح المتصفح واذهب لـ google.com |
| security_report | Show security summary | تقرير الأمان |
| security_block [id] | Block a user | احجب 123456 |
| security_unblock [id] | Unblock a user | ارفع الحجب عن 123456 |
| logout | Invalidate session | تسجيل خروج |
| watchdog_status | Watchdog health | حالة الـ watchdog |
| stream_start | Start screen streaming | ابدأ البث |
| stream_stop | Stop streaming | أوقف البث |
| stream_status | Streaming info | حالة البث |

---

## 5. SECURITY MODEL

Security is enforced in layers; every inbound message passes all gates in order:

```
Message received
      │
      ▼
[1] Is user in allowed_users?   ── NO ──► send "غير مصرح" + notify admins
      │ YES
      ▼
[2] Is user blocked?            ── YES ──► send "تم حجبك"
      │ NO
      ▼
[3] Rate limit exceeded?        ── YES ──► send "انتظر دقيقة"
      │ NO
      ▼
[4] require_pin enabled?
      │ YES
      ▼
[4a] Active session?            ── NO ──► request PIN, start 2-min timer
      │ YES
      ▼
[5] Execute command
```

**PIN flow:** User sends PIN → hashed with SHA-256 → compared to stored hash.  
Wrong PIN 3 times → user auto-blocked.  
Session expires after 1 hour of inactivity (configurable via SESSION_TIMEOUT).  
Rate limit: 30 messages per 60-second window.

**Encryption at rest:** Sensitive config fields (bot_token, API keys, PIN, stream password)  
are encrypted with Fernet (AES-128-CBC + HMAC-SHA256) before saving to disk.  
The key lives in `%APPDATA%\PCCommander\secret.key` (never committed to git).

---

## 6. ARCHITECTURE

### Startup sequence

```
main.py
  └── PCCommanderService.start()
        ├── _start_server()       → Flask HTTP server (port 5000)
        ├── _start_tunnel()       → Cloudflare or ngrok
        ├── _start_ai()           → OpenAIHandler or GeminiHandler
        ├── _wire_vision_handler()→ inject VisionHandler into commands module
        ├── _start_bot()          → PCCommanderBot (runs in daemon thread)
        ├── _start_scheduler()    → APScheduler (daily report)
        └── _start_network_monitor()
```

### Message flow

```
User (Telegram)
      │  text / voice / document
      ▼
PCCommanderBot.handle_*()
      │  _check_auth_and_session()
      ▼
_process_text()
      │  ai_handler.process_command(text, context)
      ▼
execute_command(command, args, config)          ← commands.py dispatcher
      │
      ├── LocalExecutor (screenshot, processes, files …)
      └── SmartExecutor (vision_do, vision_task …)
                │
                └── VisionHandler → OpenAI GPT-4o Vision
```

---

## 7. ADDING A NEW COMMAND

**Step 1 — Add a handler function** in the appropriate `src/pc_control/*.py` module.

**Step 2 — Register it** in `src/bot/commands.py` inside `execute_command()`:
```python
elif command == "my_new_command":
    result_text = my_module.my_function(args)
```

**Step 3 — Teach the AI** about it by adding a line to `SYSTEM_PROMPT_AR` in  
`src/ai/openai_handler.py` and `src/ai/gemini_handler.py`:
```
- my_new_command [param]: وصف الأمر
```

**Step 4 — Write a test** in `tests/test_commands.py`:
```python
def test_my_new_command():
    with patch("src.pc_control.my_module.my_function", return_value="✅ done"):
        text, file = cmd_mod.execute_command("my_new_command", ["arg"], SAMPLE_CONFIG)
    assert "✅" in text
```

---

## 8. BUILD & DISTRIBUTION

```bat
:: From pc-commander\ directory:
build.bat
```

The script:
1. Installs all `requirements.txt` dependencies via pip.
2. Generates `assets/icon.ico` using `create_icon.py`.
3. Runs PyInstaller → produces `dist\PCCommander\PCCommander.exe`.
4. (Optional) Compiles `installer\setup.iss` with Inno Setup → `dist\installer\NexAgent_V{N}.zip`.
5. Increments `VERSION` on success.

To bump the version manually:
```
python scripts/bump_version.py
```

---

## 9. KNOWN LIMITATIONS

- **Windows only.** The bot relies on `pywin32`, `pystray`, `pycaw`, and Windows-specific APIs. It will not run on Linux or macOS.
- **Voice transcription with Gemini** uses `speech_recognition` + Google Web Speech API (requires internet). For offline transcription, use OpenAI Whisper via the OpenAI provider.
- **AnyDesk auto-accept** is not yet implemented; the path must point to a pre-configured AnyDesk installation.
- **Screen streaming** is LAN-only unless a tunnel is active.
- **Wake-on-LAN** requires the target machine to support WoL and the router to allow directed broadcasts.
- **vision_* commands** require OpenAI GPT-4o and will not work with Gemini.

---

## 10. CHANGELOG

### V1.1.0 — NexAgent (2026)
- Renamed user-facing product name from "PC Commander" to "NexAgent".
- **FIX-1:** Activated Fernet encryption for bot_token, API keys, PIN, stream password in config.py.
- **FIX-2:** Unified authorization: all 5 Telegram handlers now use `_check_auth_and_session()`, enforcing PIN everywhere.
- **FIX-3:** Wired shared `VisionHandler` into `commands.py` via `set_vision_handler()` in `main_service.py`; vision commands no longer instantiate a new handler per call.
- **FIX-4:** Watchdog `_restart()` now calls `self.stop()` + `time.sleep(2)` + `self.start()` instead of a no-op lambda.
- **FIX-5:** Fixed socket leak in `watchdog._is_internet_available()` — now uses `with socket.socket(...) as s`.
- **FIX-6:** Fixed `asyncio.run()` in `bot.stop()` — replaced with event-loop-aware call using `loop.call_soon_threadsafe`.
- **FIX-7:** Deleted dead `src/security/auth.py` (conflicted with `security_auth.py`).
- **FIX-8:** Updated Gemini model from deprecated `gemini-pro` to `gemini-1.5-flash` in config, GeminiHandler, and `_start_ai()`.
- **FIX-9:** Refactored `handle_voice` to call shared `_process_text()` instead of mutating `update.message.text`.
- **FIX-10:** Added `pycaw==0.8.0` and `comtypes==1.4.1` to `requirements.txt`.
- **FIX-11:** Added `.gitignore`; removed `PCCommander_v1.0.0.tar.gz` binary from repo.
- **FIX-12:** Added `self.ai_handler = None` to `PCCommanderService.__init__()`.
- **FIX-13:** Added `last_activity` tracking and `_start_context_cleanup()` thread to remove idle conversation contexts after 2 hours.
- Added `paramiko==3.4.0` to `requirements.txt` (preparation for SSH layer).
- Added complete test suite: `tests/test_config.py`, `tests/test_security_auth.py`, `tests/test_watchdog.py`, `tests/test_commands.py`.
- Added `DOCS.md`, `INSTALL_AR.txt`, `INSTALL_EN.txt`.
- Added `VERSION` file and `scripts/bump_version.py`.

### V1.0.0 — PC Commander (initial release)
- Telegram bot with GPT-4o / Gemini support.
- Screenshot, file manager, process manager, system monitor.
- AnyDesk integration, Wake-on-LAN, screen streaming.
- Fernet key generation (encryption not yet activated).
- Basic whitelist authorization.
- Cloudflare and ngrok tunnel support.
- PyInstaller build script, Inno Setup installer.
