# NexAgent — Complete Documentation

**Version:** 1.3.0  
**Updated:** 2026-05-19

---

## 1. PROJECT OVERVIEW

NexAgent is a two-layer Windows PC remote-control system:

- **Layer 1 — AI Telegram Bot:** Control your Windows PC through natural Arabic (or English) commands. Powered by OpenAI GPT-4o or Google Gemini 1.5 Flash.
- **Layer 2 — SSH Tunnel (SshRemote V2):** Secure, passwordless SSH access to the machine via a bore tunnel. Works even without a static IP or port-forwarding.

**Key design goals:**
- Single authorised user (or a small whitelist) controls one Windows machine.
- Minimal setup — one config file, one executable.
- Layered security: whitelist → block list → rate limit → PIN → session token.
- Resilient: a Watchdog thread restarts the bot automatically if it crashes.
- SSH layer auto-reconnects and notifies you on Telegram with the new port.

---

## 2. DIRECTORY STRUCTURE

```
pc-commander/
├── main.py                      Entry point (GUI + tray icon)
├── requirements.txt             Python dependencies
├── build.bat                    Build & package script (both layers)
├── install.bat                  One-click installer (both layers)
├── uninstall.bat                Uninstaller (both layers)
├── create_icon.py               Generates assets/icon.ico
├── nexagent_config.ini          Unified config template (Layer 1 + Layer 2)
├── VERSION                      Monotonic build counter
├── DOCS.md                      This file
├── INSTALL_AR.txt               Arabic installation guide
├── INSTALL_EN.txt               English installation guide
├── LICENSE.txt
│
├── core/                        ── Layer 2: SshRemote V2 ──
│   ├── sshremote_tunnel_v2.ps1  PowerShell tunnel service (bore + reconnect)
│   ├── sshremote_config.ini     Layer 2 config (bot_token, chat_id, ports)
│   ├── sshremote_key.pub        Public key deployed to authorized_keys
│   ├── setup_v2.bat             Full Layer 2 installer (OpenSSH + task)
│   ├── start_tunnel_v2.bat      Start tunnel manually
│   ├── stop_tunnel_v2.bat       Stop tunnel
│   ├── show_port_v2.bat         Show current bore port
│   ├── uninstall_v2.bat         Remove Layer 2 completely
│   ├── README_AR.txt            Arabic Layer 2 guide
│   └── README_EN.txt            English Layer 2 guide
│   (bore.exe must be placed here manually — Windows binary)
│
├── installer/
│   └── setup.iss                Inno Setup script (GUI installer, both layers)
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
│   │   ├── autologon.py         Windows auto-login registry
│   │   └── ssh_executor.py      SSHExecutor — Layer 2 bridge
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
│   ├── test_config.py           5 tests — encryption, round-trip, defaults
│   ├── test_security_auth.py    10 tests — whitelist, PIN, session, rate-limit
│   ├── test_watchdog.py         5 tests — socket, internet check, lifecycle
│   ├── test_commands.py         7 tests — commands, vision guard, chat
│   └── test_ssh_executor.py     24 tests — SSHExecutor + SSH commands routing
│
└── pre_login/
    ├── pre_login_agent.py       Runs before Windows login (SYSTEM task)
    ├── install_pre_login.bat
    └── uninstall_pre_login.bat
```

---

## 3. CONFIGURATION REFERENCE

### 3a. Bot Config (runtime, encrypted)

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
| ssh | username | str | "" | Windows username for SSH login |
| ssh | key_path | str | "" | Path to SSH private key file |
| ssh | password | str | "" | SSH password (if no key) |
| ssh | host | str | "127.0.0.1" | SSH host (always local for Layer 2) |
| ssh | port | int | 22 | Local SSH port |
| ssh | bore_port_file | str | "C:\\SshRemote_V2\\bore_port.txt" | Path to bore port file |

### 3b. SSH Layer Config (static INI)

Template: `nexagent_config.ini` (also `core/sshremote_config.ini` for Layer 2 standalone).

| Section | Key | Description |
|---------|-----|-------------|
| telegram | bot_token | Telegram bot token (for SSH notifications) |
| telegram | chat_id | Your Telegram chat ID |
| bore | bore_server | Relay server (default: bore.pub) |
| bore | local_port | Local SSH port to tunnel (default: 22) |
| install | install_path | Where Layer 2 files live (default: C:\SshRemote_V2) |
| install | task_name | Windows Scheduled Task name |
| ssh | sshd_port | OpenSSH port (default: 22) |

