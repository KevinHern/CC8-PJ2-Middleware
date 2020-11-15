import re
from flask import Flask, request, jsonify
import requests
import telegram
from credentials import bot_token, bot_user_name,URL
from multiprocessing import Lock

global bot
global TOKEN
TOKEN = bot_token
bot = telegram.Bot(token=TOKEN)
telegram_id = "Telegram CC8-KH Bot"

app = Flask(__name__)


def bot_reply_to(chat_id, msg_id, message):
	bot.sendMessage(chat_id=chat_id, text=message, reply_to_message_id=msg_id)

def generate_request():
	return {'id': telegram_id}


@app.route('/{}'.format(TOKEN), methods=['POST'])
def respond():
	try:
		# retrieve the message in JSON and then transform it to Telegram object
		update = telegram.Update.de_json(request.get_json(force=True), bot)

		# Get the chat from which the bot was called
		chat_id = update.message.chat.id

		# Get the message ID to reply to it
		msg_id = update.message.message_id

		text = update.message.text.encode('utf-8').decode()

		# Extracting commands and parameteres
		raw_command = text.split(' ')
		command = raw_command[0]

		# // ALL THE MAGIC STARTS HERE
		if command == "/start":
			# Welcome message
			bot_welcome = """
			Welcome! This is a simple bot that can connect to a middleware and do magic stuff!\nType '/help' for available commands!
			This is an extra for the CC8 IoT final project of 2020.
			"""
			# send the welcoming message
			bot_reply_to(chat_id, msg_id, bot_welcome)
		elif command == "/help":
			message = """
			Available commands:\n
			/find <Middlware URL>
				> Sets the Middleware URL to which the bot will try to connect to.
			/discover
				> Retrieves all the IoT devices associated with the middleware
			/showall
				> Shows the retrieved IoT devices
			/showurl
				> Shows the URL of the middleware that the bot is connected to.
			/change <Device Number> <value>
				> Changes the device's current value to the one you specify. Depending on the device, it will take different values
				Use the following link for more details in case you want to change values on the KH Living Room Middleware:
				https://hernandez-kevin.gitbook.io/cc8-kh-middleware/

			Note*
			When the value is
			"""
			bot_reply_to(chat_id, msg_id, message)
		elif command == "/find":		
			try:
				parameters = raw_command[1:]
				message = ""
				if len(parameters[0]) > 0:
					middleware_url = parameters[0]
					f = open("middleware_url.txt", "w")
					f.write(middleware_url)
					f.close()
					message = "Connection set to: " + middleware_url + "\nTry to send a command to test if the connection is stablished."
				else:
					message = "URL is empty."
				bot_reply_to(chat_id, msg_id, message)
			except Exception as e:
				print(e)
				bot_reply_to(chat_id, msg_id, "An error has occured while setting URL. Try again.")

		# IoT devices commands!
		elif command == "/discover":
			message = ""
			try:
				# Prepare Request
				the_json = generate_request()

				url = ""
				with open("middleware_url.txt", "r") as middleware_url:
					url = middleware_url.readline()
				rjson = requests.post(url + "/info", json=the_json).json()

				# Parse Respons

				# Devices
				hardware = rjson['hardware']
				devices_keys = list(hardware.keys())

				index = 1
				message = ""
				with open("devices.txt", "w") as devices:	
					for device_key in devices_keys:
						# Get device
						device = hardware[device_key]

						# Build message and 
						devices.write(device['tag']+"&"+device['type']+"&"+device_key+"&\n")

						message += str(index) + ") " + device['tag'] + "\nType of device: " + device['type'] + "\n\n"
						# Updating index
						index += 1

				message = message[0:-2] if len(message) > 0 else "No IoT devices were found"
			except Exception as e:
				print(e)
				message = "Could not fetch IoT devices from the middleware. Is the URL correct?"

			bot_reply_to(chat_id, msg_id, message)
		elif command == "/showall":
			try:
				message = ""
				index = 1

				with open("devices.txt", "r") as devices:
					for device in devices:

						device_fields = device.split('&')
						message += str(index) + ") " + device_fields[0] + "\nType of device: " + device_fields[1] + "\n\n"
						# Updating index
						index += 1
				

				message = message[0:-2] if len(message) > 0 else "No IoT devices were found"

				bot_reply_to(chat_id, msg_id, message)
			except:
				bot_reply_to(chat_id, msg_id, "No IoT devices have been retreived!")
		elif command == "/showurl":
			try:
				with open("middleware_url.txt", "r") as middleware_url:
					bot_reply_to(chat_id, msg_id, middleware_url.readline())
			except:
				bot_reply_to(chat_id, msg_id, "URL has not been set!")
		elif command == "/change":
			parameters = raw_command[1:]
			try:
				device_id = ""
				with open("devices.txt", "r") as devices:
					for i, line in enumerate(devices):
						if i == (int(parameters[0], 10) - 1):
							device_id = line.split('&')[-2]
							break
				url = ""
				with open("middleware_url.txt", "r") as middleware_url:
					url = middleware_url.readline()

				the_json = generate_request()
				the_json['url'] = 'CC8.Bot'
				the_json['change'] = {device_id: {'text': str(parameters[1]).upper(), 'status': False if str(parameters[1]).upper() == 'OFF' else True}}

				rjson = requests.post(url + "/change", json=the_json).json()
				#print(rjson)

				if rjson['status'] == 'OK':
					bot_reply_to(chat_id, msg_id, "Change has been applied succesfully.")	
				else:
					bot_reply_to(chat_id, msg_id, "An error has occured, try again.")
			except Exception as e:
				print(e)
				bot_reply_to(chat_id, msg_id, "An error has occured, have you retrieved the IoT devices from the middlware?")
		else:
			try:
				# Send meme
				url = "https://i.pinimg.com/originals/f6/3e/d4/f63ed4353608ac2c6080fdafedd60865.png"
				bot.sendPhoto(chat_id=chat_id, photo=url, reply_to_message_id=msg_id)
			except Exception:
				pass
		return 'Hidden easter egg!'
	except:
		return 'Hidden easter egg!'

@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
	s = bot.setWebhook('{URL}{HOOK}'.format(URL=URL, HOOK=TOKEN))
	# asdf
	if s:
		return "webhook setup ok"
	else:
		return "webhook setup failed"

@app.route('/')
def index():
	return 'Unauthorized access.'


if __name__ == '__main__':
	 app.run(threaded=True)
