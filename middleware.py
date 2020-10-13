from flask import Flask, request, jsonify
from pymongo import MongoClient
import io
import threading
import os
import time
from datetime import datetime
import requests

mongo_url = "mongodb://127.0.0.1:27017/"
middleware_id = 'MWApp_CC8Project001'

'''
client = MongoClient(mongo_url)
db = client.cc8

// ----- COLLECTIONS ----- //
col = client.cc8.iot_disp
col = client.cc8.iot_events
col = client.cc8.logs
col = client.cc8.miscellaneous

// ----- QUICK COMMANDS ----- //

- Search
col.find({}) 				// Returns all documents in the collection
col.find({'filter': 1}) 	// Returns all documents in the collection that cumple the condition

- Insert
col.insert_one(document)	// Inserts a document

// ----- USEFUL LINKS ----- //
- https://www.w3schools.com/python/python_mongodb_insert.asp 			// Python MongoDB Documentation
- https://www.tutorialspoint.com/mongodb/mongodb_insert_document.htm	// MongoDB console Documentation
'''

def get_collection(option):
	client = MongoClient(mongo_url)
	if option == 'iot_disp':
		return client.cc8.iot_disp
	elif option == 'iot_events':
		return client.cc8.iot_events
	elif option == 'logs':
		return client.cc8.logs
	elif option == 'misc':	
		return client.cc8.miscellaneous
	else:
		return object

def get_next(option):
	field = ''
	if option == 'device':
		field = 'next_device'
	else:
		field = 'next_event'

	col = get_collection('misc')
	doc = col.find_one({'name': 'misc'})

	# Get ID and update it
	next_id = doc.get('field')
	doc_id = doc.get('_id')

	# Updating next ID
	col.update_one({'_id': doc_id}, {'$inc': {'field': 1}})

	return int(next_id)

def get_date():		# PENDING
	return datetime.today().isoformat() + 'Z'


def generate_response():
	return {'id': middleware_id, 'url': '127.0.0.1', 'date': get_date()}


def worker():
    return threading.current_thread().name + str(threading.get_ident())

# create the flask object
app = Flask(__name__)

@app.route('/')
def index():
	return "You should not be here"

# -------------------------------------- IOT DEVICES ACTIONS

@app.route('/info', methods=['POST'])
def info():
	'''
	Input Fields:

	Output Fields:
	- hardware: an object of objects
	'''

	# Dispatching request
	server_response = generate_response()

	col = get_collection('iot_disp')
	iot_devices = col.find({})

	devices = {}
	for device in iot_devices:
		device_info = {
			'tag': device.get('tag'),
			'type': device.get('type'),
		}
		devices[device.get('id')] = device_info

	server_response['hardware'] = devices
	return jsonify(server_response)

@app.route('/change', methods=['POST'])
def change():
	'''
	Input Fields:

	Output Fields:
	- status: either OK or ERROR
	'''

	rjson = request.get_json()

	# Extracting Fields
	change = rjson['change']
	id_devices = list(change.keys())
	
	# Dispatching request
	server_response = generate_response()

	try:
		for id_device in id_devices:
			# Extracting fields
			status = change[id_device]['status']
			text = change[id_device]['text']
			col = get_collection('iot_disp')

			col.update_one({'id': id_device}, {'$set': {'status': status, 'text': text}})

		server_response['status'] = 'OK'
	except:
		server_response['status'] = 'ERROR'

	return jsonify(server_response)

@app.route('/search', methods=['POST'])		# PENDING
def search():
	'''
	Input Fields:

	Output Fields:
	- status: either OK or ERROR
	'''

	
	rjson = request.get_json()

	# Extracting fields
	search = rjson['search']

	id_ = search['id_hardware']
	start = search['start_date']
	finish = search['finish_date']

	# Dispatching request
	server_response = generate_response()

	try:
		col = get_collection('iot_disp')
		print(id_)
		iot_device = col.find_one({'id': id_})
		type_ = iot_device.get('type')

		server_response['search'] = {'id_hardware': id_, 'type': type_}

		# Do here date comparisons to get the data
		'''
		col = get_collection('logs')
		iot_device = iot_devices = col.find({'id': id_})
		'''
	except:
		pass
	'''
	
	'''

	return jsonify(server_response)

