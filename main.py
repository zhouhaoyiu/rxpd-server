import json
from flask import Flask
from flask_cors import CORS

from adminapi import admin_api
from mysqlconfig import mydb
from personapi import person_api
from workapi import work_api
from gevent import pywsgi

app = Flask(__name__)
app.config.from_object(__name__)

CORS(app, supports_credentials=True)

app.register_blueprint(work_api)
app.register_blueprint(person_api)
app.register_blueprint(admin_api)


@app.route('/getPersonList', methods=['GET'])
def getPersonList():
    cursor = mydb.cursor()
    cursor.execute("SELECT * FROM person")
    domain = cursor.description
    result = []
    for row in cursor.fetchall():
        result.append(dict(zip([col[0] for col in domain], row)))

    return json.dumps(result, ensure_ascii=False)


if __name__ == '__main__':
    app.config['JSON_AS_ASCII'] = False
    server = pywsgi.WSGIServer(('0.0.0.0', 5000), app)
    server.serve_forever()
