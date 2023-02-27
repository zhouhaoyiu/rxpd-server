from flask import Blueprint, request
import json

from mysqlconfig import mydb

person_api = Blueprint('person_api', __name__)


@person_api.route('/addPerson', methods=['POST'])
def addPerson():
    data = json.loads(request.get_data())
    personInfo = data['personInfo']
    personName = personInfo['personName']
    personWx = personInfo['personWx']

    cursor = mydb.cursor()
    cursor.execute("INSERT INTO person (personName, personWx) VALUES (%s, %s)",
                   (personName, personWx))

    mydb.commit()
    return json.dumps({'success': True}, ensure_ascii=False)


@person_api.route('/changePerson', methods=['POST'])
def changePerson():
    data = json.loads(request.get_data())
    personInfo = data['personInfo']
    personId = personInfo['personId']
    personName = personInfo['personName']
    personWx = personInfo['personWx']

    cursor = mydb.cursor()
    cursor.execute("UPDATE person SET personName = %s, personWx = %s WHERE personId = %s",
                   (personName, personWx, personId))

    mydb.commit()
    return json.dumps({'success': True}, ensure_ascii=False)


@person_api.route('/deletePerson', methods=['POST'])
def deletePerson():
    data = json.loads(request.get_data())
    personId = data['personId']

    cursor = mydb.cursor()
    cursor.execute("DELETE FROM person WHERE personId = %s", (personId,))

    mydb.commit()
    return json.dumps({'success': True}, ensure_ascii=False)


@person_api.route('/getPersonByPersonId', methods=['GET'])
def getPerson():
    data = json.loads(request.get_data())
    personId = request.args.get('personId')
    cursor = mydb.cursor()
    cursor.execute("SELECT * FROM person WHERE personId = %s", (personId,))
    domain = cursor.description
    result = []
    for row in cursor.fetchall():
        result.append(dict(zip([col[0] for col in domain], row)))

    return json.dumps({'success': True}, result, ensure_ascii=False)
