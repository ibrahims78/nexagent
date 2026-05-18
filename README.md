# NexAgent

> Full remote control of your Windows PC via Telegram — powered by AI, secured by design.

[![Tests](https://github.com/ibrahims78/nexagent/actions/workflows/tests.yml/badge.svg)](https://github.com/ibrahims78/nexagent/actions/workflows/tests.yml)
![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![Platform](https://img.shields.io/badge/Platform-Windows-informational?logo=windows)
![AI](https://img.shields.io/badge/AI-GPT--4o%20%7C%20Gemini-blueviolet)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Overview

NexAgent is a two-layer remote PC control system for Windows. Send a Telegram message (or voice note) and NexAgent executes it — taking screenshots, running commands, managing files, streaming your screen, waking the PC from sleep, and more. An optional SSH tunnel layer gives you full terminal access without port forwarding or a static IP.

```
┌─────────────────────────────────────────────────────────────────┐
│                         Your Phone                              │
│                      Telegram Client                            │
└─────────────────────────────┬───────────────────────────────────┘
                              │  HTTPS
              ┌───────────────▼───────────────┐
              │        Telegram Servers        │
              └───────────────┬───────────────┘
                              │
          ┌───────────────────▼────────────────────┐
          │             Layer 1 — AI Bot            │
          │   python-telegram-bot  +  GPT-4o/Gemini │
          │   PC Control · Streaming · Scheduling   │
          └───────────────────┬────────────────────┘
                              │  localhost
          ┌───────────────────▼────────────────────┐
          │           Windows PC (Target)           │
          │                                         │
          │  Layer 2 (optional) — SshRemote V2      │
          │  bore.exe → public SSH endpoint         │
          └─────────────────────────────────────────┘
```

---

## Features

### AI & Natural Language
- **GPT-4o / Gemini** — send commands in Arabic or English, plain text or voice note
- **Vision control** — AI analyzes your screen and clicks, types, or navigates autonomously
- **Multi-step tasks** — describe a workflow in one message; the bot executes it step by step
- **Voice replies** — optional text-to-speech responses via gTTS

### PC Control
| Category | What you can do |
|---|---|
| **System** | Screenshot, system stats (CPU / RAM / disk / temp), lock screen, volume |
| **Power** | Shutdown / restart with timer, cancel, Wake-on-LAN |
| **Apps** | Open / close applications, list running processes |
| **Files** | Browse, search (regex), delete, read & edit Word documents |
| **AnyDesk** | Start, stop, retrieve remote ID |

### Screen Streaming
- MJPEG stream served over Flask — open in any browser
- Password-protected with PBKDF2-hashed credentials
- Configurable FPS, quality, and scale
- Expose via Cloudflare Tunnel or ngrok with one command

### SSH Tunnel Layer (SshRemote V2)
- Uses `bore.exe` for NAT traversal — no static IP, no port forwarding
- Full SSH + SFTP access: execute commands, transfer files
- Runs as a Windows scheduled task at startup

### Pre-Login Agent
- Runs as a SYSTEM task **before** any user logs in
- Sends a Telegram notification when the PC boots
- Tap the reply button from anywhere to trigger auto-login via Autologon.exe

### Scheduler
- Schedule any bot command at a fixed time or interval
- Daily reports delivered automatically

### Security
- **Allowlist** → **blocklist** → **rate limiting** (30 req/min) → **PIN session**
- All sensitive config (tokens, API keys) encrypted with Fernet (AES-128-CBC + HMAC-SHA256)
- HTTP API token stored encrypted on disk
- Dangerous shell patterns blocked before execution (`format`, `reg delete`, `wmic`, `vssadmin`, and more)
- Session tokens with TTL and automatic cleanup

---

## Project Structure

```
nexagent/
├── pc-commander/               # Layer 1 — Telegram bot
│   ├── src/
│   │   ├── bot/                # Bot dispatcher & handlers
│   │   ├── pc_control/         # Commands: screenshot, process, files, WoL…
│   │   ├── streaming/          # Screen stream (Flask + MJPEG)
│   │   ├── scheduler/          # Task scheduler
│   │   ├── ai/                 # GPT-4o / Gemini integration
│   │   ├── server/             # Local HTTP API server
│   │   ├── gui/                # Settings window (CustomTkinter) + tray icon
│   │   └── utils/              # Config, encryption, logger
│   ├── pre_login/              # Pre-login boot agent
│   ├── wol_agent/              # Android/Termux WoL agent
│   ├── tests/                  # pytest test suite
│   ├── main.py                 # Entry point
│   ├── requirements.txt
│   └── install.bat             # One-click installer
│
├── SshRemote_V2/               # Layer 2 — SSH tunnel
│   ├── core/
│   │   ├── setup_v2.bat        # Install & configure tunnel
│   │   └── sshremote_config.ini
│   └── uninstall_v2.bat
│
├── .github/workflows/
│   └── tests.yml               # CI — runs pytest on windows-latest
└── README.md
```

---

## Quick Start

### Prerequisites
- Windows 10 / 11
- Python 3.10 or later ([python.org](https://python.org/downloads)) — enable **"Add Python to PATH"** during install
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- Your Telegram chat ID from [@userinfobot](https://t.me/userinfobot)
- An OpenAI or Google Gemini API key

### 1 — Install

Right-click `install.bat` → **Run as administrator**. The installer will:
- Check Python and pip
- Install all dependencies from `requirements.txt`
- Copy `nexagent_config.ini.template` → `nexagent_config.ini`

### 2 — Configure

Open `pc-commander/nexagent_config.ini` and fill in your credentials:

```ini
[telegram]
bot_token = YOUR_BOT_TOKEN
chat_id   = YOUR_CHAT_ID

[ai]
provider = gemini          ; or: openai
gemini_api_key = YOUR_KEY
; openai_api_key = YOUR_KEY
```

> The config file is never committed to git. All secrets are encrypted on first run.

### 3 — Run

```bat
cd pc-commander
python main.py
```

A system tray icon appears. Open Settings from the tray to adjust all options via the GUI.

### 4 — (Optional) Enable SSH Layer 2

```bat
cd SshRemote_V2\core
notepad sshremote_config.ini   # add your bot token + chat ID
setup_v2.bat                   # run as Administrator
```

The tunnel registers as a Windows scheduled task and starts automatically on boot.

---

## Bot Command Reference

| Command | Description |
|---|---|
| `screenshot` | Capture and send the current screen |
| `system_status` | CPU, RAM, disk, and temperature report |
| `daily_report` | Generate and send the daily summary now |
| `lock` | Lock the Windows session |
| `volume [0-100]` | Set system volume |
| `shutdown [min]` | Shut down in N minutes (default: now) |
| `restart [min]` | Restart in N minutes |
| `cancel_shutdown` | Cancel a pending shutdown/restart |
| `open_app <name>` | Launch an allowed application |
| `close_app <name>` | Terminate a running process |
| `list_processes` | List active processes |
| `list_files <path>` | Browse a directory |
| `search_files <pattern>` | Search files by name or regex |
| `read_word <file>` | Read a .docx file |
| `edit_word <file> <text>` | Append text to a .docx file |
| `stream_start` | Start the screen stream |
| `stream_stop` | Stop the stream |
| `stream_status` | Get the stream URL |
| `wol_start` | Send Wake-on-LAN magic packet |
| `wol_status` | Check if the target PC is online |
| `ssh_exec <cmd>` | Run a command over SSH |
| `sftp_get <path>` | Download a file via SFTP |
| `sftp_put` | Upload a file via SFTP (send as attachment) |
| `ssh_bore_port` | Get the current public SSH tunnel port |
| `vision_do <task>` | AI performs an action using screen vision |
| `vision_describe` | AI describes the current screen in detail |
| `vision_find_click <element>` | AI finds and clicks a UI element |
| `vision_task <goal>` | AI executes a multi-step visual workflow |
| `security_report` | Show recent security events |
| `security_block <id>` | Block a Telegram user ID |
| `security_unblock <id>` | Unblock a user |
| `logout` | End the current PIN session |

---

## Configuration Reference

All settings live in `nexagent_config.ini` (gitignored). Key sections:

| Section | Key settings |
|---|---|
| `[telegram]` | `bot_token`, `chat_id` |
| `[ai]` | `provider` (`openai`/`gemini`), `openai_api_key`, `gemini_api_key` |
| `[streaming]` | `password`, `fps`, `quality`, `scale`, `port` |
| `[tunnel]` | `provider` (`cloudflare`/`ngrok`), `ngrok_token` |
| `[security]` | `pin`, `rate_limit`, `session_ttl` |
| `[general]` | `timezone`, `start_with_windows`, `extra_allowed_apps` |

> On first run, sensitive values are encrypted with a per-machine Fernet key stored in `%APPDATA%\PCCommander\secret.key`.

---

## Running Tests

```bat
cd pc-commander
python -m pytest tests/ -v
```

The CI pipeline runs the full suite automatically on every push and pull request via GitHub Actions (Windows runner).

---

## Tech Stack

| Component | Library |
|---|---|
| Telegram bot | `python-telegram-bot` 20+ |
| AI — OpenAI | `openai` (GPT-4o, Whisper) |
| AI — Google | `google-generativeai` (Gemini 1.5 Flash) |
| GUI | `customtkinter`, `pystray` |
| Screen capture | `Pillow` (ImageGrab), `pyautogui` |
| Streaming | `Flask`, `Werkzeug` |
| SSH / SFTP | `paramiko` |
| Encryption | `cryptography` (Fernet) |
| System info | `psutil`, `pycaw`, `pywin32` |
| Text-to-speech | `gTTS` |
| Testing | `pytest` |

---

## License

MIT — see [LICENSE](LICENSE) for details.
