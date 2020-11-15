from flask import Flask, request, jsonify, make_response
from pymongo import MongoClient
import requests
from datetime import datetime, timedelta
import time
import sys, os
import io
import threading
from multiprocessing import Process, Lock
import log
import devices as devaux


# Response MW variables
flag_change_devices = True
lock_flag = Lock()

# Other Auxiliary variables
virtual_device_url = "http://127.0.0.1:1850"
mongo_url = "mongodb://127.0.0.1:27017/"
middleware_id = 'MW_KH_Living_Room_IoT'
middleware_url = 'http://9fbd15ae8c2e.ngrok.io'
#middleware_url = 'http://6525989f8f18.ngrok.io'
logger = log.Logger('middleware.log')




'''
client = MongoClient(mongo_url)
db = client.cc8

// ----- COLLECTIONS ----- //
col = client.cc8.iot_devices
col = client.cc8.iot_events_local
col = client.cc8.iot_events_external
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
	# Global Vars
	global mongo_url

	# Do stuff
	client = MongoClient(mongo_url)
	if option == 'devices':
		return client.cc8.iot_devices
	elif option == 'levents':
		return client.cc8.iot_events_local
	elif option == 'eevents':
		return client.cc8.iot_events_external
	elif option == 'logs':
		return client.cc8.logs
	elif option == 'misc':	
		return client.cc8.miscellaneous
	else:
		return object

def get_next(option):
	try:
		field = ''
		if option == 'device':
			field = 'next_device'
		elif option == 'event':
			field = 'next_external_event'
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
	except Exception as e:
		print("Error en get_next: " + print(e))


def do_event(value, iot_device):
	# Global Vars
	global middleware_id
	global middleware_url

	# Get Device info
	devices = get_collection('devices')
	device = devices.find_one({'iot_type': iot_device})
	query = {'id': device.get('id')}

	# Fetch all events related to the device
	events = get_collection('levents')
	iotdev_events = events.find_one(query).get('events')

	try:
		events_list = list(iotdev_events.keys())
		# Execute all events
		for event_ in events_list:
			# Fetch If, Then y Else
			event = iotdev_events[event_]
			#print(event)
			if_ = event['if']
			condition = if_['condition']

			# Evaluate Condition
			#print("Before")
			field = list(if_['right'].keys()).pop(0)
			#print("after")
			result = False

			

			value = value if device.get('type') == 'input' else device.get('text')
			print("Value: " + str(value) + "\tRight side: " + str(if_['right'][field]))
			if condition == "=":
				result = value == if_['right'][field]
			elif condition == "!=":
				result = value != if_['right'][field]
			elif condition == "<":
				result = value < if_['right'][field]
			elif condition == "<=":
				result = value <= if_['right'][field]
			elif condition == ">":
				result = value > if_['right'][field]
			elif condition == "=>":
				result = value >= if_['right'][field]

			# Do real execution
			to_execute = {}
			if result:
				to_execute = event['then']
			else:
				to_execute = event['else']


			# Send request
			requests.post(
				to_execute['url'] + ('/' if to_execute['url'][-1] != '/' else "") + 'change',
				json = {
					'id': middleware_id,
					'url': middleware_url,
					'date': get_date(),
					'change': {
						to_execute['id']: {
							'status': to_execute['status'],
							'text': to_execute['text']
						}
					}
			})
			
	except Exception as e:
		#print("Error en Do_event: " + str(e))
		pass

def execute_events(vd_data):
	# Getting parameters
	if len(vd_data) > 0:
		flags = int(vd_data[0:2], 16)
		speed = int(vd_data[2], 16)
		sliders = int(vd_data[4:10], 16)
		led_rgb = int(vd_data[11:17], 16)
		color = int(vd_data[18:24], 16)

		'''
		message = ""
		if len(data) > 24:
			message = data[25:]
			message = bytes.fromhex(message).decode('utf-8') 
		
		# Processing 
		lcd = flags & 0x80
		'''

		
		# Processing Switches
		switch0 = (flags & 0x40) >> 6
		do_event(switch0,'switch-0')
		
		'''
		switch1 = (flags & 0x20) >> 5
		do_event(switch1, 'switch-1')

		# Processing Fan
		fan = (flags & 0x10) >> 4
		log_device(2, 0 if fan == 0 else speed, 'fan-0')
		'''

		# Processing RGBs
		rgb = (flags & 0x08) >> 3

		'''
		red_rgb = led_rgb & 0xFF0000
		green_rgb = led_rgb & 0x00FF00
		blue_rgb = led_rgb & 0x0000FF
		'''

		do_event(led_rgb, 'rgb-0')

		# Processing LEDs
		led0 = (flags & 0x40) >> 6
		do_event(led0, 'led-0')

		led1 = (flags & 0x20) >> 5
		do_event(led1, 'led-1')

		'''
		# Processing heat
		heat = flags & 0x01
		log_device(1, heat, 'heat-0')
		'''

		
		# Processing Sliders
		slider0 = (sliders & 0xFF0000) >> 16
		do_event(slider0, 'slider-0')

		
		slider1 = (sliders & 0x00FF00) >> 8
		do_event(slider1, 'slider-1')
		

		'''
		slider2 = sliders & 0x0000FF
		log_device(2, slider2, 'slider-2')
		'''

		# Processing Pick Color
		'''
		red_color = color & 0xFF0000
		green_color = color & 0x00FF00
		blue_color = color & 0x0000FF
		'''

		do_event(color, 'pick_color-0')
		
	else:
		pass

def log_device(device_type, value, iot_device):
	# Collections
	devices = get_collection('devices')
	logs = get_collection('logs')

	try:
		# Get Device info
		device = devices.find_one({'iot_type': iot_device})
		query = {'id': device.get('id')}
		#print("Device: " + str(device == None))
		# Date
		this_date = get_date()

		# Log number
		multiple_logs = logs.find_one(query)
		#print("Multiple Logs: " + str(device == None))
		log_number = multiple_logs.get('sizelog') + 1
		#print("Log Number: " + str(log_number))
		#print("Device Status: " + str(device.get('status')))
		#print("Device text: " + str(device.get('text')))
		''' Log info '''
		# Switch, LED or RGB
		# 1 = Input device
		if device_type == 1: 
			value, status, text = devaux.compute_data(iot_device, value)
			logs.update_one(
				query,
				{
					'$set': {
						('log' + str(log_number)):
							{'date': this_date, 'sensor': value, 'status': status, 'text': text},
						'sizelog': log_number
					}
				}
			)
		elif device_type == 2:
			logs.update_one(
				query,
				{
					'$set': {
						('log' + str(log_number)):
							{'date': this_date, 'sensor': None, 'status': device.get('status'), 'text': device.get('text')},
						'sizelog': log_number
					}
				}
			)
		# Message
		elif device_type == 3:
			pass

		# Do event
		do_event(value, iot_device)
	except Exception as e:
		print("Error from log_device:" + str(e))
	

def process_data(data):
	# Getting parameters
	if len(data) > 0:
		flags = int(data[0:2], 16)
		speed = int(data[2], 16)
		sliders = int(data[4:10], 16)
		led_rgb = int(data[11:17], 16)
		color = int(data[18:24], 16)

		'''
		message = ""
		if len(data) > 24:
			message = data[25:]
			message = bytes.fromhex(message).decode('utf-8') 
		
		# Processing 
		lcd = flags & 0x80
		'''

		
		# Processing Switches
		switch0 = (flags & 0x40) >> 6
		log_device(1, switch0,'switch-0')
		
		'''
		switch1 = (flags & 0x20) >> 5
		log_device(1, switch1, 'switch-1')

		# Processing Fan
		fan = (flags & 0x10) >> 4
		log_device(2, 0 if fan == 0 else speed, 'fan-0')
		'''

		# Processing RGBs
		rgb = (flags & 0x08) >> 3

		'''
		red_rgb = led_rgb & 0xFF0000
		green_rgb = led_rgb & 0x00FF00
		blue_rgb = led_rgb & 0x0000FF
		'''

		log_device(2, led_rgb, 'rgb-0')

		# Processing LEDs
		
		led0 = (flags & 0x40) >> 6
		log_device(2, led0, 'led-0')
		'''

		led1 = (flags & 0x20) >> 5
		log_device(2, led1, 'led-1')

		
		# Processing heat
		heat = flags & 0x01
		log_device(1, heat, 'heat-0')
		'''

		
		# Processing Sliders
		slider0 = (sliders & 0xFF0000) >> 16
		log_device(2, slider0, 'slider-0')

		
		slider1 = (sliders & 0x00FF00) >> 8
		log_device(2, slider1, 'slider-1')
		

		'''
		slider2 = sliders & 0x0000FF
		log_device(2, slider2, 'slider-2')
		'''

		# Processing Pick Color
		'''
		red_color = color & 0xFF0000
		green_color = color & 0x00FF00
		blue_color = color & 0x0000FF
		'''

		#log_device(1, color, 'pick_color-0')
		
		
	else:
		pass

def get_date():
	return datetime.today().isoformat() + '-06:00'

def get_sub_date(isSubstraction):
	today = datetime.today()
	dtime = timedelta(seconds=3)
	final_datetime = (today - dtime) if isSubstraction else (today + dtime)

	return final_datetime.isoformat() + '-06:00'

def generate_response():
	#Global Vars
	global middleware_id
	global middleware_url

	return {'id': middleware_id, 'url': middleware_url, 'date': get_date()}


def execute_external_event(event_id):		# Pending
	# Global Vars
	global middleware_id
	global middleware_url

	frequency = 0
	while True:
		try:
			# Get collection
			events = get_collection('eevents')
			event = events.find_one({'id': event_id})
			print(event)

			# Getting and executing if
			if_ = event.get('if')

			frequency = if_['left']['freq']
			#print("Frecuency: " + str(frequency))
			mw_url = if_['left']['url']
			mw_device = if_['left']['id']

			result = True
			# Do search here, but... how to get the last record?
			print("Extra thread> Searching")
			response_ext_mw = requests.post(
				mw_url + '/search',
				json = {
					'id': middleware_id,
					'url': middleware_url,
					'date': get_date(),
					'search': {
						'id_hardware': mw_device,
						'start_date': get_sub_date(True),
						'finish_date': get_sub_date(False),
					}
			}).json()

			print("Extra thread> Got some registers")
			# Extract the latest value
			logs = response_ext_mw['data']
			ldates = list(logs.keys()) 
			if len(ldates) == 0:
				raise Exception("Logs Are empty")

			# Obtener max date
			max_date = ldates[0]
			for ldate in ldates:
				max_date = ldate if ldate > max_date else max_date

			# Obtain Value
			#print("Got some logs")
			the_log = logs[max_date]
			#print("Got max date")

			# Evaluate condition
			condition = if_['condition']
			result = False
			value = the_log['sensor']
			if condition == "=":
				result = value == if_['right']['sensor']
			elif condition == "!=":
				result = value != if_['right']['sensor']
			elif condition == "<":
				result = value < if_['right']['sensor']
			elif condition == "<=":
				result = value <= if_['right']['sensor']
			elif condition == ">":
				result = value > if_['right']['sensor']
			elif condition == "=>":
				result = value >= if_['right']['sensor']
			print("Result: " + str(result))

			# Executing branch
			to_execute = event.get('then') if result else event.get('else')

			#print("To execute Side: " + str(to_execute))
			#print("To execute URL: " + to_execute['url'])

			status = requests.post(
				to_execute['url'] + '/change',
				json = {
					'id': middleware_id,
					'url': middleware_url,
					'date': get_date(),
					'change': {
						to_execute['id']: {
							'status': to_execute['status'],
							'text': to_execute['text']
						}
					}
			}).json()['status']

			if status == 'OK':
				print("Evento ejecutado correctamente")
			else:
				print("Evento ejecutado incorrectamente")
			

			# Sleep
			time.sleep(frequency/1000)
		except Exception as e:
			print("Error on executing external event: " + print(e))
			break


# -------------------------------------- Web Server

# create the flask object
app = Flask(__name__)

@app.route('/')
def index():
	logger.log_warning("Unauthorized access.")
	return "You should not be here"

# -------------------------------------- IOT DEVICES ACTIONS

@app.route('/info', methods=['POST'])
def info():
	'''
	Input Fields:

	Output Fields:
	- hardware: an object of objects
	'''

	# Extracting fields
	rjson = request.get_json()

	# Logging
	logger.log_request(rjson['id'], "info", rjson)

	# Dispatching request
	server_response = generate_response()

	col = get_collection('devices')
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
	# GLobal Vars
	global flag_change_devices


	'''
	Input Fields:

	Output Fields:
	- status: either OK or ERROR
	'''

	# Extracting fields
	rjson = request.get_json()

	# Logging
	logger.log_request(rjson['id'], "change", rjson)

	# Extracting Fields

	
	change = rjson['change']
	id_devices = list(change.keys())
	
	# Dispatching request
	server_response = generate_response()

	try:
		for id_device in id_devices:
			# Extracting fields
			print("Change JSON: " + str(change))
			text = change[id_device]['text']
			devices = get_collection('devices')
			device = devices.find_one({'id': id_device})

			# Compute for given device

			value, status, text = devaux.compute_data(device.get('iot_type'), text)

			# Sanity Check
			if value == None:
				raise Exception("Error")

			# Update VD
			mw_response = ""
			with open("response.txt", "r") as mwres:
				values = mwres.readline()
				mw_response = values.split('-')[0]
			mw_response1 = devaux.generate_data(mw_response, device.get('iot_type'), value)
			with open("response.txt", "w") as mwres:
				mwres.write(mw_response1+"-1")
			print("Old value: " + mw_response + "\tNew Value: " + mw_response1)
			devices.update_one({'id': id_device}, {'$set': {'status': status, 'text': text}})


		server_response['status'] = 'OK'
	except Exception as e:
		print("Error en change: " + str(e))
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		print(exc_type, fname, exc_tb.tb_lineno)
		server_response['status'] = 'ERROR'

	return jsonify(server_response)

@app.route('/search', methods=['POST'])
def search():
	'''
	Input Fields:

	Output Fields:
	- status: either OK or ERROR
	'''

	# Extracting fields
	rjson = request.get_json()
	print("The JSON: " + str(rjson))

	# Logging
	logger.log_request(rjson['id'], "search", rjson)

	# Extracting fields
	search = rjson['search']

	id_ = search['id_hardware']
	start = search['start_date']
	finish = search['finish_date']

	# Dispatching request
	server_response = generate_response()

	try:
		col = get_collection('devices')
		iot_device = col.find_one({'id': id_})
		type_ = iot_device.get('type')

		server_response['search'] = {'id_hardware': id_, 'type': type_}
		
		logs = get_collection('logs')
		iot_device = logs.find_one({'id': id_})
		
		num_logs = iot_device.get('sizelog')

		retreived_logs = {}
		for i in range(num_logs):
			candidate = iot_device.get('log' + str(i+1))
			if(finish >= candidate['date'] and candidate['date'] >= start):
				retreived_logs[candidate['date']] = {'sensor': candidate['sensor'], 'status': candidate['status'], 'text': candidate['text']}
			else:
				pass

		server_response['data'] = retreived_logs
	except:
		pass

	return jsonify(server_response)

# -------------------------------------- IOT EVENTS

@app.route('/create', methods=['POST'])
def create():
	# Global Vars
	global middleware_url
	'''
	Input Fields:

	Output Fields:
	- status: either OK or ERROR
	'''

	rjson = request.get_json()

	# Logging
	logger.log_request(rjson['id'], "create", rjson)

	# Extracting fields
	create = rjson['create']

	if_ = create['if']
	then = create['then']
	else_ = create['else']

	# Dispatching request
	server_response = generate_response()

	# Get device
	left_device = ''
	try:
		# Local Events
		if if_['left']['url'] == middleware_url:
			id_ = if_['left']['id']
			query = {'id': id_}


			# If Validation area
			devices = get_collection('devices')
			device = devices.find_one(query)
			field = list(if_['right'].keys()).pop(0)

			if (device.get('type') == 'input') and (field == 'status' or field == 'text'):
				raise Exception("Not allowed, device is input and got status or text")
			elif (device.get('type') == 'output') and (field == 'sensor'):
				raise Exception("Not allowed, device is output and got sensor")

			# Create new event for device
			events = get_collection('levents')
			iotdev_events = events.find_one(query)

			event_id_no = iotdev_events.get('sizeevent') + 1
			event_id = id_ + "-EV" + str(event_id_no)

			# Create the event
			events.update_one(
				query,
				{
					'$set': {
						'events': {
							event_id:
								{'if': if_, 'then': then, 'else': else_}
						},
						'sizeevent': event_id_no
					}
				}
			)

			# Success
			server_response['idEvent'] = event_id
		# External events
		else:
			id_ = if_['left']['id']
			query = {'id': id_}

			# Create new external event
			events = get_collection('eevents')
			event_id = "EXEV" + str(get_next('event'))

			# Create the event
			events.insert_one({'id': event_id, 'if': if_, 'then': then, 'else': else_})

			# Create process
			thread = Process(target=execute_external_event, args=[event_id])
			thread.start()

			# Success
			server_response['idEvent'] = event_id

		
		server_response['status'] = 'OK'
	except Exception as e:
		print("Error en create: " + str(e))
		server_response['status'] = 'ERROR'

	return jsonify(server_response)

@app.route('/delete', methods=['POST'])
def delete():
	'''
	Input Fields:

	Output Fields:
	- status: either OK or ERROR
	'''

	rjson = request.get_json()

	# Logging
	logger.log_request(rjson['id'], "delete", rjson)

	# Extracting fields
	event_id = rjson['delete']['id']

	# Dispatching request
	server_response = generate_response()

	try:
		# Local event
		result = None
		if "EX" not in event_id:  
			# Get Device id from the event id
			device_id = event_id.split('-')[0]

			# Delete the event
			events = get_collection('levents')
			result = events.update(
				{'id': device_id},
				{'$unset': {
						'events': {event_id: 1}
					}
				}
			)
		# External Event
		else:
			# Delete the event
			events = get_collection('eevents')
			result = events.delete_one({'id': event_id})


		server_response['status'] = 'OK' if result != None else 'ERROR'
	except Exception as e:
		print("Error en delete: " + str(e))
		server_response['status'] = 'ERROR'

	return jsonify(server_response)

@app.route('/update', methods=['POST'])
def update():
	'''
	Input Fields:

	Output Fields:
	- status: either OK or ERROR
	'''

	rjson = request.get_json()

	# Logging
	logger.log_request(rjson['id'], "update", rjson)

	# Extracting fields
	update = rjson['update']
	event_id = update['id']

	# Dispatching request
	server_response = generate_response()

	try:
		to_update = list(update.keys())
		# Local Event
		if "EX" not in event_id:
			# Get Device id from the event id
			device_id = event_id.split('-')[0]

			# Update the event
			events = get_collection('levents')
			event = events.find_one({'id': device_id})

			if_ = update['if'] if 'if' in to_update else event.get('events')[event_id]['if']
			then_ = update['then'] if 'then' in to_update else event.get('events')[event_id]['then']
			else_ = update['else'] if 'else' in to_update else event.get('events')[event_id]['else']

			events.update_one({'id': device_id}, {'$set': {'events': {event_id: {'if': if_, 'then': then_, 'else': else_}}}})
		# External event
		else:
			# Update the event
			events = get_collection('eevents')

			if 'if' in to_update:
				events.update_one({'id': event_id}, {'$set': {'if': update['if']}})
			
			if 'then' in to_update:
				events.update_one({'id': event_id}, {'$set': {'then': update['then']}})
			
			if 'else' in to_update:
				events.update_one({'id': event_id}, {'$set': {'else': update['else']}})


		server_response['status'] = 'OK'
	except Exception as e:
		print("Error en update: " + str(e))
		server_response['status'] = 'ERROR'

	return jsonify(server_response)

# -------------------------------------- EXTRAS

@app.route('/iotcreate', methods=['POST'])		# Pending
def iotcreate():
	'''
	Input Fields:
	- tag: Device label
	- type: Either 'input' or 'output'
	- iot_type: type of IoT device

	1) sliders = 0
	2) leds = 0
	3) switches = 0
	4) rgbs = 0
	5) fans = 0
	6) heats = 0
	7) pick_colors = 0

	Output Fields:
	- result: either 'ok' or 'error'
	'''

	rjson = request.get_json()

	# Logging
	logger.log_request(rjson['id'], "iotcreate", rjson)

	# Extracting Fields
	tag = rjson['tag']
	type_ = rjson['type']
	id_ = 'id' + str(get_next('device'))
	iot_type = rjson['iot_type']

	# Deciding what type of iot device

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
	devices = get_collection('devices')
	result = devices.insert_one({'id': id_, 'tag': tag, 'type': type_, 'status': False, 'text': "OFF", 'iot_type': iot_type_device})

	# Creating log record
	logs = get_collection('logs')
	result = logs.insert_one({'id': id_, 'sizelog': 0})

	# Creating events
	events = get_collection('levents')
	result = events.insert_one({'id': id_, 'sizeevent': 0})
	server_response['status'] = 'OK' if result != '' else 'ERROR'

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

	# Logging
	logger.log_request(rjson['id'], "iotdelete", rjson)

	# Extracting Fields
	id_ = rjson['id']

	# Dispatching request
	server_response = generate_response()

	try:
		# Devices
		devices = get_collection('devices')
		result = devices.delete_one({'id': id_})

		# Logs
		logs = get_collection('logs')
		result = logs.delete_one({'id': id_})

		# Events
		events = get_collection('levents')
		result = events.delete_one({'id': id_})

		server_response['status'] = 'OK'
	except Exception as e:
		print("Error en iotdelete: " + str(e))
		server_response['status'] = 'ERROR'

	return jsonify(server_response)


@app.route('/log', methods=['POST'])
def log():
	# Global vars
	global flag_change_devices
	global lock_flag
	global virtual_device_url

	# Getting Data
	data = request.data.decode("utf-8") 

	# Logging
	logger.log_vd(data)

	# Making Dummy response
	response = make_response()

	response.headers['Content-Type'] = "text/plain"
	response.headers['Access-Control-Allow-Origin'] = virtual_device_url
	response.headers['Server'] = "Mr. Server CC8"

	new_response = ""
	flag_must_edit = False
	with open("response.txt", "r") as mwres:
		values = mwres.readline().split('-')
		if values[1] == '1':
			response.data = values[0]
			flag_must_edit = True
		else:
			response.data = ""
	
	with open("response.txt", "w") as mwres:
		if flag_must_edit:
			mwres.write(values[0]+"-0")
		else:
			mwres.write(data+"-0")
	
	if not flag_must_edit:
		process_data(data)
	#execute_events(data)

	return response

@app.route('/test', methods=['POST'])
def test():

	# Getting Data
	data = request.data.decode("utf-8") 

	headers = {"Content-Type":"text/plain", "Server": "Mr. Server CC8", "Access-Control-Allow-Origin": virtual_device_url}
	r = requests.post("http://127.0.0.1:1850", headers=headers, data= data)

	'''
	# Making Dummy response
	response = make_response()

	response.headers['Content-Type'] = "text/plain"
	response.headers['Access-Control-Allow-Origin'] = virtual_device_url
	response.headers['Server'] = "Mr. Server CC8"
	response.data = "60F000000000000000000000"
	'''
	print(get_sub_date(True))
	print(get_date())
	return "All good"


if __name__ == "__main__":
	app.run(host='127.0.0.1', port=12000, debug=True)
