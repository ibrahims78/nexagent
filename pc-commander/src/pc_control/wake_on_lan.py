import socket
import re
from src.utils.logger import get_logger

logger = get_logger()


def send_magic_packet(mac_address: str, broadcast_ip: str = "255.255.255.255", port: int = 9) -> bool:
    mac_clean = re.sub(r"[:\-\.]", "", mac_address).upper()
    if len(mac_clean) != 12:
        raise ValueError(f"عنوان MAC غير صالح: {mac_address}")

    mac_bytes = bytes.fromhex(mac_clean)
    magic_packet = b"\xFF" * 6 + mac_bytes * 16

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(3)
            sock.sendto(magic_packet, (broadcast_ip, port))
            sock.sendto(magic_packet, (broadcast_ip, 7))
        logger.info(f"✅ تم إرسال Magic Packet إلى {mac_address}")
        return True
    except Exception as e:
        logger.error(f"❌ فشل إرسال Magic Packet: {e}")
        return False


def get_local_broadcast() -> str:
    try:
        import netifaces
        for iface in netifaces.interfaces():
            addrs = netifaces.ifaddresses(iface)
            if netifaces.AF_INET in addrs:
                for addr in addrs[netifaces.AF_INET]:
                    if "broadcast" in addr and not addr["addr"].startswith("127."):
                        return addr["broadcast"]
    except Exception:
        pass
    return "255.255.255.255"


def validate_mac(mac: str) -> bool:
    pattern = r"^([0-9A-Fa-f]{2}[:\-\.]){5}([0-9A-Fa-f]{2})$"
    return bool(re.match(pattern, mac))


def get_pc_mac_windows() -> str:
    try:
        import subprocess
        result = subprocess.run(
            ["powershell", "-Command",
             "Get-NetAdapter | Where-Object {$_.Status -eq 'Up' -and $_.InterfaceDescription -notlike '*Virtual*'} | Select-Object -First 1 -ExpandProperty MacAddress"],
            capture_output=True, text=True, timeout=5
        )
        mac = result.stdout.strip()
        if mac:
            return mac.replace("-", ":")
    except Exception:
        pass

    try:
        import uuid
        mac_int = uuid.getnode()
        mac_hex = f"{mac_int:012x}"
        return ":".join(mac_hex[i:i+2] for i in range(0, 12, 2))
    except Exception:
        return ""


def wol_command(config: dict) -> str:
    wol_config = config.get("wol", {})
    mac = wol_config.get("mac_address", "")
    broadcast = wol_config.get("broadcast_ip", "255.255.255.255")

    if not mac:
        return "❌ عنوان MAC غير مضبوط. اذهب للإعدادات وأضف MAC Address للحاسب."

    if not validate_mac(mac):
        return f"❌ عنوان MAC غير صالح: {mac}"

    success = send_magic_packet(mac, broadcast)
    if success:
        return (
            "📡 **تم إرسال إشارة الإيقاظ (Magic Packet)**\n\n"
            f"🖥️ MAC: `{mac}`\n"
            "⏳ الحاسب يحتاج 30-60 ثانية للإقلاع\n"
            "💡 سأرسل لك إشعاراً عندما يكون جاهزاً"
        )
    return "❌ فشل إرسال إشارة الإيقاظ. تأكد من الإعدادات."
