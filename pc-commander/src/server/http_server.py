import time
import threading
from flask import Flask, request, jsonify
import logging
from src.utils.logger import get_logger

log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)

logger = get_logger()
app = Flask(__name__)
_command_handler = None
_secret_token = None
_telegram_webhook_callback = None
_rate_limits: dict = {}
_rate_lock = threading.Lock()

RATE_LIMIT_MAX = 60
RATE_WINDOW    = 60


def _cleanup_rate_limits():
    """Periodically evict IPs whose rate-limit windows have fully expired."""
    while True:
        time.sleep(300)
        with _rate_lock:
            now = time.time()
            stale = [ip for ip, events in list(_rate_limits.items())
                     if not any(now - t < RATE_WINDOW for t in events)]
            for ip in stale:
                del _rate_limits[ip]


threading.Thread(target=_cleanup_rate_limits, daemon=True,
                 name="RateLimitCleanup").start()


def set_command_handler(handler):
    global _command_handler
    _command_handler = handler


def set_secret_token(token: str):
    global _secret_token
    _secret_token = token


def register_telegram_webhook(callback):
    """Register a callback that receives raw Telegram update dicts from /webhook."""
    global _telegram_webhook_callback
    _telegram_webhook_callback = callback


def _is_rate_limited(client_ip: str) -> bool:
    with _rate_lock:
        now = time.time()
        events = [t for t in _rate_limits.get(client_ip, []) if now - t < RATE_WINDOW]
        _rate_limits[client_ip] = events
        if len(events) >= RATE_LIMIT_MAX:
            return True
        _rate_limits[client_ip] = events + [now]
        return False


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "app": "NexAgent"})


@app.route("/webhook", methods=["POST"])
def telegram_webhook():
    """Receive Telegram webhook updates and forward to the registered bot callback."""
    if _telegram_webhook_callback is None:
        return jsonify({"error": "Webhook not registered"}), 503
    data = request.get_json(force=True, silent=True) or {}
    try:
        _telegram_webhook_callback(data)
    except Exception as e:
        logger.error(f"Webhook callback error: {e}")
        return jsonify({"error": str(e)}), 500
    return jsonify({"ok": True})


@app.route("/command", methods=["POST"])
def execute_command():
    client_ip = request.remote_addr or "unknown"

    if _is_rate_limited(client_ip):
        return jsonify({"error": "Rate limit exceeded"}), 429

    token = request.headers.get("X-Auth-Token", "")
    if _secret_token and token != _secret_token:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True)
    if not data or "command" not in data:
        return jsonify({"error": "Invalid request"}), 400

    if _command_handler:
        result = _command_handler(data["command"], data.get("args", []))
        return jsonify({"result": result})
    return jsonify({"error": "No handler"}), 500


def start_server(port: int = 5000, lan_access: bool = False):
    import werkzeug.serving
    host = "0.0.0.0" if lan_access else "127.0.0.1"
    server = werkzeug.serving.make_server(host, port, app, threaded=True)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    access_note = f"LAN access ON ({host}:{port})" if lan_access else f"localhost only ({host}:{port})"
    logger.info(f"HTTP server started — {access_note}")
    return t
