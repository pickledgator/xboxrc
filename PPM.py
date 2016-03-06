#!/usr/bin/env python

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
	def __init__(self, gpio, channels=8, frame_ms=27, gap_us=100, debug=False):
		self.pi = pigpio.pi()

		if not self.pi.connected:
			print("pigpio error, is the pigpiod running?")
			exit(0)

		self.gpio = gpio
		self.gap_us = gap_us
		self.debug = debug

		if frame_ms < 5:
			frame_ms = 5
			channels = 2
		elif frame_ms > 500:
			frame_ms = 500

		self.frame_us = int(frame_ms * 1000)
		self.frame_s = frame_ms / 1000.0

		if channels < 1:
			channels = 1
		elif channels > (frame_ms // 2):
			channels = int(frame_ms // 2)

		self.channels = channels

		self.widths = [1000 for c in range(channels)] # init to min channels
		self.waves = []

		self.pi.write(gpio, pigpio.LOW) # start gpio low

		self.shouldExit = False
		self.count = 0
		self.lastSendTime = 0
		self.lastWavesLength = 0
		
		_ppms.append(self)
		signal.signal(signal.SIGINT, _signalHandler)
		signal.signal(signal.SIGTERM, _signalHandler)
		signal.signal(signal.SIGHUP, _signalHandler)

	def start(self):
		self.sendThread = threading.Thread(name='ppmsend', target=self.send)
		self.sendThread.daemon = True
		self.sendThread.start()

	def update_waves(self):
		if self.debug:
			print("Updating channels {}".format(' '.join(str(s) for s in self.widths)))

		# calculate the next wave to be added
		wf =[]
		micros = 0
		for i in self.widths:
			wf.append(pigpio.pulse(0, 1<<self.gpio, self.gap_us))
			wf.append(pigpio.pulse(1<<self.gpio, 0, i))
			micros += (i+self.gap_us)
		# off for the remaining frame period
		wf.append(pigpio.pulse(0, 1<<self.gpio, self.frame_us-micros))

		# add it to our 2 element list
		self.pi.wave_add_generic(wf)
		wid = self.pi.wave_create()
		
		# if there's already a wave in the list, pop it off, we only want max 1 wave in the list
		if len(self.waves) > 0:
			self.pi.wave_delete(self.waves[0])
			self.waves.pop()

		self.waves.append(wid)

	def send(self):
		if self.shouldExit: 
			return

		if len(self.waves) == 0:
			donothing = 1
			#print("{} No waves in list to send".format(time.time()))
		else:
			self.pi.wave_send_using_mode(self.waves[0], pigpio.WAVE_MODE_REPEAT_SYNC)
			print("{} Sending wid {}".format(time.time(), self.waves[0]))
			self.pi.wave_delete(self.waves[0])
			self.waves.pop()
		
		remaining = self.lastSendTime + self.frame_s - time.time()
		if remaining < self.frame_s/2.0:
			remaining += self.frame_s
		self.lastSendTime = time.time()
		self.sendTimer = threading.Timer(remaining,self.send)
		self.sendTimer.start()

		self.count += 1

	def update_channel(self, channel, width):
		if channel > self.channels-1:
			print("Invalid channel {} > max channel {}".format(channel, self.channels-1))
			return
		# check for valid input
		width = min(max(1000,width), 2000)
		self.widths[channel] = width
		self.update_waves()

	def update_channels(self, widths):
		if not len(widths) == self.channels:
			print("widths list must match number of channels")
			return
		# check for valid input
		widths = [min(max(1000,w), 2000) for w in widths]
		self.widths[0:len(widths)] = widths[0:self.channels]
		self.update_waves()

	def stop(self):
		print("Stopping waveforms")
		self.shouldExit = True
		time.sleep(0.5) # wait a bit for the thread to exit
		self.pi.wave_tx_stop()
		self.pi.wave_clear()
		for w in self.waves:
			if w is not None:
				self.pi.wave_delete(w)
		self.pi.stop()		

if __name__ == "__main__":

	# build ppm using gpio 6
	ppm = PPM(6)
	ppm.start()
	start = time.time()
	# test invalid range inputs
	ppm.update_channels([3000, 500, -1000, 1000, 1000, 1000, 1000, 2000])
	time.sleep(0.5)
	# test wrong number of channels in update list
	ppm.update_channels([2000, 1000, 2000, 1000, 2000, 1000, 2000])
	# update individual channel
	ppm.update_channel(6, 500)
	# test channel out of range
	ppm.update_channel(9, 1500)
	ppm.update_channels([1500, 2000, 1000, 2000, 1000, 2000, 1000, 2000])
	ppm.update_channels([1501, 2000, 1000, 2000, 1000, 2000, 1000, 2000])
	for i in range(1,20):
		ppm.update_channels([1000+i*20, 2000, 1000+i*20, 2000, 1000+i*20, 2000, 1000+i*20, 2000])
		time.sleep(0.1)
	end = time.time()
	ppm.stop()
	print("{} sends in {:.1f} secs ({:.2f}/s) avg time {:.2f}ms".format(ppm.count, end-start, ppm.count/(end-start), 1000*(end-start)/float(ppm.count)))
