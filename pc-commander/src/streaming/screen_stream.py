"""
PC Commander - Screen Stream Server
بث الشاشة الحي عبر MJPEG - يمكن فتحه من أي متصفح
"""
import io
import time
import threading
import hashlib
import secrets

_cleanup_thread_started = False
_cleanup_thread_lock = threading.Lock()

try:
    from flask import Flask, Response, request, abort, render_template_string
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

try:
    from PIL import ImageGrab
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from src.utils.logger import get_logger

logger = get_logger()

_stream_server = None
_stream_thread = None
_server_lock   = threading.Lock()

HTML_VIEWER = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PC Commander - بث الشاشة</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #0d0d1a; color: #eee; font-family: 'Segoe UI', sans-serif; }
  .header {
    background: #1a1a2e; padding: 12px 20px; display: flex;
    align-items: center; justify-content: space-between;
    border-bottom: 2px solid #7c4dff;
  }
  .logo { font-size: 18px; font-weight: bold; color: #7c4dff; }
  .status {
    display: flex; align-items: center; gap: 8px;
    font-size: 13px; color: #aaa;
  }
  .dot { width: 8px; height: 8px; border-radius: 50%; background: #66bb6a;
         animation: pulse 1.5s infinite; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }
  .screen-wrap {
    display: flex; justify-content: center; align-items: flex-start;
    padding: 16px; min-height: calc(100vh - 60px);
  }
  .screen-img {
    max-width: 100%; border-radius: 8px;
    border: 2px solid #333; box-shadow: 0 4px 30px rgba(124,77,255,.3);
  }
  .info { position: fixed; bottom: 12px; right: 12px;
          background: rgba(0,0,0,.6); padding: 6px 12px;
          border-radius: 20px; font-size: 11px; color: #666; }
</style>
</head>
<body>
<div class="header">
  <div class="logo">🖥️ PC Commander</div>
  <div class="status"><div class="dot"></div> بث مباشر</div>
</div>
<div class="screen-wrap">
  <img src="/stream" class="screen-img" alt="شاشة الحاسب">
</div>
<div class="info">PC Commander &copy; 2024</div>
</body>
</html>"""

HTML_LOGIN = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<title>PC Commander - تسجيل الدخول</title>
<style>
  body { background: #0d0d1a; color: #eee; font-family: 'Segoe UI', sans-serif;
         display: flex; align-items: center; justify-content: center; min-height: 100vh; }
  .card { background: #1a1a2e; padding: 40px; border-radius: 16px;
          border: 1px solid #333; width: 320px; text-align: center; }
  h2 { color: #7c4dff; margin-bottom: 24px; }
  input { width: 100%; padding: 10px 14px; background: #0d0d1a; border: 1px solid #444;
          border-radius: 8px; color: #eee; font-size: 14px; margin-bottom: 16px; }
  button { width: 100%; padding: 11px; background: #7c4dff; color: #fff;
           border: none; border-radius: 8px; font-size: 15px; cursor: pointer; }
  button:hover { background: #651fff; }
  .err { color: #ef5350; font-size: 13px; margin-top: 10px; }
</style>
</head>
<body>
<div class="card">
  <h2>🔒 PC Commander</h2>
  <form method="POST">
    <input type="password" name="password" placeholder="كلمة المرور" autofocus>
    <button type="submit">دخول</button>
  </form>
  {% if error %}<div class="err">❌ كلمة مرور خاطئة</div>{% endif %}
</div>
</body>
</html>"""


def _hash_password(password: str) -> str:
    return hashlib.pbkdf2_hmac(
        'sha256', password.encode(), b'nexagent-stream-v1', 200_000
    ).hex()


def _capture_frame(quality: int = 60, scale: float = 1.0) -> bytes:
    if not PIL_AVAILABLE:
        raise RuntimeError("Pillow is not installed")
    img = ImageGrab.grab()
    if scale != 1.0:
        new_w = int(img.width * scale)
        new_h = int(img.height * scale)
        img = img.resize((new_w, new_h))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    return buf.getvalue()


def _generate_stream(fps: int, quality: int, scale: float):
    delay = 1.0 / max(fps, 1)
    while True:
        try:
            frame = _capture_frame(quality, scale)
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" +
                frame +
                b"\r\n"
            )
        except Exception as e:
            logger.warning(f"Frame capture error: {e}")
        time.sleep(delay)


def create_stream_app(password_hash: str, fps: int, quality: int, scale: float) -> Flask:
    app = Flask(__name__)
    app.secret_key = secrets.token_hex(32)

    SESSION_COOKIE = "pcc_auth"
    SESSION_TTL = 86400  # 24 hours
    _active_sessions: dict = {}  # token -> expiry_timestamp

    def is_authenticated():
        token = request.cookies.get(SESSION_COOKIE)
        if not token:
            return False
        expiry = _active_sessions.get(token)
        if expiry is None:
            return False
        if time.time() > expiry:
            _active_sessions.pop(token, None)
            return False
        return True

    def logout_session(token: str):
        _active_sessions.pop(token, None)

    def _cleanup_sessions():
        now = time.time()
        expired = [t for t, exp in list(_active_sessions.items()) if now > exp]
        for t in expired:
            _active_sessions.pop(t, None)

    _cleanup_sessions()

    def _periodic_cleanup():
        while True:
            time.sleep(3600)
            _cleanup_sessions()

    global _cleanup_thread_started
    with _cleanup_thread_lock:
        if not _cleanup_thread_started:
            _cleanup_thread_started = True
            _cleanup_thread = threading.Thread(
                target=_periodic_cleanup, daemon=True, name="StreamSessionCleanup"
            )
            _cleanup_thread.start()

    @app.route("/", methods=["GET", "POST"])
    def index():
        if is_authenticated():
            return render_template_string(HTML_VIEWER)
        if request.method == "POST":
            pwd = request.form.get("password", "")
            if _hash_password(pwd) == password_hash:
                session_token = secrets.token_hex(32)
                _active_sessions[session_token] = time.time() + SESSION_TTL
                resp = Response(render_template_string(HTML_VIEWER))
                resp.set_cookie(SESSION_COOKIE, session_token, httponly=True, samesite="Strict")
                return resp
            return render_template_string(HTML_LOGIN, error=True)
        return render_template_string(HTML_LOGIN, error=False)

    @app.route("/logout", methods=["POST"])
    def logout():
        token = request.cookies.get(SESSION_COOKIE)
        if token:
            logout_session(token)
        resp = Response("", status=302, headers={"Location": "/"})
        resp.delete_cookie(SESSION_COOKIE)
        return resp

    @app.route("/stream")
    def stream():
        if not is_authenticated():
            abort(403)
        return Response(
            _generate_stream(fps, quality, scale),
            mimetype="multipart/x-mixed-replace; boundary=frame"
        )

    @app.route("/health")
    def health():
        return {"status": "ok", "service": "PC Commander Stream"}, 200

    return app


class ScreenStreamServer:
    def __init__(self, port: int, password: str, fps: int, quality: int, scale: float):
        self.port     = port
        self.fps      = fps
        self.quality  = quality
        self.scale    = scale
        self._phash   = _hash_password(password)
        self._thread  = None
        self._running = False
        self._app     = None

    def start(self) -> bool:
        if self._running:
            return True
        if not FLASK_AVAILABLE:
            raise RuntimeError("Flask is not installed — run: pip install flask")
        if not PIL_AVAILABLE:
            raise RuntimeError("Pillow is not installed — run: pip install Pillow")

        self._app = create_stream_app(self._phash, self.fps, self.quality, self.scale)

        import werkzeug.serving
        self._server = werkzeug.serving.make_server(
            "127.0.0.1", self.port, self._app, threaded=True
        )
        self._running = True
        self._thread  = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        logger.info(f"Screen stream started on port {self.port} (127.0.0.1 only)")
        return True

    def stop(self):
        if self._running and self._server:
            self._server.shutdown()
        self._running = False
        logger.info("Screen stream stopped")

    @property
    def is_running(self) -> bool:
        return self._running


def start_stream(config: dict) -> str:
    global _stream_server
    with _server_lock:
        if _stream_server and _stream_server.is_running:
            return "⚠️ البث يعمل بالفعل"

        sc       = config.get("stream", {})
        port     = int(sc.get("port", 8765))
        password = sc.get("password", "")
        fps      = int(sc.get("fps", 5))
        quality  = int(sc.get("quality", 60))
        scale    = float(sc.get("scale", 0.8))

        if not password:
            return (
                "❌ **لا يمكن تشغيل البث بدون كلمة مرور**\n\n"
                "افتح الإعدادات ← تبويب الإعدادات ← حقل كلمة مرور البث\n"
                "واضبط كلمة مرور قبل تشغيل البث."
            )

        _stream_server = ScreenStreamServer(port, password, fps, quality, scale)
        try:
            _stream_server.start()
            return f"✅ تم تشغيل البث\n🌐 متاح على المنفذ: {port}"
        except Exception as e:
            return f"❌ فشل تشغيل البث: {e}"


def stop_stream() -> str:
    global _stream_server
    with _server_lock:
        if not _stream_server or not _stream_server.is_running:
            return "⚠️ البث ليس يعمل"
        _stream_server.stop()
        _stream_server = None
        return "⏹ تم إيقاف البث"


def get_stream_status(config: dict) -> dict:
    port    = int(config.get("stream", {}).get("port", 8765))
    running = bool(_stream_server and _stream_server.is_running)
    return {"running": running, "port": port}
