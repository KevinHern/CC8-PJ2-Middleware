from flask import Flask, request, jsonify, make_response
from pymongo import MongoClient
import io
import threading
import os
import time
from datetime import datetime
import requests

virtual_device_url = "http://127.0.0.1:1850"
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
	elif option == 'event':
		field = 'next_event'
	elif option == 'switch':
		field = 'next_switch'
	elif option == 'slider':	
		field = 'next_slider'
	elif option == 'led':
		field = 'next_led'
	elif option == 'rgb':
		field = 'next_rgb'
	elif option == 'fan':
		field = 'next_fan'
	elif option == 'heat':
		field = 'next_heat'
	elif option == 'pick_color':
		field = 'next_pick_color'

	col = get_collection('misc')
	doc = col.find_one({'name': 'misc'})

	# Get ID and update it
	next_id = doc.get(field)
	doc_id = doc.get('_id')

	# Updating next ID
	col.update_one({'_id': doc_id}, {'$inc': {field: 1}})

	return int(next_id)

def log_device(device_type, value, iot_device):
	# Collections
	devices = get_collection('iot_disp')
	logs = get_collection('logs')

	# Get Device info
	device = devices.find_one({'iot_type': iot_device})
	query = {'id': device.get('id')}

	# Get Events
	events = get_collection('iot_events')

	# Date
	this_date = get_date()

	# Log number
	log_number = logs.find_one(query).get('sizelog') + 1

	''' Log info '''
	# Switch, LED or RGB
	if device_type == 1: 
		logs.update_one(
			query,
			{
				'$set': {
					('log' + str(log_number)):
						{'date': this_date, 'sensor': value, 'status': device.get('status'), 'text': 'ON' if value == 1 else 'OFF'},
					'sizelog': log_number
				}
			}
		)
	# Fan, Heat, Slider, RGB or Pick Color
	elif device_type == 2:
		logs.update_one(
			query,
			{
				'$set': {
					('log' + str(log_number)):
						{'date': this_date, 'sensor': value, 'status': device.get('status'), 'text': device.get('text')},
					'sizelog': log_number
				}
			}
		)
	# Message
	elif device_type == 3:
		pass

def process_data(data):
	# Getting parameters
	if len(data) > 0:
		flags = int(data[0:2], 16)
		speed = int(data[2], 16)
		sliders = int(data[4:10], 16)
		led_rgb = int(data[12:18], 16)
		color = int(data[19:24], 16)

		message = ""
		if len(data) > 24:
			message = data[25:]
			message = bytes.fromhex(message).decode('utf-8') 
		
		# Processing 
		lcd = flags & 0x80

		# Processing Switches
		switch0 = (flags & 0x40) >> 6
		log_device(1, switch0,'switch-0')
		

		switch1 = (flags & 0x20) >> 5
		log_device(1, switch1, 'switch-1')

		
		'''
		# Processing Fan
		fan = (flags & 0x10) >> 4
		log_device(2, 0 if fan == 0 else speed, 'fan-0')

		# Processing RGBs
		rgb = (flags & 0x08) >> 3

		red_rgb = led_rgb & 0xFF0000
		green_rgb = led_rgb & 0x00FF00
		blue_rgb = led_rgb & 0x0000FF

		log_device(1, 0 if rgb == 0 else led_rgb, 'rgb-0')

		# Processing LEDs
		led0 = (flags & 0x40) >> 6
		log_device(1, led0, 'led-0')

		led1 = (flags & 0x20) >> 5
		log_device(1, led1, 'led-1')

		# Processing heat
		heat = flags & 0x01
		log_device(1, heat, 'heat-0')

		# Processing Sliders
		slider0 = sliders & 0xFF0000
		log_device(2, slider0, 'slider-0')

		slider1 = sliders & 0x00FF00
		log_device(2, slider1, 'slider-1')

		slider2 = sliders & 0x0000FF
		log_device(2, slider2, 'slider-2')

		# Processing Pick Color
		red_color = color & 0xFF0000
		green_color = color & 0x00FF00
		blue_color = color & 0x0000FF

		log_device(2, slider0, 'pick_color-0')

		'''
		
	else:
		pass

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
		
		logs = get_collection('logs')
		iot_device = logs.find_one({'id': id_})
		
		print('here')
		num_logs = iot_device.get('sizelog')

		print('here1')

		for i in range(num_logs):
			candidate = iot_device.get('log' + str(i+1))
			if(finish >= candidate['date'] and candidate['date'] >= start):
				server_response[candidate['date']] = {'sensor': candidate['sensor'], 'status': candidate['status'], 'text': candidate['text']}
			else:
				pass


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
	- iot_type: type of IoT device

	Output Fields:
	- result: either 'ok' or 'error'

	1) sliders = 0
	2) leds = 0
	3) switches = 0
	4) rgbs = 0
	5) fans = 0
	6) heats = 0
	7) pick_colors = 0
	'''

	rjson = request.get_json()

	# Extracting Fields
	tag = rjson['tag']
	type_ = rjson['type']
	id_ = 'id' + str(get_next('device'))
	iot_type = rjson['iot_type']

	# Deciding what type of iot device
	iot_type_device = ""

	if iot_type == 1:
		iot_type_device = "slider-" + str(get_next('slider'))
	elif iot_type == 2:
		iot_type_device = "led-" + str(get_next('led'))
	elif iot_type == 3:
		iot_type_device = "switch-" + str(get_next('switch'))
	elif iot_type == 4:
		iot_type_device = "rgb-" + str(get_next('rgb'))
	elif iot_type == 5:
		iot_type_device = "fan-" + str(get_next('fan'))
	elif iot_type == 6:
		iot_type_device = "heat-" + str(get_next('heat'))
	else:
		iot_type_device = "pick_color-" + str(get_next('pick_color'))

	# Dispatching request
	server_response = generate_response()

	# Registering device
	devices = get_collection('iot_disp')
	result = devices.insert_one({'id': id_, 'tag': tag, 'type': type_, 'status': False, 'iot_type': iot_type_device})

	# Creating log record
	logs = get_collection('logs')
	result = logs.insert_one({'id': id_, 'sizelog': 0})
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
	server_response = generate_ersponse()

	try:
		# Devices
		devices = get_collection('iot_disp')
		result = devices.delete_one({'id': id_})

		# Logs
		logs = get_collection('logs')
		result = logs.delete_one({'id': id_})

		server_response['result'] = 'OK'
	except:
		server_response['result'] = 'ERROR'

	return jsonify(server_response)


@app.route('/log', methods=['POST'])
def log():

	# Getting Data
	print("Data:")
	data = request.data.decode("utf-8") 
	print(data)
	print(len(data))

	# Process Data
	process_data(data)

	# Making Dummy response
	response = make_response()

	response.headers['Content-Type'] = "text/plain"
	response.headers['Access-Control-Allow-Origin'] = virtual_device_url
	response.headers['Server'] = "Mr. Server CC8"
	response.data = ""

	return response


if __name__ == "__main__":
	app.run(host='127.0.0.1', port=12000, debug=True)