"""
NexAgent - Windows Built-in VPN Manager
Uses Windows RRAS (Routing and Remote Access Service) to turn the PC
into a VPN server. Supports L2TP/IPsec (primary) and IKEv2 (secondary).
Requires: Windows 10/11 Pro/Enterprise + Admin rights.
"""
import subprocess
import secrets
import string
import sys
import time
import urllib.request
from src.utils.logger import get_logger

logger = get_logger()
IS_WINDOWS = sys.platform == "win32"

VPN_USER_NAME = "nexvpn"
FIREWALL_RULES = [
    ("NexAgent-VPN-UDP500",  "UDP", "500"),
    ("NexAgent-VPN-UDP4500", "UDP", "4500"),
    ("NexAgent-VPN-UDP1701", "UDP", "1701"),
]


def _run(cmd: list, timeout: int = 30) -> tuple:
    """Run a subprocess command and return (returncode, stdout, stderr)."""
    result = subprocess.run(
        cmd, capture_output=True, text=True,
        timeout=timeout, encoding="utf-8", errors="replace"
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def _run_ps(script: str, timeout: int = 60) -> tuple:
    """Run a PowerShell script and return (returncode, output)."""
    rc, out, err = _run(
        ["powershell", "-NoProfile", "-NonInteractive",
         "-ExecutionPolicy", "Bypass", "-Command", script],
        timeout=timeout
    )
    return rc, (out + "\n" + err).strip()


def _generate_psk(length: int = 32) -> str:
    """Generate a cryptographically secure pre-shared key."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _generate_password(length: int = 16) -> str:
    """Generate a secure VPN user password."""
    alphabet = string.ascii_letters + string.digits + "!@#"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def get_public_ip() -> str:
    """Fetch the machine's public IP address."""
    for url in ["https://api.ipify.org", "https://ifconfig.me/ip"]:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "NexAgent"})
            with urllib.request.urlopen(req, timeout=8) as r:
                ip = r.read().decode().strip()
                if ip:
                    return ip
        except Exception:
            continue
    return "UNKNOWN"


def get_local_ip() -> str:
    """Get the local network IP of this machine."""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


def check_windows_edition() -> dict:
    """Check if Windows edition supports RRAS VPN server."""
    if not IS_WINDOWS:
        return {"supported": False, "reason": "Not Windows"}
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
        )
        edition, _ = winreg.QueryValueEx(key, "EditionID")
        winreg.CloseKey(key)
        edition_lower = edition.lower()
        if any(e in edition_lower for e in ["home", "core"]):
            return {
                "supported": False,
                "edition": edition,
                "reason": "Windows Home لا يدعم RRAS. يحتاج Pro أو Enterprise"
            }
        return {"supported": True, "edition": edition}
    except Exception as e:
        return {"supported": True, "edition": "Unknown", "reason": str(e)}


def get_rras_status() -> str:
    """Return current RRAS service status."""
    rc, out, _ = _run(["sc", "query", "RemoteAccess"])
    if "RUNNING" in out:
        return "running"
    if "STOPPED" in out:
        return "stopped"
    return "unknown"


def enable_rras() -> tuple:
    """Enable and start the RRAS (RemoteAccess) service."""
    if get_rras_status() == "running":
        return True, "RRAS already running"
    _run(["sc", "config", "RemoteAccess", "start=", "auto"])
    rc2, _, _ = _run(["net", "start", "RemoteAccess"])
    time.sleep(3)
    if get_rras_status() == "running":
        return True, "RRAS started successfully"
    return False, f"Failed to start RRAS (rc={rc2})"


def disable_rras() -> tuple:
    """Stop and disable the RRAS service."""
    _run(["net", "stop", "RemoteAccess"])
    _run(["sc", "config", "RemoteAccess", "start=", "disabled"])
    return True, "RRAS stopped"


