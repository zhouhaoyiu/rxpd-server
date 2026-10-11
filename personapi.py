from flask import Blueprint, request, jsonify, abort
from mysqlconfig import query, execute, transaction
from security import admin

person_api = Blueprint("person_api", __name__)

def person_input():
    body = request.get_json()
    data = body.get("personInfo") if isinstance(body, dict) else None
    if not isinstance(data, dict):
        abort(400, "人员资料格式错误")
    for field in ("personName", "personWx"):
        if not isinstance(data.get(field), str) or not data[field].strip() or len(data[field]) > 128:
            abort(400, "请填写姓名与联系标识")
    return data

@person_api.get("/getPersonList")
def get_people():
    return jsonify(query("SELECT personId,personName,personWx FROM person WHERE active = 1 ORDER BY personId"))

@person_api.post("/addPerson")
def add_person():
    admin()
    data = person_input()
    with transaction():
        identifier, _ = execute("INSERT INTO person (personName,personWx,active) VALUES (%s,%s,1)",
                                (data["personName"].strip(), data["personWx"].strip()))
        person = query("SELECT personId,personName,personWx FROM person WHERE personId = %s", (identifier,))[0]
    return jsonify(success=True, data=person)

@person_api.post("/changePerson")
def change_person():
    admin()
    data = person_input()
    if not data.get("personId"):
        abort(400, "缺少人员编号")
    with transaction():
        if not query("SELECT personId FROM person WHERE personId = %s AND active = 1", (data["personId"],)):
            abort(404, "人员不存在")
        execute("UPDATE person SET personName=%s,personWx=%s WHERE personId=%s",
                (data["personName"].strip(), data["personWx"].strip(), data["personId"]))
        person = query("SELECT personId,personName,personWx FROM person WHERE personId=%s", (data["personId"],))[0]
    return jsonify(success=True, data=person)

@person_api.post("/deletePerson")
def delete_person():
    admin()
    data = request.get_json()
    if not isinstance(data, dict) or not data.get("personId"):
        abort(400, "缺少人员编号")
    with transaction():
        _, count = execute("UPDATE person SET active=0 WHERE personId=%s AND active=1", (data["personId"],))
        if count != 1:
            abort(404, "人员不存在")
    return jsonify(success=True)

@person_api.get("/getPersonByPersonId")
def get_person():
    identifier = request.args.get("personId")
    if not identifier:
        abort(400, "缺少人员编号")
    rows = query("SELECT personId,personName,personWx FROM person WHERE personId=%s AND active=1", (identifier,))
    if not rows:
        abort(404, "人员不存在")
    return jsonify(success=True, data=rows[0])
