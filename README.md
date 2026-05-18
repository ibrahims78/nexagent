# NexAgent

Remote PC control via Telegram and SSH, built for Windows.

## Description

NexAgent lets you monitor and control your Windows PC from anywhere using a Telegram bot. It supports AI-assisted commands (OpenAI / Gemini), screen streaming, process management, Wake-on-LAN, scheduled tasks, and a secure SSH tunnel layer for direct remote access.

## Folder Structure

```
pc-commander/       Bot layer — Telegram bot, AI handler, PC control commands
SshRemote_V2/       SSH tunnel layer — persistent reverse SSH tunnel via bore
```

## Quick Start

1. Copy the config template and fill in your credentials:
   ```
   copy pc-commander\nexagent_config.ini.template pc-commander\nexagent_config.ini
   ```
   Edit `nexagent_config.ini` and set your Telegram bot token, chat ID, and AI API key.

2. Install dependencies:
   ```
   cd pc-commander
   pip install -r requirements.txt
   ```

3. Run the bot:
   ```
   python main.py
   ```

4. (Optional) Enable the SSH tunnel layer:
   - Edit `SshRemote_V2\sshremote_config.ini`
   - Run `SshRemote_V2\setup_v2.bat` as Administrator

## Documentation

See [DOCS.md](DOCS.md) for full feature reference, command list, and configuration options.