# -------------------------------------- IOT EVENTS

@app.route('/create', methods=['POST'])		# PENDING
def create():
	'''
	Input Fields:

	Output Fields:
	- status: either OK or ERROR
	'''

	rjson = request.get_json()

	# Extracting fields
	create = rjson['create']

	if_ = create['if']
	then = create['then']
	else_ = create['else']
	id_ = 'EV' + str(get_next('event'))

	# Dispatching request
	server_response = generate_response()

	try:
		col = get_collection('iot_events')
		col.insert_one({'id': id_, 'if': if_, 'then': then, 'else': else_})	

		server_response['idEvent'] = id_
		server_response['status'] = 'OK'
	except:
		server_response['status'] = 'ERROR'

	return jsonify(server_response)

@app.route('/delete', methods=['POST'])		# PENDING
def delete():
	'''
	Input Fields:

	Output Fields:
	- status: either OK or ERROR
	'''

	rjson = request.get_json()

	# Extracting fields
	id_ = rjson['delete']['id']

	# Dispatching request
	server_response = generate_response()

	try:
		col = get_collection('iot_events')
		result = col.delete_one({'id': id_})

		server_response['result'] = 'OK' if result != None else 'ERROR'
	except:
		server_response['status'] = 'ERROR'

	return jsonify(server_response)

@app.route('/update', methods=['POST'])		# PENDING
def update():
	'''
	Input Fields:

	Output Fields:
	- status: either OK or ERROR
	'''

	rjson = request.get_json()

	# Extracting fields
	update = rjson['update']
	id_event = update['id']

	# Dispatching request
	server_response = generate_response()

	try:
		to_update = list(update.keys())
		col = get_collection('iot_disp')

		if 'if' in to_update:
			col.update_one({'id': id_event}, {'$set': {'if': update['if']}})
		
		if 'then' in to_update:
			col.update_one({'id': id_event}, {'$set': {'then': update['then']}})
		
		if 'else' in to_update:
			col.update_one({'id': id_event}, {'$set': {'else': update['else']}})

		server_response['result'] = 'OK'
	except:
		server_response['status'] = 'ERROR'

	return jsonify(server_response)

# -------------------------------------- EXTRAS

@app.route('/iotcreate', methods=['POST'])
def iotcreate():
	'''
	Input Fields:
	- tag: Device label
	- type: Either 'input' or 'output'

	Output Fields:
	- result: either 'ok' or 'error'
	'''

	rjson = request.get_json()

	# Extracting Fields
	tag = rjson['tag']
	type_ = rjson['type']
	id_ = 'id' + str(get_next('device'))


	# Dispatching request
	server_response = generate_response()

	col = get_collection('iot_disp')
	result = col.insert_one({'id': id_, 'tag': tag, 'type': type_, 'status': False})

	server_response['result'] = 'OK' if result != '' else 'ERROR'

	return jsonify(server_response)

@app.route('/iotdelete', methods=['POST'])
def iotdelete():
	'''
	Input Fields:
	- id: Device's id

	Output Fields:
	- result: either 'ok' or 'error'
	'''

	rjson = request.get_json()

	# Extracting Fields
	id_ = rjson['id']

	# Dispatching request
	server_response = generate_response()

	col = get_collection('iot_disp')
	result = col.delete_one({'id': id_})

	server_response['result'] = 'OK' if result != None else 'ERROR'

	return jsonify(server_response)



@app.route('/test', methods=['POST'])
def test():
	# Dispatching request
	col = get_collection('iot_disp')
	test_doc = {'succesful2': ' ok'}

	col.insert_one(test_doc)
	# Return response
	server_response = {'status': ' OK'}
	return jsonify(server_response)


if __name__ == "__main__":
	app.run(host='127.0.0.1', port=12000, debug=True)