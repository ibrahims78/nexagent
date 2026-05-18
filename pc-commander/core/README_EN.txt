╔══════════════════════════════════════════════════════════════════╗
║          SshRemote V2 — Part of NexAgent Project                 ║
║             Installation & Usage Guide                           ║
║                Secure Remote SSH Access                          ║
╚══════════════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  What is SshRemote?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  SshRemote is the infrastructure layer of the NexAgent project.
  It enables full SSH access to a Windows machine from anywhere,
  even when behind a NAT router with no static IP.

  How it works:
  1. bore.exe opens a public tunnel on bore.pub
  2. The assigned port is sent to you via Telegram
  3. You connect from anywhere with a simple SSH command

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Requirements
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  - OS: Windows 10 or Windows 11
  - Permissions: Administrator rights
  - Active internet connection
  - Telegram account + a bot (creation explained in Step 0)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Step 0: Create a Telegram Bot (skip if you already have one)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  [ Create the bot ]
  1. Open Telegram and search for: @BotFather
  2. Send: /newbot
  3. Enter a display name (example: My NexAgent Bot)
  4. Enter a username ending in "bot" (example: mynexagent_bot)
  5. Save the token BotFather sends you

  [ Get your Chat ID ]
  1. Search for: @userinfobot
  2. Send: /start — save the numeric ID it replies with

  ⚠️ Send /start to your new bot before running setup.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Step 1: Pre-setup
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Note: sshremote_config.ini is NOT included in the repository to
  prevent credentials from being committed to git. A template file
  (sshremote_config.ini.template) is provided instead.

  If sshremote_config.ini does not exist, setup_v2.bat will create
  it automatically from the template on first run, then pause and
  ask you to fill in your credentials before continuing.

  To configure manually:
  1. Copy sshremote_config.ini.template → sshremote_config.ini
  2. Open: sshremote_config.ini  (with Notepad)
  3. Fill in:

     bot_token = your bot token here
     chat_id   = your Chat ID here

  4. Save the file.
  5. (Optional) Change install_path — default: C:\SshRemote_V2

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Step 2: Installation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  1. Right-click: setup_v2.bat → "Run as administrator"
  2. Wait for all 7 steps — each shows "OK"
  3. When "Setup Complete!" appears — done
  4. Check Telegram — connection message arrives within 30 seconds

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Step 3: Connecting remotely
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  [ Windows — PowerShell or CMD ]
    ssh -i .\sshremote_key USERNAME@bore.pub -p PORT

  [ Mac / Linux — Terminal ]
    chmod 600 sshremote_key
    ssh -i ./sshremote_key USERNAME@bore.pub -p PORT

  Example:
    ssh -i sshremote_key ibrahim@bore.pub -p 54321

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  File Reference
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  sshremote_config.ini     - Telegram credentials & install path  ← fill first
  setup_v2.bat             - Full installer (run once as admin)
  start_tunnel_v2.bat      - Manually start the tunnel
  stop_tunnel_v2.bat       - Manually stop the tunnel
  show_port_v2.bat         - Display current active port
  uninstall_v2.bat         - Fully remove SshRemote
  sshremote_tunnel_v2.ps1  - Main tunnel script (runs automatically)
  sshremote_key.pub        - SSH public key (safe to share)
  bore.exe                 - bore tunnel binary
  sshremote_key            - ⚠️ SSH private key — never share this

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Managing the Tunnel
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Start:     Right-click start_tunnel_v2.bat  → Run as administrator
  Stop:      Right-click stop_tunnel_v2.bat   → Run as administrator
  Show port: Run show_port_v2.bat (no admin needed)
  Uninstall: Right-click uninstall_v2.bat     → Run as administrator

  The tunnel starts automatically on every Windows login.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Troubleshooting
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  No Telegram message → check bot_token/chat_id, send /start to bot
                        check log: C:\SshRemote_V2\sshremote_tunnel.log
  Access Denied       → right-click → Run as administrator
  Connection refused  → run show_port_v2.bat, confirm tunnel is up
  Permission denied   → use -i sshremote_key flag; chmod 600 on Mac/Linux
  bore keeps stopping → auto-retries 10 times; run stop then start manually

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Security Notes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ⚠️ sshremote_key grants full access — never share or upload it.
  ⚠️ If compromised: run uninstall_v2.bat immediately.
  ⚠️ Stop the tunnel when not needed via stop_tunnel_v2.bat.
  ⚠️ Do not install on machines you do not own.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Version: V2 | NexAgent Project | 2026
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
