# ═══════════════════════════════════════════════════════════════
#   SshRemote V2 — Part of NexAgent
#   Tunnel Service Script
#   - Reads config from sshremote_config.ini
#   - Auto-reconnects on disconnect
#   - Sends Telegram notification with connection details
#   - Fixes administrators_authorized_keys on every run
#   - Respects MAX_RETRIES before giving up
# ═══════════════════════════════════════════════════════════════

# ── Config loader ──────────────────────────────────────────────
function Read-IniValue {
    param([string]$Path, [string]$Section, [string]$Key)
    $inSection = $false
    foreach ($line in Get-Content $Path -Encoding UTF8 -ErrorAction SilentlyContinue) {
        $line = $line.Trim()
        if ($line -match "^\[(.+)\]$") {
            $inSection = ($matches[1].Trim() -eq $Section)
        }
        if ($inSection -and $line -match "^$Key\s*=\s*(.+)$") {
            return $matches[1].Trim()
        }
    }
    return $null
}

# ── Resolve install path (script's own directory) ──────────────
$INSTALL_PATH = Split-Path -Parent $MyInvocation.MyCommand.Path
$CONFIG_FILE  = Join-Path $INSTALL_PATH "sshremote_config.ini"

if (-not (Test-Path $CONFIG_FILE)) {
    Write-Host "$(Get-Date -Format 'HH:mm:ss') [ERROR] sshremote_config.ini not found at: $CONFIG_FILE"
    exit 1
}

# ── Read settings ──────────────────────────────────────────────
$BOT_TOKEN    = Read-IniValue $CONFIG_FILE "telegram" "bot_token"
$CHAT_ID      = Read-IniValue $CONFIG_FILE "telegram" "chat_id"
$BORE_SERVER  = Read-IniValue $CONFIG_FILE "bore" "bore_server"
$LOCAL_PORT   = Read-IniValue $CONFIG_FILE "bore" "local_port"

if (-not $BOT_TOKEN -or $BOT_TOKEN -eq "YOUR_BOT_TOKEN_HERE") {
    Write-Host "$(Get-Date -Format 'HH:mm:ss') [ERROR] bot_token not set in sshremote_config.ini"
    exit 1
}
if (-not $CHAT_ID -or $CHAT_ID -eq "YOUR_CHAT_ID_HERE") {
    Write-Host "$(Get-Date -Format 'HH:mm:ss') [ERROR] chat_id not set in sshremote_config.ini"
    exit 1
}

if (-not $BORE_SERVER) { $BORE_SERVER = "bore.pub" }
if (-not $LOCAL_PORT)  { $LOCAL_PORT  = "22" }

# ── Paths ──────────────────────────────────────────────────────
$BORE_EXE     = Join-Path $INSTALL_PATH "bore.exe"
$BORE_OUT     = Join-Path $INSTALL_PATH "bore_out.txt"
$BORE_ERR     = Join-Path $INSTALL_PATH "bore_err.txt"
$PORT_FILE    = Join-Path $INSTALL_PATH "bore_port.txt"
$LOG_FILE     = Join-Path $INSTALL_PATH "sshremote_tunnel.log"
$AUTH_KEYS    = "C:\Users\$env:USERNAME\.ssh\authorized_keys"
$ADMIN_KEYS   = "C:\ProgramData\ssh\administrators_authorized_keys"
$KEY_PUB      = Join-Path $INSTALL_PATH "sshremote_key.pub"

# ── Constants ──────────────────────────────────────────────────
$MAX_RETRIES          = 10
$RETRY_WAIT_SEC       = 5
$BORE_STARTUP_TIMEOUT = 30
$RECONNECT_DELAY_SEC  = 5

# ── Helper: write log ──────────────────────────────────────────
function Write-Log {
    param([string]$Level, [string]$Message)
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $entry = "[$ts] [$Level] $Message"
    Write-Host $entry
    Add-Content -Path $LOG_FILE -Value $entry -Encoding UTF8 -ErrorAction SilentlyContinue
}

# ── Helper: send Telegram message ─────────────────────────────
function Send-Telegram {
    param([string]$Text)
    $encoded = [uri]::EscapeDataString($Text)
    $url = "https://api.telegram.org/bot$BOT_TOKEN/sendMessage?chat_id=$CHAT_ID&text=$encoded"
    try {
        Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 10 | Out-Null
        Write-Log "INFO" "Telegram notification sent."
    } catch {
        Write-Log "WARN" "Telegram send failed: $_"
    }
}

# ── Helper: ensure bore.exe exists ────────────────────────────
function Test-BoreExe {
    if (-not (Test-Path $BORE_EXE)) {
        Write-Log "ERROR" "bore.exe not found at: $BORE_EXE"
        Send-Telegram "❌ SshRemote خطأ: bore.exe غير موجود في $BORE_EXE"
        exit 1
    }
}

