from flask import Flask, request, jsonify
import threading
import sys
import logging

log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)

app = Flask(__name__)
_command_handler = None
_secret_token = None


def set_command_handler(handler):
    global _command_handler
    _command_handler = handler


def set_secret_token(token: str):
    global _secret_token
    _secret_token = token


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "app": "PC Commander"})


@app.route("/command", methods=["POST"])
def execute_command():
    global _command_handler, _secret_token
    token = request.headers.get("X-Auth-Token", "")
    if _secret_token and token != _secret_token:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    if not data or "command" not in data:
        return jsonify({"error": "Invalid request"}), 400

    if _command_handler:
        result = _command_handler(data["command"], data.get("args", []))
        return jsonify({"result": result})
    return jsonify({"error": "No handler"}), 500


def start_server(port: int = 5000):
    def run():
        app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)
    t = threading.Thread(target=run, daemon=True)
    t.start()
    return t