---

## 4. BOT COMMANDS REFERENCE

### 4a. Layer 1 — PC Control Commands

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

### 4b. Layer 2 — SSH Commands

| Command (internal) | Description | Example Arabic trigger |
|--------------------|-------------|------------------------|
| ssh_status | Show tunnel status + connection string | حالة SSH |
| ssh_exec [cmd] | Run a shell command via SSH | نفّذ عبر SSH dir C:\ |
| ssh_list [path] | List remote directory via SFTP | اعرض ملفات سطح المكتب عبر SSH |
| sftp_get [path] | Download file from PC via SFTP | حمّل الملف C:\report.pdf |
| sftp_put [local] [remote] | Upload file to PC via SFTP | ارفع الملف للحاسب |
| ssh_bore_port | Show current bore tunnel port | منفذ النفق الحالي |

> **Note:** SSH commands require `ssh.username` to be set in the config. If the field is empty, NexAgent starts normally but all `ssh_*` commands return an Arabic error message.

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

**SSH security:** Layer 2 uses public-key authentication only (`PasswordAuthentication no` in sshd_config). The private key never leaves your control device. bore tunnels are ephemeral — a new random port is assigned on each reconnect.

---

## 6. ARCHITECTURE

### 6a. Two-Layer Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Your Phone (Telegram)                │
└───────────────────┬─────────────────────────────────────┘
                    │ HTTPS (Telegram API)
        ┌───────────▼───────────┐
        │   Layer 1: NexAgent   │  ← AI Bot (Python)
        │   Telegram Bot        │
        │   GPT-4o / Gemini     │
        └───────────┬───────────┘
                    │ Paramiko SSH (127.0.0.1:22)
        ┌───────────▼───────────┐
        │   Layer 2: SshRemote  │  ← SSH Tunnel (bore)
        │   OpenSSH Server      │
        │   bore → bore.pub:N   │
        └───────────────────────┘
                    ▲
                    │ ssh USER@bore.pub -p N (from anywhere)
              Your laptop / terminal
```

### 6b. Startup Sequence

```
main.py
  └── PCCommanderService.start()
        ├── _start_server()          → Flask HTTP server (port 5000)
        ├── _start_tunnel()          → Cloudflare or ngrok
        ├── _start_ai()              → OpenAIHandler or GeminiHandler
        ├── _wire_vision_handler()   → inject VisionHandler into commands module
        ├── _wire_ssh_executor()     → inject SSHExecutor into commands module
        ├── _start_bot()             → PCCommanderBot (daemon thread)
        ├── _start_scheduler()       → APScheduler (daily report)
        └── _start_network_monitor()
```

### 6c. Message Flow

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
      ├── LocalExecutor  (screenshot, files, processes …)
      ├── SmartExecutor  (vision_do, vision_task …)
      │         └── VisionHandler → OpenAI GPT-4o Vision
      └── SSHExecutor    (ssh_exec, sftp_get, ssh_status …)
                └── Paramiko → OpenSSH → bore tunnel → Internet
```

---

## 7. SSH LAYER (LAYER 2) — DETAILED GUIDE

### 7a. How bore works

```
bore.exe local 22 --to bore.pub
  → bore.pub assigns a random port P
  → All TCP traffic on bore.pub:P is forwarded to localhost:22
  → sshremote_tunnel_v2.ps1 sends the new port to Telegram and saves it to bore_port.txt
```

### 7b. Setup steps

1. Fill in `core/sshremote_config.ini`:
   - `bot_token` — same bot token as Layer 1
   - `chat_id` — your Telegram Chat ID
2. Place `bore.exe` in the `core/` folder (download from github.com/ekzhang/bore/releases).
3. Run `core/setup_v2.bat` **as Administrator**.
4. Within 30 seconds you will receive a Telegram message like:
   ```
   ✅ SshRemote متصل!
   🖥️ الجهاز: DESKTOP-ABC
   🔗 للاتصال:
   ssh USER@bore.pub -p 54321
   🔑 المفتاح: sshremote_key
   ```
5. Set `ssh.username` in `nexagent_config.ini` so the bot can use SSH commands.

### 7c. SSHExecutor — API

