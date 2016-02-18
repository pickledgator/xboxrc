#!/usr/bin/env python

# PPM.py
# 2016-02-16
# Public Domain

import pigpio

class X:

   GAP=100
   WAVES=3

   def __init__(self, pi, gpio, channels=8, frame_ms=27):
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

      self._widths = [1000] * channels # set each channel to minimum pulse width

      self._wid = [None]*self.WAVES
      self._next_wid = 0

      pi.write(gpio, pigpio.LOW)

   def _update(self):
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
      self.pi.wave_send_repeat(wid)
      self._wid[self._next_wid] = wid
      #print("create", self._next_wid, "with", wid)

      self._next_wid += 1
      if self._next_wid >= self.WAVES:
         self._next_wid = 0

      wid = self._wid[self._next_wid]
      if wid is not None:
         #print("delete", self._next_wid, "with", wid)
         self.pi.wave_delete(wid)
         self._wid[self._next_wid] = None

   def update_channel(self, channel, width):
      self._widths[channel] = width
      self._update()

   def update_channels(self, widths):
      self._widths[0:len(widths)] = widths[0:self.channels]
      self._update()

   def cancel(self):
      self.pi.wave_tx_stop()
      for i in self._wid:
         if i is not None:
            self.pi.wave_delete(i)

if __name__ == "__main__":

   import time
   import PPM
   import pigpio

   pi = pigpio.pi()

   if not pi.connected:
      exit(0)

   ppm = PPM.X(pi, 6)

   updates = 0
   start = time.time()
   for chan in range(8):
      for pw in range(1000, 2000, 5):
         ppm.update_channel(chan, pw)
         updates += 1
         time.sleep(0.03)
   end = time.time()
   secs = end - start
   print("{} updates in {:.1f} seconds ({}/s)".format(updates, secs, int(updates/secs)))

   ppm.update_channels([1000, 2000, 1000, 2000, 1000, 2000, 1000, 2000])

   time.sleep(2)

   ppm.cancel()

   pi.stop()