# ── Helper: fix authorized_keys permissions ────────────────────
function Repair-AuthorizedKeys {
    if (-not (Test-Path $AUTH_KEYS)) {
        Write-Log "WARN" "authorized_keys missing — recreating..."
        if (Test-Path $KEY_PUB) {
            $sshDir = Split-Path $AUTH_KEYS
            if (-not (Test-Path $sshDir)) { New-Item -ItemType Directory -Path $sshDir | Out-Null }
            Copy-Item $KEY_PUB $AUTH_KEYS
        }
    }
    icacls $AUTH_KEYS /inheritance:r /grant "${env:USERNAME}:F" /grant "SYSTEM:F" | Out-Null

    if (Test-Path $AUTH_KEYS) {
        Copy-Item $AUTH_KEYS $ADMIN_KEYS -Force
        icacls $ADMIN_KEYS /inheritance:r /grant "SYSTEM:F" /grant "Administrators:F" | Out-Null
    }
}

# ── Helper: kill any running bore ─────────────────────────────
function Stop-Bore {
    Get-Process -Name "bore" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# ── Helper: clean temp files ───────────────────────────────────
function Clear-TempFiles {
    foreach ($f in @($BORE_OUT, $BORE_ERR)) {
        if (Test-Path $f) { Remove-Item $f -Force -ErrorAction SilentlyContinue }
    }
}

# ══════════════════════════════════════════════
#   MAIN LOOP
# ══════════════════════════════════════════════
Write-Log "INFO" "SshRemote V2 (NexAgent) tunnel started. Device: $env:COMPUTERNAME | User: $env:USERNAME"
Test-BoreExe

$failCount = 0

while ($true) {

    if ($failCount -ge $MAX_RETRIES) {
        $msg = "⚠️ SshRemote: فشل الاتصال $MAX_RETRIES مرات متتالية على $env:COMPUTERNAME. توقّف الـ tunnel."
        Write-Log "ERROR" "Max retries ($MAX_RETRIES) reached. Stopping."
        Send-Telegram $msg
        exit 1
    }

    Repair-AuthorizedKeys
    Stop-Bore
    Clear-TempFiles

    Write-Log "INFO" "Starting bore tunnel: local $LOCAL_PORT -> $BORE_SERVER ..."

    $proc = Start-Process `
        -FilePath $BORE_EXE `
        -ArgumentList "local $LOCAL_PORT --to $BORE_SERVER" `
        -RedirectStandardOutput $BORE_OUT `
        -RedirectStandardError $BORE_ERR `
        -NoNewWindow -PassThru

    $PORT = $null
    for ($i = 0; $i -lt $BORE_STARTUP_TIMEOUT; $i++) {
        Start-Sleep -Seconds 1
        if ($proc.HasExited) {
            Write-Log "WARN" "bore exited during startup after $i sec."
            break
        }
        $content = Get-Content $BORE_OUT -Raw -ErrorAction SilentlyContinue
        if ($content -match "$BORE_SERVER`:(\d+)") {
            $PORT = $matches[1]
            break
        }
    }

    if (-not $PORT) {
        $failCount++
        $errContent = Get-Content $BORE_ERR -Raw -ErrorAction SilentlyContinue
        Write-Log "WARN" "Failed to get port (attempt $failCount/$MAX_RETRIES). bore stderr: $errContent"
        Start-Sleep -Seconds $RETRY_WAIT_SEC
        continue
    }

    $failCount = 0
    Write-Log "INFO" "Connected! Port: $PORT"
    Set-Content -Path $PORT_FILE -Value $PORT -Encoding UTF8

    Start-Sleep -Seconds 10

    if ($proc.HasExited) {
        Write-Log "WARN" "bore exited immediately after port acquisition. Retrying..."
        continue
    }

    $device = $env:COMPUTERNAME
    $user   = $env:USERNAME
    $msg    = "✅ SshRemote (NexAgent) متصل!`n`n🖥️ الجهاز: $device`n👤 المستخدم: $user`n`n🔗 للاتصال:`nssh $user@$BORE_SERVER -p $PORT`n`n🔑 المفتاح: sshremote_key"
    Send-Telegram $msg

    Write-Log "INFO" "Tunnel stable. Monitoring..."
    while (-not $proc.HasExited) {
        Start-Sleep -Seconds 10
    }

    Write-Log "INFO" "bore disconnected. Reconnecting in $RECONNECT_DELAY_SEC sec..."
    Start-Sleep -Seconds $RECONNECT_DELAY_SEC
}
