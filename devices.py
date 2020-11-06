def led_action(text):
	if text == "ON":
		return 0x01, True, text
	elif text == "OFF":
		return 0x00, False, text

def switch_action(text):
	if text == "ON":
		return 0x01, True, text
	elif text == "OFF":
		return 0x00, False, text

def rgb_action(text):
	if text == "OFF":
		return 0x000000, False, "OFF"
	else:
		return int(text.upper()[1:], 16), True, text

def color_picker_action(text):
	if text == "OFF":
		return 0x000000, False, "OFF"
	else:
		return int(text.upper()[1:], 16), True, text

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
		return int(value, 16), True, text

def brightness_slider_action(text):
	# Convert temperature
	brightness = float(text)
	if temp > 12 or temp < 0:
		return None, None, None

	value = 255*brightness/12
	value = int(value)

	if text == "OFF":
		return 0x00, False, "OFF"
	else:
		return int(value, 16), True, text

def compute_text(iot_type, text):
	print(iot_type)
	if "led" in iot_type:
		return led_action(text)
	elif "switch" in iot_type:
		return switch_action(text)
	elif "rgb" in iot_type:
		return rgb_action(text)
	elif "color" in iot_type:
		return color_picker_action(text)
	elif "slider-0" in iot_type:
		return temperature_slider_action(text)
	elif "slider-1" in iot_type:
		return brightness_slider_action(text)
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
		remaining_right = data[1:]

		section = "0" if new_value == 1 else "4"

		return section + remaining_right
	# Processing RGB
	elif "rgb" in iot_type:
		remaining1 = data[0]
		section1 = int(data[1], 16)
		remaining2 = data[2:12]
		rgb = int(data[12:18], 16)
		remaining3 = data[18:]

		if new_value == 0:
			section1 = format(section1 & ~0x8).upper()
			rgb = "000000"
		else:
			section1 = format(section1 | 0x8).upper()
			rgb = format(new_value, 'x').upper()
		return remaining1 + section1 + remaining2 + rgb + remaining3
	# Processing Slider
	elif "slider" in iot_type:
		remaining_left = data[0:4]
		section = format(new_value, 'x').upper()
		remaining_right = data[6:]

		return remaining_left + section + remaining_right
