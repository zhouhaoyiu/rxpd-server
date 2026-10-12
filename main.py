import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
from mysqlconfig import close_db
from personapi import person_api
from workapi import work_api
from security import authenticate, require_session, sessions, lock

def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        MAX_CONTENT_LENGTH=1024 * 1024,
        SQLITE_DATABASE=os.environ.get("APP_SQLITE_PATH"),
    )
    if test_config:
        app.config.update(test_config)
    app.json.ensure_ascii = False
    CORS(app, origins=os.environ.get("APP_ORIGINS", "http://127.0.0.1:5196").split(","))
    app.before_request(require_session)
    app.teardown_appcontext(close_db)
    app.register_blueprint(person_api)
    app.register_blueprint(work_api)

    @app.post("/userLogin")
    def login():
        body = request.get_json()
        if not isinstance(body, dict):
            return jsonify(success=False, message="请求格式错误"), 400
        result = authenticate(body.get("username"), body.get("password"), request.remote_addr)
        return jsonify(result or {"success": False, "message": "登录失败"}), 200 if result else 401

    @app.post("/logout")
    def logout():
        with lock:
            sessions.pop(request.headers.get("Authorization", "").removeprefix("Bearer "), None)
        return jsonify(success=True)

    @app.errorhandler(HTTPException)
    def http_error(error):
        return jsonify(success=False, message=error.description), error.code

    @app.errorhandler(Exception)
    def server_error(error):
        app.logger.error("Request failed: %s", type(error).__name__)
        return jsonify(success=False, message="服务暂时不可用"), 500

    return app

app = create_app()
if __name__ == "__main__":
    from waitress import serve
    serve(app, host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", "5000")))