def configure_l2tp(psk: str) -> tuple:
    """Configure RRAS for L2TP/IPsec with a pre-shared key."""
    script = f"""
$pskReg = 'HKLM:\\SYSTEM\\CurrentControlSet\\Services\\RasMan\\Parameters'
Set-ItemProperty -Path $pskReg -Name 'ProhibitIpSec' -Value 0 -Type DWord -Force
Set-ItemProperty -Path $pskReg -Name 'AllowL2TPWeakCrypto' -Value 1 -Type DWord -Force
netsh ras set type vpnrras enabled
netsh ras set authmode vpn
"""
    rc, out = _run_ps(script)

    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Services\RasMan\Parameters",
            0, winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, "DefaultDomain", 0, winreg.REG_SZ, "")
        winreg.CloseKey(key)
    except Exception:
        pass

    _run(["netsh", "ras", "set", "presharedkey", psk])

    if rc <= 1:
        logger.info("L2TP/IPsec configured successfully")
        return True, "L2TP/IPsec configured"
    return False, f"Configuration error: {out[:200]}"


def create_vpn_user(username: str, password: str) -> tuple:
    """Create a dedicated VPN user account with dial-in permission."""
    rc1, _, _ = _run(["net", "user", username, password, "/add",
                       "/comment:NexAgent-VPN-User", "/passwordchg:no"])
    _run(["netsh", "ras", "set", "user", username, "permit"])
    if rc1 == 0 or rc1 == 2:
        logger.info(f"VPN user '{username}' ready")
        return True, f"VPN user '{username}' created/updated"
    return False, "Failed to create VPN user"


def delete_vpn_user(username: str) -> tuple:
    """Remove the VPN user account."""
    rc, _, _ = _run(["net", "user", username, "/delete"])
    return rc == 0, "VPN user removed" if rc == 0 else "User not found"


def open_vpn_firewall_rules() -> bool:
    """Add Windows Firewall rules to allow VPN traffic."""
    for name, proto, port in FIREWALL_RULES:
        _run([
            "netsh", "advfirewall", "firewall", "add", "rule",
            f"name={name}", "dir=in", "action=allow",
            f"protocol={proto}", f"localport={port}",
            "profile=any", "enable=yes"
        ])
    logger.info("VPN firewall rules added")
    return True


def close_vpn_firewall_rules() -> bool:
    """Remove VPN firewall rules."""
    for name, _, _ in FIREWALL_RULES:
        _run([
            "netsh", "advfirewall", "firewall", "delete", "rule",
            f"name={name}"
        ])
    return True


def enable_vpn_server() -> str:
    """
    Full VPN server setup: RRAS + L2TP/IPsec + user + firewall.
    Returns a formatted message with connection details.
    """
    if not IS_WINDOWS:
        return "❌ هذه الميزة لويندوز فقط"

    edition_check = check_windows_edition()
    if not edition_check["supported"]:
        return (
            f"❌ **إصدار ويندوز غير مدعوم**\n\n"
            f"الإصدار الحالي: `{edition_check.get('edition', 'Unknown')}`\n"
            f"السبب: {edition_check.get('reason', '')}\n\n"
            "✅ يحتاج: **Windows 10/11 Pro أو Enterprise**"
        )

    psk = _generate_psk(28)
    vpn_pass = _generate_password(14)

    ok, msg = enable_rras()
    if not ok:
        return f"❌ فشل تفعيل RRAS: {msg}"

    ok, msg = configure_l2tp(psk)
    if not ok:
        logger.warning(f"L2TP config warning: {msg}")

    create_vpn_user(VPN_USER_NAME, vpn_pass)
    open_vpn_firewall_rules()

    public_ip = get_public_ip()
    local_ip = get_local_ip()

    return (
        "🔐 **تم تفعيل VPN Server بنجاح!**\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📡 **بيانات الاتصال (L2TP/IPsec):**\n\n"
        f"🌐 **Server (إنترنت):** `{public_ip}`\n"
        f"🏠 **Server (شبكة محلية):** `{local_ip}`\n"
        f"🔑 **Pre-Shared Key:** `{psk}`\n"
        f"👤 **Username:** `{VPN_USER_NAME}`\n"
        f"🔒 **Password:** `{vpn_pass}`\n"
        f"🔀 **Protocol:** L2TP/IPsec\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚠️ **ملاحظة مهمة:**\n"
        "يجب فتح المنافذ في الراوتر:\n"
        "• UDP 500 (IKE)\n"
        "• UDP 4500 (IPsec NAT-T)\n"
        "• UDP 1701 (L2TP)\n\n"
        "📱 **كيفية الاتصال:**\n"
        "**iOS/Android:** إعدادات ← VPN ← إضافة ← L2TP\n"
        "**Windows:** شبكة ← VPN ← إضافة اتصال VPN\n\n"
        "💡 بعد الاتصال ستحصل على وصول كامل للشبكة المنزلية!"
    )