| Method | Description |
|--------|-------------|
| `connect()` | Open SSH connection |
| `close()` | Close connection gracefully |
| `exec_command(cmd)` | Execute shell command, return stdout+stderr |
| `upload_file(local, remote)` | SFTP put |
| `download_file(remote)` | SFTP get → bytes |
| `list_files(path)` | SFTP directory listing |
| `get_tunnel_port(port_file)` | Read bore_port.txt → port string |
| `tunnel_status(port_file)` | Human-readable tunnel status |

---

## 8. ADDING A NEW COMMAND

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

## 9. BUILD & DISTRIBUTION

```bat
:: From pc-commander\ directory:
build.bat
```

The script:
1. Installs all `requirements.txt` dependencies via pip.
2. Generates `assets/icon.ico` using `create_icon.py`.
3. Runs PyInstaller → produces `dist\NexAgent\NexAgent.exe`.
4. Assembles release folder with Layer 1 + Layer 2 core files + docs.
5. Creates `dist\NexAgent_V{N}.zip` (the distributable package).
6. (Optional) Compiles `installer\setup.iss` with Inno Setup → `dist\installer\NexAgent_Setup_v1.1.0.exe`.
7. Increments `VERSION` on success.

**Release zip structure:**
```
NexAgent_V{N}.zip
├── NexAgent.exe          ← Layer 1 executable
├── [PyInstaller runtime files]
├── core\                 ← Layer 2 files
│   ├── sshremote_tunnel_v2.ps1
│   ├── setup_v2.bat
│   ├── sshremote_key.pub
│   └── ...
├── nexagent_config.ini   ← Unified config template
├── install.bat           ← One-click installer
├── uninstall.bat
├── DOCS.md
├── INSTALL_AR.txt
└── INSTALL_EN.txt
```

To bump the version manually:
```
python scripts/bump_version.py
```

---

## 10. CONNECTION METHODS / طرق الاتصال

NexAgent v1.3 supports multiple simultaneous connection methods. The Connection Manager starts all available methods automatically at startup.

| الطريقة | البروتوكول | يحتاج إنترنت | يحتاج راوتر | وصول للشبكة المنزلية | الإعداد |
|---|---|:---:|:---:|:---:|:---|
| Telegram Polling (افتراضي) | HTTPS/443 | ✅ | ❌ | ❌ | لا شيء |
| Telegram Webhook | HTTPS/443 | ✅ | ❌ | ❌ | تفعيل من الإعدادات |
| HTTP API — LAN (جديد) | HTTP | ❌ | ❌ | ✅ | toggle في الإعدادات |
| HTTP API — Tailscale (جديد) | WireGuard/UDP | ✅ | ❌ | جزئي | تطبيق Tailscale |
| HTTP API — Cloudflare | HTTPS/443 | ✅ | ❌ | ❌ | cloudflared |
| HTTP API — ngrok | HTTPS/443 | ✅ | ❌ | ❌ | ngrok token |
| SSH عبر bore | TCP/SSH | ✅ | ❌ | ❌ | setup_v2.bat |
| VPN Server RRAS (جديد) | L2TP/IPsec | ✅ | ✅ (UDP 500/4500/1701) | ✅ كامل | `vpn_server_enable` |

### Connection Examples

```bash
# Telegram (always works — no URL needed)
أرسل أي رسالة للبوت على تيليغرام

# HTTP API — LAN (fastest, no internet required)
curl -H "Authorization: Bearer TOKEN" \
     -d '{"command":"screenshot"}' \
     http://192.168.1.105:5000/command

# HTTP API — Tailscale (secure, from anywhere)
curl -H "Authorization: Bearer TOKEN" \
     -d '{"command":"system_status"}' \
     http://100.94.32.17:5000/command

# SSH — via bore tunnel
ssh user@bore.pub -p 45231

# SSH — direct via Tailscale IP
ssh user@100.94.32.17

# HTTP API — Cloudflare Tunnel (public URL)
curl -H "Authorization: Bearer TOKEN" \
     -d '{"command":"list_files"}' \
     https://abc123.trycloudflare.com/command
```

### Telegram Commands for Connection Management

| الأمر | الوظيفة |
|---|---|
| `network_info` | عرض كل IPs المتاحة وحالة كل اتصال |
| `tailscale_status` | حالة Tailscale والـ IP الخاص به |
| `vpn_server_enable` | تحويل الحاسب لـ VPN Server (L2TP/IPsec) |
| `vpn_server_disable` | إيقاف VPN Server |
| `vpn_server_status` | حالة VPN والاتصالات النشطة |
| `vpn_client_list` | عرض اتصالات VPN المحفوظة |
| `vpn_client_connect [name]` | الاتصال بـ VPN محفوظ |
| `ssh_bore_port` | رقم منفذ SSH الحالي عبر bore |

