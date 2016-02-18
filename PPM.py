#!/usr/bin/env python

# PPM.py
# 2016-02-16
# Public Domain

import time
import pigpio
import threading
from threading import Timer

class PPM:
	def __init__(self, pi, gpio, channels=8, frame_ms=27, gap_ms=100):
		self.pi = pi
		self.gpio = gpio
		self.gap = gap_ms

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

		pi.write(gpio, pigpio.LOW) # start gpio low

		self.shouldExit = False
		self.count = 0

	def start(self):
		self.sendThread = threading.Thread(name='ppmsend', target=self.send)
		self.sendThread.daemon = True
		self.sendThread.start()

	def _update(self):
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
		if self.shouldExit:
			return

		# if the tx is still sending the last wave, wait until its done
		if self.pi.wave_tx_busy():
			self.sendTimer = Timer(0.0001,self.send)
			self.sendTimer.start()
			return

		if len(self._waves) > 0:
			self.pi.wave_send_once(self._waves[0])
			if len(self._waves) > 1:
				self._waves.pop(0) # if there's two items in our list stack, pop the first one, so we get to the next queued one
	  		self.count += 1
			print("sending wid {}".format(self._waves[0]))
		else:
			print("wid is None at waves[0]")
			# wait a bit before trying again to send
			self.sendTimer = Timer(0.01,self.send)
			self.sendTimer.start()
			return

		self.send() # repeat send

	def update_channel(self, channel, width):
		self._widths[channel] = width
		self._update()

	def update_channels(self, widths):
		self._widths[0:len(widths)] = widths[0:self.channels]
		self._update()

	def cancel(self):
		print("Stopping waveforms")
		self.shouldExit = True
		self.sendTimer.cancel()
		self.pi.wave_tx_stop()
		for w in self._waves:
			if w is not None:
				self.pi.wave_delete(w)

if __name__ == "__main__":

	pi = pigpio.pi()

	if not pi.connected:
		exit(0)

	ppm = PPM(pi, 6)

	ppm.update_channels([1000, 1000, 1000, 1000, 1000, 1000, 1000, 2000])

	time.sleep(2)

	ppm.update_channels([1000, 2000, 1000, 2000, 1000, 2000, 1000, 2000])

	start = time.time()
	ppm.start()
	
	for i in range(1,10):
		time.sleep(1)

	ppm.cancel()
	end = time.time()
	print("{} sends in {:.1f} secs ({:.2f}/s) avg time {:.2f}ms".format(ppm.count, end-start, ppm.count/(end-start), 1000*(end-start)/float(ppm.count)))


	time.sleep(3)

	pi.stop()
