import json
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, abort, g
from mysqlconfig import query, execute, transaction
from security import admin

work_api = Blueprint("work_api", __name__)
FIELDS = ("workType", "workSource", "workContent", "contactPerson", "contactPhone",
          "workAddress", "householdNumber", "waterMeterNumber", "arrivalTimeLimit",
          "completionTimeLimit", "workArea", "waterUseNature", "workMode",
          "callerPhone", "fileNo", "label", "remark", "status", "assignee")
TRANSITIONS = {
    "待接单": {"待到场", "已挂起", "已终止", "已作废"},
    "待到场": {"待处理", "已挂起", "已终止"},
    "待处理": {"待回访", "已挂起", "已终止"},
    "待回访": {"已完成", "待处理"},
    "已挂起": {"待接单", "待到场", "待处理", "已终止"},
    "已完成": {"待处理"}, "已终止": set(), "已作废": set(),
}

def clean(data):
    if not isinstance(data, dict):
        abort(400, "工单格式错误")
    identifier = data.get("workIdentifier")
    if not isinstance(identifier, str) or not identifier.strip() or len(identifier) > 128:
        abort(400, "工单编号错误")
    result = {key: data.get(key, "") for key in FIELDS}
    if any(not isinstance(value, str) or len(value) > 10000 for value in result.values()):
        abort(400, "字段格式错误")
    if not result["workContent"].strip() or not result["workAddress"].strip():
        abort(400, "请填写工单内容与地址")
    if result["status"] not in TRANSITIONS:
        abort(400, "工单状态错误")
    if result["assignee"]:
        try:
            person = json.loads(result["assignee"])
            identifier_person = person["id"]
        except (ValueError, TypeError, KeyError):
            abort(400, "请重新选择处理人员")
        matches = query("SELECT personId,personName,personWx FROM person WHERE personId=%s AND active=1", (identifier_person,))
        if not matches:
            abort(400, "处理人员已停用")
        person = matches[0]
        result["assignee"] = json.dumps({"id": person["personId"], "name": person["personName"], "wx": person["personWx"]}, ensure_ascii=False)
    return identifier.strip(), result

def audit(identifier, action, before, after, reason):
    execute("INSERT INTO work_history (workIdentifier,action,actor,beforeData,afterData,reason,createdAt) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (identifier, action, g.user["id"], json.dumps(before, ensure_ascii=False, default=str),
             json.dumps(after, ensure_ascii=False, default=str), reason, datetime.now(timezone.utc).isoformat()))

@work_api.get("/getWorkList")
def get_work_list():
    return jsonify(query("SELECT * FROM work WHERE archived=0 ORDER BY workId DESC"))

@work_api.post("/getWorkDetail")
def get_work_detail():
    data = request.get_json()
    if not isinstance(data, dict) or not data.get("workIdentifier"):
        abort(400, "缺少工单编号")
    rows = query("SELECT * FROM work WHERE workIdentifier=%s AND archived=0", (data["workIdentifier"],))
    if not rows:
        abort(404, "工单不存在")
    return jsonify(rows)

@work_api.get("/workHistory")
def history():
    return jsonify(query("SELECT action,actor,reason,createdAt FROM work_history WHERE workIdentifier=%s ORDER BY historyId DESC", (request.args.get("workIdentifier", ""),)))

@work_api.post("/createWork")
def create_work():
    identifier, data = clean(request.get_json())
    if data["status"] != "待接单":
        abort(400, "新工单必须为待接单")
    with transaction():
        if query("SELECT workIdentifier FROM work WHERE workIdentifier=%s", (identifier,)):
            abort(409, "工单编号已存在，请查看原工单")
        fields = ("workIdentifier",) + FIELDS + ("createTime", "version", "archived")
        values = (identifier,) + tuple(data[key] for key in FIELDS) + (datetime.now(timezone.utc).isoformat(), 1, 0)
        execute("INSERT INTO work (" + ",".join(fields) + ") VALUES (" + ",".join(["%s"] * len(fields)) + ")", values)
        audit(identifier, "创建", None, data, "")
        result = query("SELECT * FROM work WHERE workIdentifier=%s", (identifier,))[0]
    return jsonify(success=True, data=result)

@work_api.post("/changeWork")
def change_work():
    body = request.get_json()
    if not isinstance(body, dict):
        abort(400)
    incoming = body.get("workData")
    identifier, data = clean(incoming)
    reason = body.get("reason", "")
    if not isinstance(reason, str):
        abort(400, "变更原因格式错误")
    reason = reason.strip()
    if len(reason) > 2000:
        abort(400, "说明过长")
    version = incoming.get("version")
    if not isinstance(version, int):
        abort(400, "缺少记录版本，请刷新")
    with transaction():
        rows = query("SELECT * FROM work WHERE workIdentifier=%s AND archived=0", (identifier,))
        if not rows:
            abort(404)
        previous = rows[0]
        if previous["version"] != version:
            abort(409, "工单已被其他人修改，请刷新")
        changed_status = data["status"] != previous["status"]
        if changed_status and data["status"] not in TRANSITIONS.get(previous["status"], set()):
            abort(409, "不能跳过工单处理阶段")
        if previous["status"] == "已完成" and changed_status:
            admin()
        if (changed_status or data["assignee"] != previous["assignee"]) and not reason:
            abort(400, "请填写状态变更或转派原因")
        _, count = execute("UPDATE work SET " + ",".join(key + "=%s" for key in FIELDS) +
                           ",version=version+1 WHERE workIdentifier=%s AND version=%s AND archived=0",
                           tuple(data[key] for key in FIELDS) + (identifier, version))
        if count != 1:
            abort(409, "工单已被其他人修改，请刷新")
        audit(identifier, "修改", previous, data, reason)
        result = query("SELECT * FROM work WHERE workIdentifier=%s", (identifier,))[0]
    return jsonify(success=True, data=result)

@work_api.post("/deleteWork")
def delete_work():
    admin()
    data = request.get_json()
    if not isinstance(data, dict) or not data.get("reason"):
        abort(400, "请填写归档原因")
    with transaction():
        rows = query("SELECT * FROM work WHERE workIdentifier=%s AND archived=0", (data.get("workIdentifier"),))
        if not rows:
            abort(404)
        _, count = execute("UPDATE work SET archived=1,version=version+1 WHERE workIdentifier=%s AND version=%s",
                           (data["workIdentifier"], data.get("version")))
        if count != 1:
            abort(409, "工单已变更，请刷新")
        audit(data["workIdentifier"], "归档", rows[0], None, data["reason"])
    return jsonify(success=True)