---

## 11. KNOWN LIMITATIONS

- **Windows only.** The bot relies on `pywin32`, `pystray`, `pycaw`, and Windows-specific APIs. It will not run on Linux or macOS.
- **Voice transcription with Gemini** uses `speech_recognition` + Google Web Speech API (requires internet). For offline transcription, use OpenAI Whisper via the OpenAI provider.
- **AnyDesk auto-accept** is not yet implemented; the path must point to a pre-configured AnyDesk installation.
- **Screen streaming** is LAN-only unless a tunnel is active.
- **Wake-on-LAN** requires the target machine to support WoL and the router to allow directed broadcasts.
- **vision_* commands** require OpenAI GPT-4o and will not work with Gemini.
- **bore.exe** must be downloaded separately and placed in `core/` (Windows-only binary, cannot be bundled cross-platform).
- **SSH commands** (`ssh_*`, `sftp_*`) require `ssh.username` to be set; if empty, they return a graceful Arabic error and the bot continues normally.

---

## 11. CHANGELOG

### V1.1.0 — NexAgent (2026)

**Layer 1 — 13 Bug Fixes:**
- **FIX-1:** Activated Fernet encryption for bot_token, API keys, PIN, stream password in config.py.
- **FIX-2:** Unified authorization: all 5 Telegram handlers now use `_check_auth_and_session()`.
- **FIX-3:** Wired shared `VisionHandler` into `commands.py` via `set_vision_handler()`.
- **FIX-4:** Watchdog `_restart()` now calls `self.stop()` + `time.sleep(2)` + `self.start()`.
- **FIX-5:** Fixed socket leak in `watchdog._is_internet_available()` — uses `with socket.socket(...) as s`.
- **FIX-6:** Fixed `asyncio.run()` in `bot.stop()` — replaced with `loop.call_soon_threadsafe`.
- **FIX-7:** Deleted dead `src/security/auth.py`.
- **FIX-8:** Updated Gemini model from `gemini-pro` to `gemini-1.5-flash` in all 3 locations.
- **FIX-9:** Refactored `handle_voice` to call `_process_text()` instead of mutating `update.message.text`.
- **FIX-10:** Added `pycaw==0.8.0` and `comtypes==1.4.1` to `requirements.txt`.
- **FIX-11:** Added `.gitignore`; removed `PCCommander_v1.0.0.tar.gz` binary from repo.
- **FIX-12:** Added `self.ai_handler = None` to `PCCommanderService.__init__()`.
- **FIX-13:** Added `last_activity` tracking and 2-hour TTL cleanup thread.

**Layer 2 — SSH Integration (SshRemote V2):**
- Added `src/pc_control/ssh_executor.py` — `SSHExecutor` class (Paramiko wrapper).
- Added `_wire_ssh_executor()` to `main_service.py` — auto-wires from config.
- Added 6 SSH bot commands: `ssh_exec`, `ssh_status`, `ssh_list`, `sftp_get`, `sftp_put`, `ssh_bore_port`.
- Copied SshRemote V2 scripts to `core/` directory.
- Added `nexagent_config.ini` — unified config for both layers.
- Updated `installer/setup.iss` — includes Layer 2 as optional install task.
- Added `install.bat` + `uninstall.bat` — one-click scripts for both layers.
- Updated `build.bat` — produces zip with Layer 1 + Layer 2 + all docs.

**Testing:**
- 51 tests total (27 Layer 1 + 24 Layer 2), all passing.
- New: `tests/test_ssh_executor.py` — 24 tests for SSHExecutor and SSH command routing.

**Documentation:**
- Added Section 7 (SSH Layer detailed guide).
- Updated directory structure, architecture diagrams, commands reference, config reference.
- Updated `INSTALL_AR.txt` + `INSTALL_EN.txt` with Layer 2 setup steps.

### V1.0.0 — PC Commander (initial release)
- Telegram bot with GPT-4o / Gemini support.
- Screenshot, file manager, process manager, system monitor.
- AnyDesk integration, Wake-on-LAN, screen streaming.
- Fernet key generation (encryption not yet activated).
- Basic whitelist authorization.
- Cloudflare and ngrok tunnel support.
- PyInstaller build script, Inno Setup installer.
