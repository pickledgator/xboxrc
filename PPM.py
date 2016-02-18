#!/usr/bin/env python

# PPM.py
# 2016-02-16
# Public Domain

import time
import signal
import pigpio
import threading

_ppms = []

def _signalHandler(signum, frame):
	for ppm in _ppms:
		ppm.stop()
	exit(0)

class PPM:
	def __init__(self, gpio, channels=8, frame_ms=27, gap_ms=100, debug=False):
		self.pi = pigpio.pi()

        	if not self.pi.connected:
                	print("pigpio error, is the pigpiod running?")
			exit(0)

		self.gpio = gpio
		self.gap_ms = gap_ms
		self.debug = debug

		if frame_ms < 5:
			frame_ms = 5
			channels = 2
		elif frame_ms > 100:
			frame_ms = 100

		self.frame_us = int(frame_ms * 1000)

		if channels < 1:
			channels = 1
		elif channels > (frame_ms // 2):
			channels = int(frame_ms // 2)

		self.channels = channels

		self._widths = [1000 for c in range(channels)] # init to min channels

		self._waves = [] # list to keep track of the next waves, maintains gapless transition on updates

		self.pi.write(gpio, pigpio.LOW) # start gpio low

		self.shouldExit = False
		self.count = 0

		_ppms.append(self)
		signal.signal(signal.SIGINT, _signalHandler)
            	signal.signal(signal.SIGTERM, _signalHandler)
            	signal.signal(signal.SIGHUP, _signalHandler)

	def start(self):
		self.sendThread = threading.Thread(name='ppmsend', target=self.send)
		self.sendThread.daemon = True
		self.sendThread.start()

	def _update(self):
		if self.debug:
			print("Updating channels {}".format(' '.join(str(s) for s in self._widths)))
		# if the waves list is full, send the first one
		if len(self._waves) == 2:
			self._waves.pop(0) # pop off the first wave

		# calculate the next wave to be added
		wf =[]
		micros = 0
		for i in self._widths:
			wf.append(pigpio.pulse(0, 1<<self.gpio, self.gap_ms))
			wf.append(pigpio.pulse(1<<self.gpio, 0, i))
			micros += (i+self.gap_ms)
		# off for the remaining frame period
		wf.append(pigpio.pulse(0, 1<<self.gpio, self.frame_us-micros))

		# add it to our 2 element list
		self.pi.wave_add_generic(wf)
		wid = self.pi.wave_create()
		self._waves.append(wid)

	def send(self):
		if self.shouldExit: return

		# if the tx is still sending the last wave, wait until its done
		while self.pi.wave_tx_busy():
			if self.shouldExit: return
			time.sleep(0.0001)

		if len(self._waves) > 0:
			if self.debug:
				print("sending wid {} waves len {}".format(self._waves[0], len(self._waves)))
			self.pi.wave_send_once(self._waves[0])
			if len(self._waves) > 1:
				self._waves.pop(0) # if there's two items in our list stack, pop the first one, so we get to the next queued one
	  		self.count += 1
		else:
			if self.debug:
				print("wid is None at waves[0]")
			# wait a bit before trying again to send
			time.sleep(0.1)

		self.send() # repeat send

	def update_channel(self, channel, width):
		if channel > self.channels-2:
			print("Invalid channel {} > max channel {}".format(channel, self.channels-1))
			return
		# check for valid input
		width = min(max(1000,width), 2000)
		self._widths[channel] = width
		self._update()

	def update_channels(self, widths):
		if not len(widths) == self.channels:
			print("widths list must match number of channels")
			return
		# check for valid input
		widths = [min(max(1000,w), 2000) for w in widths]
		self._widths[0:len(widths)] = widths[0:self.channels]
		self._update()

	def stop(self):
		print("Stopping waveforms")
		self.shouldExit = True
		time.sleep(0.01) # wait a bit for the thread to exit
		self.pi.wave_tx_stop()
		self.pi.wave_clear()
		#for w in self._waves:
		#	if w is not None:
		#		self.pi.wave_delete(w)
		self.pi.stop()		

if __name__ == "__main__":

	# build ppm using gpio 6
	ppm = PPM(6)
	# test invalid range inputs
	ppm.update_channels([3000, 500, -1000, 1000, 1000, 1000, 1000, 2000])
	time.sleep(0.5)
	# test wrong number of channels in update list
	ppm.update_channels([2000, 1000, 2000, 1000, 2000, 1000, 2000])
	# update individual channel
	ppm.update_channel(6, 500)
	# test channel out of range
	ppm.update_channel(9, 1500)
	start = time.time()
	ppm.start()
	ppm.update_channels([1500, 2000, 1000, 2000, 1000, 2000, 1000, 2000])
	ppm.update_channels([1501, 2000, 1000, 2000, 1000, 2000, 1000, 2000])
	for i in range(1,20):
		ppm.update_channels([1000+i*20, 2000, 1000+i*20, 2000, 1000+i*20, 2000, 1000+i*20, 2000])
		time.sleep(0.2)
	ppm.stop()
	end = time.time()
	print("{} sends in {:.1f} secs ({:.2f}/s) avg time {:.2f}ms".format(ppm.count, end-start, ppm.count/(end-start), 1000*(end-start)/float(ppm.count)))
