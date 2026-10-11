import base64
import hashlib
import hmac
import json
import os
import secrets
import threading
import time
from flask import abort, g, request

sessions = {}
attempts = {}
lock = threading.RLock()

def authenticate(username, password, ip):
    if not isinstance(username, str) or not isinstance(password, str) or len(password) > 1024:
        return None
    now = time.time()
    with lock:
        for key, value in list(attempts.items()):
            if now - value[0] > 60:
                del attempts[key]
        for key, value in list(sessions.items()):
            if value["expires"] <= now:
                del sessions[key]
        if len(attempts) >= 10000 or len(sessions) >= 10000:
            return None
        attempt = attempts.setdefault(ip, [now, 0])
        attempt[1] += 1
        if attempt[1] > 10:
            return None
    try:
        with open(os.environ["APP_USERS_FILE"], encoding="utf-8") as source:
            accounts = json.load(source)
        account = next((item for item in accounts if item["username"] == username), None)
        if not account or account["role"] not in ("admin", "staff"):
            return None
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), base64.b64decode(account["salt"], validate=True), 310000)
        if not hmac.compare_digest(actual, base64.b64decode(account["hash"], validate=True)):
            return None
    except (KeyError, ValueError, OSError, TypeError):
        return None
    token = secrets.token_urlsafe(32)
    with lock:
        sessions[token] = {"id": account["id"], "role": account["role"], "expires": now + 28800}
    return {"success": True, "token": token, "role": account["role"]}

def require_session():
    if request.method == "OPTIONS" or request.path == "/userLogin":
        return
    token = request.headers.get("Authorization", "").removeprefix("Bearer ")
    with lock:
        session = sessions.get(token)
    if not session or session["expires"] <= time.time():
        abort(401)
    g.user = session

def admin():
    if g.user["role"] != "admin":
        abort(403)
