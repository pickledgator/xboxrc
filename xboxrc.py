#!/usr/bin/env python

# XboxRC
# Requirements: Linux with xpad kernel module support (sudo modprobe xpad)

import sys, os
import struct, array
import threading
import logging
import signal
import time
from fcntl import ioctl

logging.basicConfig(format='%(asctime)s %(levelname)s [%(module)s] %(message)s', level=logging.INFO)

class XboxRC():
	def __init__(self, useQuack=False):
		self.logger = logging.getLogger('xboxrc')
		self.devicesAvailable = False
		self.useQuack = useQuack

		if not self.detectXboxDevices():
			return

		self.devicesAvailable = True

		# We'll store the states here.
		self.axis_states = {}
		self.button_states = {}

		# These constants were borrowed from linux/input.h
		self.axis_names = {
			0x00 : 'x',
			0x01 : 'y',
			0x02 : 'z',
			0x03 : 'rx',
			0x04 : 'ry',
			0x05 : 'rz',
			0x06 : 'trottle',
			0x07 : 'rudder',
			0x08 : 'wheel',
			0x09 : 'gas',
			0x0a : 'brake',
			0x10 : 'hat0x',
			0x11 : 'hat0y',
			0x12 : 'hat1x',
			0x13 : 'hat1y',
			0x14 : 'hat2x',
			0x15 : 'hat2y',
			0x16 : 'hat3x',
			0x17 : 'hat3y',
			0x18 : 'pressure',
			0x19 : 'distance',
			0x1a : 'tilt_x',
			0x1b : 'tilt_y',
			0x1c : 'tool_width',
			0x20 : 'volume',
			0x28 : 'misc',
		}

		self.button_names = {
			0x120 : 'trigger',
			0x121 : 'thumb',
			0x122 : 'thumb2',
			0x123 : 'top',
			0x124 : 'top2',
			0x125 : 'pinkie',
			0x126 : 'base',
			0x127 : 'base2',
			0x128 : 'base3',
			0x129 : 'base4',
			0x12a : 'base5',
			0x12b : 'base6',
			0x12f : 'dead',
			0x130 : 'a',
			0x131 : 'b',
			0x132 : 'c',
			0x133 : 'x',
			0x134 : 'y',
			0x135 : 'z',
			0x136 : 'tl',
			0x137 : 'tr',
			0x138 : 'tl2',
			0x139 : 'tr2',
			0x13a : 'select',
			0x13b : 'start',
			0x13c : 'mode',
			0x13d : 'thumbl',
			0x13e : 'thumbr',

			0x220 : 'dpad_up',
			0x221 : 'dpad_down',
			0x222 : 'dpad_left',
			0x223 : 'dpad_right',

			# XBox 360 controller uses these codes.
			0x2c0 : 'dpad_left',
			0x2c1 : 'dpad_right',
			0x2c2 : 'dpad_up',
			0x2c3 : 'dpad_down',
		}

		self.axis_map = []
		self.button_map = []

		if self.useQuack:
			self.capnp = __import__('capnp')
			self.quack = __import__('quack')
			self.xboxrc_capnp = __import__('xboxrc_capnp')
			self.ctx = self.quack.Node("xboxrc")
			self.pub = self.quack.Publisher(self.ctx, "XBOX/RAW", [])
			self.logger = self.ctx.logger

		self.thread = threading.Thread(name='xpad', target=self.run)
		self.thread.setDaemon(True)
		self.thread.start()

		#self.openXboxDevice()
		
	def openXboxDevice(self):
		# Open the joystick device.
		fn = '/dev/input/js0'
		self.logger.info("Opening {}...".format(fn))
		self.jsdev = open(fn, 'rb')

		# Get the device name.
		buf = array.array('c', ['\0'] * 64)
		ioctl(jsdev, 0x80006a13 + (0x10000 * len(buf)), buf) # JSIOCGNAME(len)
		js_name = buf.tostring()
		self.logger.info('Device name: {}'.format(js_name))

		# Get number of axes and buttons.
		buf = array.array('B', [0])
		ioctl(jsdev, 0x80016a11, buf) # JSIOCGAXES
		num_axes = buf[0]

		buf = array.array('B', [0])
		ioctl(jsdev, 0x80016a12, buf) # JSIOCGBUTTONS
		num_buttons = buf[0]

		# Get the axis map.
		buf = array.array('B', [0] * 0x40)
		ioctl(jsdev, 0x80406a32, buf) # JSIOCGAXMAP

		for axis in buf[:num_axes]:
			axis_name = axis_names.get(axis, 'unknown(0x%02x)' % axis)
			axis_map.append(axis_name)
			axis_states[axis_name] = 0.0

		# Get the button map.
		buf = array.array('H', [0] * 200)
		ioctl(jsdev, 0x80406a34, buf) # JSIOCGBTNMAP

		for btn in buf[:num_buttons]:
			btn_name = button_names.get(btn, 'unknown(0x%03x)' % btn)
			button_map.append(btn_name)
			button_states[btn_name] = 0

		self.logger.info("{} axes found: {}".format(num_axes, ",".join(axis_map)))
		self.logger.info("{} buttons found: {}".format(num_buttons, ",".join(button_map)))


	def detectXboxDevices(self):
		# Iterate over the joystick devices.
		numDevices = 0
		try:
			for fn in os.listdir('/dev/input'):
				if fn.startswith('js'):
					numDevices = numDevices + 1
		except:
			pass

		self.logger.info("Searching for devices: Found {} devices".format(numDevices))
		return numDevices

	def run(self):
		if not self.devicesAvailable:
			return
		
		# Main event loop
		while True:
			eventType = self.xboxrc_capnp.Xbox.EventType.none
			eventField = self.xboxrc_capnp.Xbox.EventField.none
			eventValue = 0.0
			evbuf = self.jsdev.read(8)
			if evbuf:
				time, value, type, number = struct.unpack('IhBB', evbuf)

				if type & 0x80:
					 self.logger.info("(initial)"),

				if type & 0x01:
					eventType = self.xboxrc_capnp.Xbox.EventType.Button
					eventValue = value
					# tood field to capnp
					button = button_map[number]
					if button:
						button_states[button] = value
						if value:
							self.logger.info("{} pressed".format(button))
						else:
							self.logger.info("{} released".format(button))

				if type & 0x02:
					eventType = self.xboxrc_capnp.Xbox.EventType.Axis
					eventValue = value
					# todo map field to capnp
					axis = axis_map[number]
					if axis:
						fvalue = value / 32767.0
						axis_states[axis] = fvalue
						self.logger.info("{}: {:.3f}".format(axis, fvalue))

				if self.useQuack:
					self.sendEvent(eventType, eventField, eventValue)

	def sendEvent(self, eventType, eventField, eventValue):
		msg = self.xboxrc_capnp.Xbox.new_message()
		msg.timestamp = int(time.time() * 1000000) # microsecond
		msg.type = eventType
		msg.field = eventField
		msg.value = eventValue
		self.pub.send(msg)


if __name__ == '__main__':
	rc = XboxRC(True)
	rc.run()

	