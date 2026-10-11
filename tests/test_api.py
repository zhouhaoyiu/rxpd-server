import sqlite3
import time
import pytest
from main import create_app
from security import sessions
from workapi import FIELDS

@pytest.fixture
def client(tmp_path):
    database = tmp_path / "test.db"
    connection = sqlite3.connect(database)
    connection.execute("CREATE TABLE person(personId INTEGER PRIMARY KEY AUTOINCREMENT, personName TEXT, personWx TEXT, active INTEGER DEFAULT 1)")
    fields = ",".join(name + " TEXT" for name in FIELDS)
    connection.execute("CREATE TABLE work(workId INTEGER PRIMARY KEY AUTOINCREMENT, workIdentifier TEXT UNIQUE," + fields + ",createTime TEXT,version INTEGER,archived INTEGER)")
    connection.execute("CREATE TABLE work_history(historyId INTEGER PRIMARY KEY AUTOINCREMENT, workIdentifier TEXT,action TEXT,actor TEXT,beforeData TEXT,afterData TEXT,reason TEXT,createdAt TEXT)")
    connection.commit()
    connection.close()
    sessions["test-admin"] = {"id": "admin", "role": "admin", "expires": time.time() + 60}
    sessions["test-staff"] = {"id": "staff", "role": "staff", "expires": time.time() + 60}
    app = create_app({"TESTING": True, "TEST_DATABASE": str(database)})
    yield app.test_client()
    sessions.clear()

AUTH = {"Authorization": "Bearer test-admin"}

def test_auth_required(client):
    assert client.get("/getPersonList").status_code == 401
    assert client.post("/deleteWork", json={}).status_code == 401

def test_create_returns_id_and_normal_get_works(client):
    result = client.post("/addPerson", json={"personInfo": {"personName": "Test", "personWx": "test"}}, headers=AUTH)
    assert result.status_code == 200
    person = result.json["data"]
    assert person["personId"] > 0
    assert client.get("/getPersonByPersonId", query_string={"personId": person["personId"]}, headers=AUTH).json["data"] == person
    assert client.get("/getPersonByPersonId", headers=AUTH).status_code == 400

def test_staff_cannot_manage_people(client):
    result = client.post("/addPerson", json={"personInfo": {"personName": "Test", "personWx": "test"}}, headers={"Authorization": "Bearer test-staff"})
    assert result.status_code == 403

def create_work(client):
    return client.post("/createWork", json={"workIdentifier": "TEST-01", "workContent": "Test repair", "workAddress": "Test location", "status": "待接单"}, headers=AUTH)

def test_duplicate_work_never_inserts_twice(client):
    assert create_work(client).status_code == 200
    assert create_work(client).status_code == 409
    assert len(client.get("/getWorkList", headers=AUTH).json) == 1

def test_version_conflict_preserves_first_change(client):
    work = create_work(client).json["data"]
    work["status"] = "待到场"
    first = client.post("/changeWork", json={"workData": work, "reason": "Assigned"}, headers=AUTH)
    assert first.status_code == 200
    assert first.json["data"]["version"] == 2
    assert client.post("/changeWork", json={"workData": work, "reason": "Old edit"}, headers=AUTH).status_code == 409
    history = client.get("/workHistory?workIdentifier=TEST-01", headers=AUTH).json
    assert len(history) == 2

def test_status_cannot_skip_stages(client):
    work = create_work(client).json["data"]
    work["status"] = "已完成"
    assert client.post("/changeWork", json={"workData": work, "reason": "Skip"}, headers=AUTH).status_code == 409

def test_archive_preserves_history(client):
    work = create_work(client).json["data"]
    result = client.post("/deleteWork", json={"workIdentifier": "TEST-01", "version": work["version"], "reason": "Duplicate intake"}, headers=AUTH)
    assert result.status_code == 200
    assert client.get("/getWorkList", headers=AUTH).json == []
    assert len(client.get("/workHistory?workIdentifier=TEST-01", headers=AUTH).json) == 2
