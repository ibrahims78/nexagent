import time
import threading
from flask import Flask, request, jsonify
import logging

log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)

app = Flask(__name__)
_command_handler = None
_secret_token = None
_rate_limits: dict = {}
_rate_lock = threading.Lock()

RATE_LIMIT_MAX = 60
RATE_WINDOW    = 60


def set_command_handler(handler):
    global _command_handler
    _command_handler = handler


def set_secret_token(token: str):
    global _secret_token
    _secret_token = token


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


def start_server(port: int = 5000):
    import werkzeug.serving
    server = werkzeug.serving.make_server("127.0.0.1", port, app, threaded=True)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return t
