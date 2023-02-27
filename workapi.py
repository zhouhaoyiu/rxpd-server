from flask import Blueprint, request
import json

from mysqlconfig import mydb

work_api = Blueprint('work_api', __name__)


@work_api.route('/getWorkList', methods=['GET'])
def getWorkList():
    cursor = mydb.cursor()
    # cursor.execute("SELECT * FROM work")
    # 从旧到新排序
    cursor.execute("SELECT * FROM work ORDER BY workId DESC")
    domain = cursor.description
    result = []
    for row in cursor.fetchall():
        result.append(dict(zip([col[0] for col in domain], row)))

    return json.dumps(result, ensure_ascii=False)


@work_api.route('/getWorkDetail', methods=['POST'])
def getWorkDetail():
    data = json.loads(request.get_data())
    workIdentifier = data['workIdentifier']
    cursor = mydb.cursor()
    cursor.execute(
        "SELECT * FROM work WHERE workIdentifier = %s", (workIdentifier,))
    domain = cursor.description
    result = []
    for row in cursor.fetchall():
        result.append(dict(zip([col[0] for col in domain], row)))

    return json.dumps(result, ensure_ascii=False)


@work_api.route('/deleteWork', methods=['POST'])
def deleteWork():
    data = json.loads(request.get_data())
    print(data)
    workIdentifier = data['workIdentifier']
    cursor = mydb.cursor()
    cursor.execute("DELETE FROM work WHERE workIdentifier = %s",
                   (workIdentifier,))
    mydb.commit()

    return json.dumps({'success': True}, ensure_ascii=False)


@work_api.route('/createWork', methods=['POST'])
def createWork():
    data = json.loads(request.get_data())

    workIdentifier = data['workIdentifier']
    workType = data['workType']
    workSource = data['workSource']
    workContent = data['workContent']
    contactPerson = data['contactPerson']
    contactPhone = data['contactPhone']
    workAddress = data['workAddress']
    householdNumber = data['householdNumber']
    waterMeterNumber = data['waterMeterNumber']
    arrivalTimeLimit = data['arrivalTimeLimit']
    completionTimeLimit = data['completionTimeLimit']
    workArea = data['workArea']
    waterUseNature = data['waterUseNature']
    workMode = data['workMode']
    callerPhone = data['callerPhone']
    fileNo = data['fileNo']
    label = data['label']
    remark = data['remark']
    status = data['status']
    assignee = data['assignee']
    createTime = data['createTime']

    cursor = mydb.cursor()
    sql = "INSERT INTO work (workIdentifier, workType, workSource, workContent, contactPerson, contactPhone, " \
          "workAddress, householdNumber, waterMeterNumber, arrivalTimeLimit, completionTimeLimit, workArea, " \
          "waterUseNature, workMode, callerPhone, fileNo, label, remark, status, assignee, createTime) VALUES (%s, " \
          "%s, %s, " \
          "%s, %s, %s, %s, %s, " \
          "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    val = (workIdentifier, workType, workSource, workContent, contactPerson, contactPhone, workAddress,
           householdNumber, waterMeterNumber, arrivalTimeLimit, completionTimeLimit, workArea, waterUseNature, workMode,
           callerPhone, fileNo, label, remark, status, assignee, createTime)
    cursor.execute(sql, val)
    mydb.commit()

    return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}


@work_api.route('/changeWork', methods=['POST'])
def changeWork():
    Sdata = json.loads(request.get_data())
    data = Sdata['workData']

    workIdentifier = data['workIdentifier']
    workType = data['workType']
    workSource = data['workSource']
    workContent = data['workContent']
    contactPerson = data['contactPerson']
    contactPhone = data['contactPhone']
    workAddress = data['workAddress']
    householdNumber = data['householdNumber']
    waterMeterNumber = data['waterMeterNumber']
    arrivalTimeLimit = data['arrivalTimeLimit']
    completionTimeLimit = data['completionTimeLimit']
    workArea = data['workArea']
    waterUseNature = data['waterUseNature']
    workMode = data['workMode']
    callerPhone = data['callerPhone']
    fileNo = data['fileNo']
    label = data['label']
    remark = data['remark']
    status = data['status']
    assignee = data['assignee']

    cursor = mydb.cursor()
    sql = "UPDATE work SET workType = %s, workSource = %s, workContent = %s, contactPerson = %s, contactPhone = %s, " \
          "workAddress = %s, householdNumber = %s, waterMeterNumber = %s, arrivalTimeLimit = %s, " \
          "completionTimeLimit = %s, workArea = %s, waterUseNature = %s, workMode = %s, callerPhone = %s, " \
          "fileNo = %s, label = %s, remark = %s, status = %s, assignee = %s WHERE workIdentifier = %s"
    val = (workType, workSource, workContent, contactPerson, contactPhone, workAddress,
           householdNumber, waterMeterNumber, arrivalTimeLimit, completionTimeLimit, workArea, waterUseNature, workMode,
           callerPhone, fileNo, label, remark, status, assignee, workIdentifier)
    cursor.execute(sql, val)
    mydb.commit()

    return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
