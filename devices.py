def led_action(text):
	if text == "ON":
		return 0x01, True, text
	elif text == "OFF":
		return 0x00, False, text

def switch_action(value):
	if value == 1:
		return 0x01, True, "Active"
	else:
		return 0x00, False, "Inactive"

def rgb_action(text):
	if text == "OFF":
		return 0x000000, False, "OFF"
	else:
		return int(text.upper()[1:], 16), True, text

def color_picker_action(value):

	red = (value & 0xFF0000) >> 16
	red = ("0" if red < 16 else "") + format(red, 'x').upper()

	green = (value & 0x00FF00) >> 8
	green = ("0" if green < 16 else "") + format(green, 'x').upper()

	blue = (value & 0x0000FF)
	blue = ("0" if blue < 16 else "") + format(blue, 'x').upper()

	color = red + green + blue

	return value, True, "#" + color 

def temperature_slider_action(text):
	# Convert temperature
	temp = float(text)
	if temp > 35 or temp < 10:
		return None, None, None

	value = 255*(temp-10)/25
	value = int(value)

	if text == "OFF":
		return 0x00, False, "OFF"
	else:
		return value, True, text

def brightness_slider_action(text):
	# Convert temperature
	brightness = float(text)
	if brightness > 12 or brightness < 0:
		return None, None, None

	value = 255*brightness/12
	value = int(value)

	if text == "OFF":
		return 0x00, False, "OFF"
	else:
		return value, True, text

def compute_data(iot_type, data):
	if "led" in iot_type:
		return led_action(data)
	elif "switch" in iot_type:
		return switch_action(data)
	elif "rgb" in iot_type:
		return rgb_action(data)
	elif "color" in iot_type:
		return color_picker_action(data)
	elif "slider-0" in iot_type:
		return temperature_slider_action(data)
	elif "slider-1" in iot_type:
		return brightness_slider_action(data)
	else:
		return None, None, None

def generate_data(data, iot_type, new_value):

	# Processing LEDs
	if "led" in iot_type:
		remaining_right = data[0]
		section = int(data[1], 16)
		remaining_left = data[2:]
		

		if "0" in iot_type:
			section = format(section | 0x4, 'x').upper() if new_value == 1 else format(section & ~0x4, 'x').upper()
		elif "1" in iot_type:
			section = format(section | 0x2, 'x').upper() if new_value == 1 else format(section & ~0x2, 'x').upper()

		return remaining_right + section + remaining_left
	# Processing Switches
	elif "switch" in iot_type:
		section = int(data[0], 16)
		remaining_right = data[1:]

		if "0" in iot_type:
			section = format(section | 0x4, 'x').upper() if new_value == 1 else format(section & ~0x4, 'x').upper()
		elif "1" in iot_type:
			section = format(section | 0x2, 'x').upper() if new_value == 1 else format(section & ~0x2, 'x').upper()

		return section + remaining_right
	# Processing RGB
	elif "rgb" in iot_type:
		print("In devices.py: old value is " + data + " and new value is " + str(new_value))
		remaining1 = data[0]
		section1 = int(data[1], 16)
		remaining2 = data[2:11]
		remaining3 = data[17:]

		if new_value == 'OFF':
			section1 = format(section1 & ~0x8, 'x').upper()
			rgb = "000000"
		else:
			section1 = format(section1 | 0x8, 'x').upper()
			
			red = (new_value & 0xFF0000) >> 16
			red = ("0" if red < 16 else "") + format(red, 'x').upper()

			green = (new_value & 0x00FF00) >> 8
			green = ("0" if green < 16 else "") + format(green, 'x').upper()

			blue = (new_value & 0x0000FF)
			blue = ("0" if blue < 16 else "") + format(blue, 'x').upper()


			rgb = red + green + blue
		return remaining1 + section1 + remaining2 + rgb + remaining3
	# Processing slider Slider
	elif "slider" in iot_type:
		offset = 0 if ("0" in iot_type) else 2
		remaining_left = data[0:4 + offset]
		section =  ("0" if new_value < 16 else "") + format(new_value, 'x').upper()
		remaining_right = data[6 + offset:]

		return remaining_left + section + remaining_right