import base64
import hashlib
import json
import sqlite3
import pytest
from local_database import initialize_database
from main import create_app
from security import attempts, sessions


@pytest.fixture
def local_app(tmp_path, monkeypatch):
    database = initialize_database(tmp_path / "dispatch.db")
    salt = b"local-runtime-test"
    account = {
        "username": "fixture-admin", "id": "fixture-admin", "role": "admin",
        "salt": base64.b64encode(salt).decode(),
        "hash": base64.b64encode(hashlib.pbkdf2_hmac("sha256", b"test-password-123", salt, 310000)).decode(),
    }
    accounts = tmp_path / "accounts.json"
    accounts.write_text(json.dumps([account]), encoding="utf-8")
    monkeypatch.setenv("APP_SQLITE_PATH", str(database))
    monkeypatch.setenv("APP_USERS_FILE", str(accounts))
    for name in ("DB_USER", "DB_PASSWORD", "DB_NAME"):
        monkeypatch.delenv(name, raising=False)
    sessions.clear()
    attempts.clear()
    app = create_app()
    assert app.testing is False
    yield app, database
    sessions.clear()
    attempts.clear()


def login(client):
    response = client.post("/userLogin", json={"username": "fixture-admin", "password": "test-password-123"})
    assert response.status_code == 200
    assert response.json["role"] == "admin"
    return {"Authorization": "Bearer " + response.json["token"]}


def test_local_auth_and_logout_are_not_bypassed(local_app):
    app, _ = local_app
    client = app.test_client()
    assert client.get("/getWorkList").status_code == 401
    assert client.post("/userLogin", json={"username": "fixture-admin", "password": "wrong"}).status_code == 401
    auth = login(client)
    assert client.get("/getWorkList", headers=auth).json == []
    assert client.post("/logout", headers=auth).status_code == 200
    assert client.get("/getWorkList", headers=auth).status_code == 401


def test_local_workflow_persists_after_app_recreation(local_app):
    app, database = local_app
    client = app.test_client()
    auth = login(client)
    person = client.post("/addPerson", json={"personInfo": {"personName": "Demo", "personWx": "demo-only"}}, headers=auth).json["data"]
    work = {"workIdentifier": "LOCAL-01", "workContent": "Demo only", "workAddress": "Demo location", "status": "待接单",
            "assignee": json.dumps({"id": person["personId"]})}
    created = client.post("/createWork", json=work, headers=auth)
    assert created.status_code == 200
    assert client.post("/createWork", json=work, headers=auth).status_code == 409
    work = created.json["data"]
    work["status"] = "待到场"
    assert client.post("/changeWork", json={"workData": work, "reason": "Demo assignment"}, headers=auth).status_code == 200
    assert client.post("/changeWork", json={"workData": work, "reason": "Stale version"}, headers=auth).status_code == 409
    initialize_database(database)
    sessions.clear()
    restarted = create_app().test_client()
    assert restarted.get("/getWorkList", headers=auth).status_code == 401
    auth = login(restarted)
    rows = restarted.get("/getWorkList", headers=auth).json
    assert len(rows) == 1 and rows[0]["version"] == 2 and rows[0]["status"] == "待到场"
    assert len(restarted.get("/workHistory?workIdentifier=LOCAL-01", headers=auth).json) == 2
    assert restarted.post("/deleteWork", json={"workIdentifier": "LOCAL-01", "version": 2, "reason": "Demo archive"}, headers=auth).status_code == 200
    assert restarted.get("/getWorkList", headers=auth).json == []
    assert len(restarted.get("/workHistory?workIdentifier=LOCAL-01", headers=auth).json) == 3


def test_initializer_refuses_unrecognized_database(tmp_path):
    database = tmp_path / "existing.db"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE unrelated(value TEXT)")
        connection.execute("INSERT INTO unrelated VALUES ('keep')")
    with pytest.raises(ValueError):
        initialize_database(database)
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT value FROM unrelated").fetchall() == [("keep",)]


def test_missing_database_is_not_silently_created(tmp_path):
    database = tmp_path / "missing.db"
    client = create_app({"SQLITE_DATABASE": str(database)}).test_client()
    from mysqlconfig import get_db
    with client.application.app_context(), pytest.raises(sqlite3.OperationalError):
        get_db()
    assert not database.exists()
