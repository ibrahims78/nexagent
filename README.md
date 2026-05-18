# NexAgent

> Full remote control of your Windows PC via Telegram — powered by AI, secured by design.
>
> تحكم كامل بجهاز الكمبيوتر عن بُعد عبر تيليغرام — مدعوم بالذكاء الاصطناعي، مؤمَّن بالتصميم.

[![Tests](https://github.com/ibrahims78/nexagent/actions/workflows/tests.yml/badge.svg)](https://github.com/ibrahims78/nexagent/actions/workflows/tests.yml)
![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![Platform](https://img.shields.io/badge/Platform-Windows-informational?logo=windows)
![AI](https://img.shields.io/badge/AI-GPT--4o%20%7C%20Gemini-blueviolet)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Overview | نظرة عامة

**English:** NexAgent is a two-layer remote PC control system for Windows. Send a Telegram message (or voice note) and NexAgent executes it — taking screenshots, running commands, managing files, streaming your screen, waking the PC from sleep, and more. An optional SSH tunnel layer gives you full terminal access without port forwarding or a static IP.

**العربية:** NexAgent نظام للتحكم الكامل بجهاز الكمبيوتر عن بُعد يعمل على ويندوز، ويتكون من طبقتين. أرسل رسالة نصية أو رسالة صوتية عبر تيليغرام وسيُنفّذها البوت فوراً — التقاط لقطات الشاشة، تنفيذ الأوامر، إدارة الملفات، بث الشاشة، تشغيل الجهاز من السكون، والمزيد. الطبقة الثانية الاختيارية توفر وصولاً كاملاً عبر SSH دون الحاجة لـ IP ثابت أو فتح منافذ.

```
┌─────────────────────────────────────────────────────────────────┐
│                    هاتفك / Your Phone                           │
│                      Telegram Client                            │
└─────────────────────────────┬───────────────────────────────────┘
                              │  HTTPS
              ┌───────────────▼───────────────┐
              │        Telegram Servers        │
              └───────────────┬───────────────┘
                              │
          ┌───────────────────▼────────────────────┐
          │        الطبقة الأولى — Layer 1          │
          │        بوت الذكاء الاصطناعي / AI Bot    │
          │   python-telegram-bot  +  GPT-4o/Gemini │
          │   PC Control · Streaming · Scheduling   │
          └───────────────────┬────────────────────┘
                              │  localhost
          ┌───────────────────▼────────────────────┐
          │       جهاز الكمبيوتر / Windows PC       │
          │                                         │
          │  الطبقة الثانية (اختياري) / Layer 2     │
          │  SshRemote V2 — bore.exe → SSH public   │
          └─────────────────────────────────────────┘
```

---

## Features | المميزات

### AI & Natural Language | الذكاء الاصطناعي واللغة الطبيعية

- **GPT-4o / Gemini** — أرسل الأوامر بالعربية أو الإنجليزية، نصاً أو رسالة صوتية
- **التحكم البصري** — يحلل الذكاء الاصطناعي شاشتك وينقر ويكتب ويتنقل تلقائياً
- **المهام متعددة الخطوات** — صف مهمة كاملة في رسالة واحدة والبوت ينفذها خطوة بخطوة
- **الردود الصوتية** — ردود صوتية اختيارية عبر تقنية تحويل النص إلى كلام (gTTS)

---

- **GPT-4o / Gemini** — send commands in Arabic or English, plain text or voice note
- **Vision control** — AI analyzes your screen and clicks, types, or navigates autonomously
- **Multi-step tasks** — describe a workflow in one message; the bot executes it step by step
- **Voice replies** — optional text-to-speech responses via gTTS

---

### PC Control | التحكم بالجهاز

| الفئة / Category | ما يمكنك فعله / What you can do |
|---|---|
| **النظام / System** | لقطة شاشة، إحصائيات (CPU/RAM/قرص/حرارة)، قفل الشاشة، مستوى الصوت |
| **الطاقة / Power** | إيقاف/إعادة التشغيل بمؤقت، إلغاء، تشغيل عن بُعد (WoL) |
| **التطبيقات / Apps** | فتح/إغلاق التطبيقات، عرض العمليات الجارية |
| **الملفات / Files** | تصفح، بحث (Regex)، حذف، قراءة وتعديل ملفات Word |
| **AnyDesk** | تشغيل، إيقاف، الحصول على معرف الجلسة |

---

### Screen Streaming | بث الشاشة

- بث MJPEG مباشر عبر Flask — افتحه في أي متصفح
- محمي بكلمة مرور مشفرة بـ PBKDF2
- قابل للضبط: معدل الإطارات، الجودة، والحجم
- يمكن كشفه للإنترنت عبر Cloudflare Tunnel أو ngrok بأمر واحد

---

- MJPEG stream served over Flask — open in any browser
- Password-protected with PBKDF2-hashed credentials
- Configurable FPS, quality, and scale
- Expose via Cloudflare Tunnel or ngrok with one command

---

### SSH Tunnel Layer | طبقة نفق SSH (SshRemote V2)

- يستخدم `bore.exe` لاختراق NAT — لا IP ثابت، لا فتح منافذ
- وصول كامل عبر SSH + SFTP: تنفيذ أوامر، نقل ملفات
- يعمل كمهمة مجدولة في ويندوز عند الإقلاع

---

- Uses `bore.exe` for NAT traversal — no static IP, no port forwarding
- Full SSH + SFTP access: execute commands, transfer files
- Runs as a Windows scheduled task at startup

---

### Pre-Login Agent | وكيل ما قبل تسجيل الدخول

- يعمل كمهمة SYSTEM **قبل** تسجيل دخول أي مستخدم
- يرسل إشعاراً على تيليغرام عند إقلاع الجهاز
- اضغط زر الرد من أي مكان لتفعيل الدخول التلقائي عبر Autologon.exe

---

- Runs as a SYSTEM task **before** any user logs in
- Sends a Telegram notification when the PC boots
- Tap the reply button from anywhere to trigger auto-login via Autologon.exe

---

### Scheduler | المجدول الزمني

- جدوِل أي أمر من أوامر البوت في وقت محدد أو بفاصل زمني
- تقارير يومية تُسلَّم تلقائياً

---

- Schedule any bot command at a fixed time or interval
- Daily reports delivered automatically

---

### Security | الأمان

- **قائمة السماح** ← **قائمة الحظر** ← **تحديد المعدل** (30 طلب/دقيقة) ← **جلسة PIN**
- تشفير كامل لجميع الإعدادات الحساسة (توكن، مفاتيح API) بـ Fernet (AES-128-CBC + HMAC-SHA256)
- توكن HTTP API مُخزَّن مشفراً على القرص
- أنماط الأوامر الخطرة محجوبة قبل التنفيذ (`format`، `reg delete`، `wmic`، `vssadmin`، وغيرها)
- توكنات الجلسة بصلاحية محدودة وتنظيف تلقائي

---

- **Allowlist** → **blocklist** → **rate limiting** (30 req/min) → **PIN session**
- All sensitive config (tokens, API keys) encrypted with Fernet (AES-128-CBC + HMAC-SHA256)
- HTTP API token stored encrypted on disk
- Dangerous shell patterns blocked before execution (`format`, `reg delete`, `wmic`, `vssadmin`, and more)
- Session tokens with TTL and automatic cleanup

---

## Project Structure | هيكل المشروع

```
nexagent/
├── pc-commander/               # الطبقة الأولى — بوت تيليغرام / Layer 1 — Telegram bot
│   ├── src/
│   │   ├── bot/                # مُوزِّع البوت والمعالجات / Bot dispatcher & handlers
│   │   ├── pc_control/         # أوامر التحكم: شاشة، عمليات، ملفات، WoL
│   │   ├── streaming/          # بث الشاشة / Screen stream (Flask + MJPEG)
│   │   ├── scheduler/          # المجدول الزمني / Task scheduler
│   │   ├── ai/                 # تكامل GPT-4o / Gemini
│   │   ├── server/             # خادم HTTP المحلي / Local HTTP API server
│   │   ├── gui/                # نافذة الإعدادات + أيقونة الشريط
│   │   └── utils/              # إعدادات، تشفير، سجل الأحداث
│   ├── pre_login/              # وكيل الإقلاع / Pre-login boot agent
│   ├── wol_agent/              # وكيل WoL للأندرويد/Termux
│   ├── tests/                  # مجموعة اختبارات pytest
│   ├── main.py                 # نقطة الدخول / Entry point
│   ├── requirements.txt
│   └── install.bat             # مثبّت بنقرة واحدة / One-click installer
│
├── SshRemote_V2/               # الطبقة الثانية — نفق SSH / Layer 2 — SSH tunnel
│   ├── core/
│   │   ├── setup_v2.bat        # إعداد وتثبيت النفق
│   │   └── sshremote_config.ini
│   └── uninstall_v2.bat
│
├── .github/workflows/
│   └── tests.yml               # CI — pytest على windows-latest
└── README.md
```

---

## Quick Start | البدء السريع

### Prerequisites | المتطلبات

- ويندوز 10 / 11
- Python 3.10 أو أحدث ([python.org](https://python.org/downloads)) — فعّل **"Add Python to PATH"** أثناء التثبيت
- توكن بوت تيليغرام من [@BotFather](https://t.me/BotFather)
- معرف المحادثة (Chat ID) من [@userinfobot](https://t.me/userinfobot)
- مفتاح API من OpenAI أو Google Gemini

---

- Windows 10 / 11
- Python 3.10 or later ([python.org](https://python.org/downloads)) — enable **"Add Python to PATH"** during install
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- Your Telegram chat ID from [@userinfobot](https://t.me/userinfobot)
- An OpenAI or Google Gemini API key

---

### 1 — Install | التثبيت

**العربية:** انقر بزر الفأرة الأيمن على `install.bat` ← **تشغيل كمسؤول**. سيقوم المثبّت بـ:
- التحقق من Python و pip
- تثبيت جميع المكتبات من `requirements.txt`
- نسخ `nexagent_config.ini.template` ← `nexagent_config.ini`

**English:** Right-click `install.bat` → **Run as administrator**. The installer will:
- Check Python and pip
- Install all dependencies from `requirements.txt`
- Copy `nexagent_config.ini.template` → `nexagent_config.ini`

---

### 2 — Configure | الإعداد

**العربية:** افتح `pc-commander/nexagent_config.ini` وأدخل بياناتك:

**English:** Open `pc-commander/nexagent_config.ini` and fill in your credentials:

```ini
[telegram]
bot_token = YOUR_BOT_TOKEN   ; توكن البوت من @BotFather
chat_id   = YOUR_CHAT_ID     ; معرفك من @userinfobot

[ai]
provider = gemini             ; أو openai / or: openai
gemini_api_key = YOUR_KEY
; openai_api_key = YOUR_KEY
```

> **العربية:** ملف الإعدادات لا يُرفع إلى git أبداً. جميع البيانات الحساسة تُشفَّر تلقائياً عند أول تشغيل.
>
> **English:** The config file is never committed to git. All secrets are encrypted on first run.

---

### 3 — Run | التشغيل

```bat
cd pc-commander
python main.py
```

**العربية:** ستظهر أيقونة في شريط المهام. افتح الإعدادات منها للتحكم بجميع الخيارات عبر الواجهة الرسومية.

**English:** A system tray icon appears. Open Settings from the tray to adjust all options via the GUI.

---

### 4 — (Optional) Enable SSH Layer 2 | (اختياري) تفعيل طبقة SSH

```bat
cd SshRemote_V2\core
notepad sshremote_config.ini   :: أدخل التوكن ومعرف المحادثة / add bot token + chat ID
setup_v2.bat                   :: شغّل كمسؤول / run as Administrator
```

**العربية:** يُسجَّل النفق كمهمة مجدولة في ويندوز ويبدأ تلقائياً مع كل إقلاع.

**English:** The tunnel registers as a Windows scheduled task and starts automatically on boot.

---

## Bot Command Reference | مرجع أوامر البوت

| الأمر / Command | الوصف / Description |
|---|---|
| `screenshot` | التقاط الشاشة وإرسالها / Capture and send the current screen |
| `system_status` | تقرير CPU، RAM، القرص، الحرارة / CPU, RAM, disk, and temperature report |
| `daily_report` | إنشاء وإرسال التقرير اليومي / Generate and send the daily summary now |
| `lock` | قفل جلسة ويندوز / Lock the Windows session |
| `volume [0-100]` | ضبط مستوى الصوت / Set system volume |
| `shutdown [دقائق]` | إيقاف التشغيل بعد N دقيقة / Shut down in N minutes |
| `restart [دقائق]` | إعادة التشغيل بعد N دقيقة / Restart in N minutes |
| `cancel_shutdown` | إلغاء الإيقاف المجدول / Cancel a pending shutdown/restart |
| `open_app <اسم>` | تشغيل تطبيق مسموح به / Launch an allowed application |
| `close_app <اسم>` | إنهاء عملية جارية / Terminate a running process |
| `list_processes` | عرض البرامج النشطة / List active processes |
| `list_files <مسار>` | تصفح مجلد / Browse a directory |
| `search_files <نمط>` | بحث عن ملفات / Search files by name or regex |
| `read_word <ملف>` | قراءة ملف .docx / Read a .docx file |
| `edit_word <ملف> <نص>` | إضافة نص لملف Word / Append text to a .docx file |
| `stream_start` | بدء بث الشاشة / Start the screen stream |
| `stream_stop` | إيقاف البث / Stop the stream |
| `stream_status` | الحصول على رابط البث / Get the stream URL |
| `wol_start` | إرسال حزمة Wake-on-LAN / Send Wake-on-LAN magic packet |
| `wol_status` | التحقق من تشغيل الجهاز / Check if the target PC is online |
| `ssh_exec <أمر>` | تنفيذ أمر عبر SSH / Run a command over SSH |
| `sftp_get <مسار>` | تحميل ملف عبر SFTP / Download a file via SFTP |
| `sftp_put` | رفع ملف عبر SFTP (أرسله كمرفق) / Upload a file via SFTP |
| `ssh_bore_port` | الحصول على منفذ SSH العام / Get the current public SSH tunnel port |
| `vision_do <مهمة>` | الذكاء الاصطناعي ينفذ إجراء بصرياً / AI performs an action using screen vision |
| `vision_describe` | الذكاء الاصطناعي يصف الشاشة / AI describes the current screen in detail |
| `vision_find_click <عنصر>` | الذكاء الاصطناعي يجد عنصراً وينقر عليه / AI finds and clicks a UI element |
| `vision_task <هدف>` | الذكاء الاصطناعي ينفذ مهمة متعددة الخطوات / AI executes a multi-step visual workflow |
| `security_report` | عرض أحداث الأمان الأخيرة / Show recent security events |
| `security_block <id>` | حظر معرف تيليغرام / Block a Telegram user ID |
| `security_unblock <id>` | رفع الحظر / Unblock a user |
| `logout` | إنهاء جلسة PIN الحالية / End the current PIN session |

---

## Configuration Reference | مرجع الإعدادات

**العربية:** جميع الإعدادات في `nexagent_config.ini` (مستثنى من git). الأقسام الرئيسية:

**English:** All settings live in `nexagent_config.ini` (gitignored). Key sections:

| القسم / Section | الإعدادات الرئيسية / Key settings |
|---|---|
| `[telegram]` | `bot_token`، `chat_id` |
| `[ai]` | `provider` (`openai`/`gemini`)، `openai_api_key`، `gemini_api_key` |
| `[streaming]` | `password`، `fps`، `quality`، `scale`، `port` |
| `[tunnel]` | `provider` (`cloudflare`/`ngrok`)، `ngrok_token` |
| `[security]` | `pin`، `rate_limit`، `session_ttl` |
| `[general]` | `timezone`، `start_with_windows`، `extra_allowed_apps` |

> **العربية:** عند أول تشغيل، تُشفَّر القيم الحساسة بمفتاح Fernet خاص بالجهاز مُخزَّن في `%APPDATA%\PCCommander\secret.key`.
>
> **English:** On first run, sensitive values are encrypted with a per-machine Fernet key stored in `%APPDATA%\PCCommander\secret.key`.

---

## Running Tests | تشغيل الاختبارات

```bat
cd pc-commander
python -m pytest tests/ -v
```

**العربية:** يُشغِّل pipeline الـ CI مجموعة الاختبارات كاملةً تلقائياً عند كل push أو pull request عبر GitHub Actions (على بيئة ويندوز).

**English:** The CI pipeline runs the full suite automatically on every push and pull request via GitHub Actions (Windows runner).

---

## Tech Stack | المكتبات المستخدمة

| المكوّن / Component | المكتبة / Library |
|---|---|
| بوت تيليغرام / Telegram bot | `python-telegram-bot` 20+ |
| ذكاء اصطناعي OpenAI | `openai` (GPT-4o, Whisper) |
| ذكاء اصطناعي Google | `google-generativeai` (Gemini 1.5 Flash) |
| واجهة رسومية / GUI | `customtkinter`، `pystray` |
| التقاط الشاشة / Screen capture | `Pillow` (ImageGrab)، `pyautogui` |
| البث / Streaming | `Flask`، `Werkzeug` |
| SSH / SFTP | `paramiko` |
| التشفير / Encryption | `cryptography` (Fernet) |
| معلومات النظام / System info | `psutil`، `pycaw`، `pywin32` |
| تحويل نص لصوت / TTS | `gTTS` |
| الاختبارات / Testing | `pytest` |

---

## License | الترخيص

MIT — see [LICENSE](LICENSE) for details.