def disable_vpn_server() -> str:
    """Disable VPN server and clean up."""
    if not IS_WINDOWS:
        return "❌ هذه الميزة لويندوز فقط"

    disable_rras()
    delete_vpn_user(VPN_USER_NAME)
    close_vpn_firewall_rules()

    return (
        "⏹ **تم إيقاف VPN Server**\n\n"
        "✅ تم إيقاف RRAS\n"
        "✅ تم حذف مستخدم VPN\n"
        "✅ تم إغلاق منافذ Firewall"
    )


def get_vpn_status() -> str:
    """Return current VPN server status."""
    if not IS_WINDOWS:
        return "❌ هذه الميزة لويندوز فقط"

    rras = get_rras_status()
    public_ip = get_public_ip()
    local_ip = get_local_ip()
    status_icon = "🟢" if rras == "running" else "🔴"

    rc, out, _ = _run(["netsh", "ras", "show", "activeconn"])
    clients = out if out and "Username" in out else "لا يوجد اتصالات نشطة"

    return (
        f"{status_icon} **حالة VPN Server:**\n\n"
        f"📡 RRAS: `{rras}`\n"
        f"🌐 IP العام: `{public_ip}`\n"
        f"🏠 IP المحلي: `{local_ip}`\n\n"
        f"👥 **الاتصالات النشطة:**\n`{clients[:300]}`\n\n"
        "الأوامر المتاحة:\n"
        "• `vpn_server_enable` — تفعيل\n"
        "• `vpn_server_disable` — إيقاف\n"
        "• `vpn_client_connect` — اتصال كعميل\n"
        "• `vpn_client_disconnect` — قطع الاتصال"
    )


def add_vpn_client_profile(
    name: str,
    server: str,
    psk: str,
    username: str,
    tunnel_type: str = "L2tp"
) -> str:
    """
    Add a VPN CLIENT connection profile on this PC.
    Password is intentionally omitted — set it locally via Windows VPN settings.
    """
    script = f"""
Add-VpnConnection `
  -Name "{name}" `
  -ServerAddress "{server}" `
  -TunnelType {tunnel_type} `
  -L2tpPsk "{psk}" `
  -EncryptionLevel Required `
  -AuthenticationMethod MSChapv2 `
  -RememberCredential `
  -Force
"""
    rc, out = _run_ps(script)
    if rc == 0:
        return (
            f"✅ تم إضافة اتصال VPN: `{name}` → `{server}`\n\n"
            "⚠️ لأسباب أمنية، كلمة المرور لا تُرسَل عبر تيليغرام.\n"
            "افتح إعدادات VPN على الجهاز مباشرةً لإدخالها."
        )
    return f"❌ فشل إضافة اتصال VPN:\n`{out[:300]}`"


def connect_vpn_client(name: str) -> str:
    """Connect to an existing VPN client profile."""
    rc, out, err = _run(["rasdial", name])
    if rc == 0:
        return f"✅ تم الاتصال بـ VPN: `{name}`"
    return f"❌ فشل الاتصال:\n`{(out + err)[:300]}`"


def disconnect_vpn_client(name: str) -> str:
    """Disconnect from a VPN client profile."""
    rc, out, err = _run(["rasdial", name, "/disconnect"])
    return f"✅ تم قطع الاتصال: `{name}`" if rc == 0 else f"❌ {out or err}"


def list_vpn_profiles() -> str:
    """List all VPN connection profiles on this PC."""
    rc, out = _run_ps(
        "Get-VpnConnection | Select-Object Name,ServerAddress,TunnelType,ConnectionStatus "
        "| Format-Table -AutoSize | Out-String"
    )
    if rc == 0 and out.strip():
        return f"📋 **اتصالات VPN المحفوظة:**\n```\n{out[:800]}\n```"
    return "📭 لا توجد اتصالات VPN محفوظة"
