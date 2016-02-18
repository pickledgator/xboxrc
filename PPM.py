#!/usr/bin/env python

# PPM.py
# 2016-02-16
# Public Domain

import time
import pigpio
from threading import Timer

class PPM:

   GAP=100
   #WAVES=3

   def __init__(self, pi, gpio, channels=8, frame_ms=500):
      self.pi = pi
      self.gpio = gpio

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

      self._widths = [1000 for c in channels] # init to min channels

      self._waves = [None, None] # list to keep track of the next waves, maintains gapless transition on updates

      pi.write(gpio, pigpio.LOW) # start gpio low

      self.shouldExit = False

   def start(self):
      self.sendThread = threading.Thread(name='ppmsend', target=self.send)
      self.sendThread.daemon = True
      self.sendThread.start()

   def _update(self):
      # if the waves list is full, send the first one
      if len(self._waves) == 2:
         self._waves.pop(0) # pop off the first wave

      # calculate the next wave to be added
      wf =[]
      micros = 0
      for i in self._widths:
         wf.append(pigpio.pulse(0, 1<<self.gpio, self.GAP))
         wf.append(pigpio.pulse(1<<self.gpio, 0, i))
         micros += (i+self.GAP)
      # off for the remaining frame period
      wf.append(pigpio.pulse(0, 1<<self.gpio, self.frame_us-micros))

      self.pi.wave_add_generic(wf)
      wid = self.pi.wave_create()
      self._waves.append(wid)

      #self.pi.wave_send_repeat(wid)
      #self._wid[self._next_wid] = wid
      #print("create", self._next_wid, "with", wid)

      #self._next_wid += 1
      #if self._next_wid >= self.WAVES:
      #   self._next_wid = 0

      #wid = self._wid[self._next_wid]
      #if wid is not None:
         #print("delete", self._next_wid, "with", wid)
      #   self.pi.wave_delete(wid)
      #   self._wid[self._next_wid] = None

   def send(self):
      if self.shouldExit:
         return

      # if the tx is still sending the last wave, wait until its done
      if self.pi.wave_tx_busy():
         self.sendTimer = Timer(0.001,self.send)
         self.sendTimer.start()
         return

      if self._waves is not None:
         self.pi.wave_send_once(self._waves[0])
         print("sending wid {}".format(self._waves[0]))
      else:
         print("wid is None")
         # wait a bit before trying again to send
         self.sendTimer = Timer(0.5,self.send)
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

   # updates = 0
   # start = time.time()
   # for chan in range(8):
   #    for pw in range(1000, 2000, 5):
   #       ppm.update_channel(chan, pw)
   #       updates += 1
   #       time.sleep(0.03)
   # end = time.time()
   # secs = end - start
   # print("{} updates in {:.1f} seconds ({}/s)".format(updates, secs, int(updates/secs)))

   ppm.update_channels([1000, 1000, 1000, 1000, 1000, 1000, 1000, 2000])

   time.sleep(2)

   ppm.update_channels([1000, 2000, 1000, 2000, 1000, 2000, 1000, 2000])

   ppm.send()

   time.sleep(2)

   ppm.cancel()

   pi.stop()
