import os, json
from flask import Flask, request
from cloudant.query import Query
from cloudant.document import Document
import atexit
from vcap import VCap
import redis

vcap = VCap("vcap.json")
r = vcap.initRedis()

dblink = vcap.initCloudant()
db = dblink.create_database("robots", throw_on_exists=False)

app = Flask(__name__)

def jsonify(data, status=200):
  return (json.dumps(data), status, {'Content-Type': 'application/json'})

@atexit.register
def shutdown():
    if dblink:
        dblink.disconnect()

@app.route("/")
def home():
  return "For more details, please visit https://app.swaggerhub.com/apis/pierre-imerir/SimpleRobotAPI/1.0.0"

@app.route("/exists/<docid>")
def testExists(docid):
  doc = Document(db, document_id=docid)
  return jsonify({"exists": doc.exists()})

@app.route("/robots", methods=['GET'])
def allRobots():
  data = db.get_view_result('_design/robots', 'all', include_docs=True)
  
  # clean up the documents to match the expected format
  final = []
  for c in map(lambda x: x['doc'], data):
    c.pop('type', None)
    c.pop('sensors', None)
    c['id'] = c['_id']
    keys = list(c.keys())
    for k in keys:
      if k[0] == '_':
        c.pop(k, None)
    final.append(c)

  return jsonify(final)

@app.route("/robots", methods=['POST'])
def newRobot():
  data = request.get_json()
  
  expectsName = "name" in data and type(data["name"]) in [str, unicode]
  expectsManufacturer = "manufacturer" in data and type(data["manufacturer"]) in [str, unicode]
  expectsSensors = "sensors" in data and type(data["sensors"]) == list and reduce(lambda x, y: x and type(y) in [str, unicode], data["sensors"], True)

  if not(expectsName and expectsManufacturer and expectsSensors):
    return jsonify({"success": False}, status=400)
  
  robot = {
    "name": data["name"],
    "manufacturer": data["manufacturer"],
    "sensors": data["sensors"]
  }

  doc = db.create_document(robot)
  return jsonify({"success": doc.exists()})

@app.route("/robots/<robotId>", methods=['GET'])
def oneRobot(robotId):
  try:
    doc = db[robotId]
  except:
    return jsonify({"found": False}, status=404)
  
  # clean up the documents to match the expected format
  doc.pop('type', None)
  doc['id'] = robotId
  keys = list(doc.keys())
  for k in keys:
    if k[0] == '_':
      doc.pop(k, None)

  return jsonify(doc)

@app.route("/robots/<robotId>/sensors/<sensorName>", methods=['PATCH'])
def newMeasurement(robotId,sensorName):
  try:
    doc = db[robotId]
  except:
    return jsonify({"error": True, "reason": "Not Found"}, status=404)
  
  data = request.get_json()
  if not "value" in data:
    return jsonify({"error": True, "reason": "Bad input"}, status=400)
  
  # clean up the documents to match the expected format
  #sensors = doc['sensors'].filter(lambda x: x['name'] != sensorName)
  doc['sensors'].append({'name': sensorName, 'value': data['value']})
  #doc['sensors'] = sensors
  doc.save()

  return jsonify({"error": False})


port = os.getenv('PORT', '5000')
if __name__ == "__main__":
  app.run(host='0.0.0.0', port=int(port), debug=True)
