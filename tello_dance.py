#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Use the sounddevice module
# http://python-sounddevice.readthedocs.io/en/0.3.10/

import time

class TelloDance():
	def __init__(self, drone):
		self.drone = drone

	def up(self, name="default"):
		#
		pass

	def swing1(self):
		print("Launch swing")
		for i in range(4):
			self.drone.send_rc_control(-20, 0, 0, 0)  # left
			time.sleep(2)
			self.stop()
			time.sleep(.1)
			self.drone.send_rc_control(20, 0, 0, 0)  # right
			time.sleep(2)
			self.stop()
			time.sleep(.1)

		self.stop()

	def swing(self):
		print("Launch swing")
		for i in range(4):
			self.drone.send_rc_control(-20, 0, 0, 100) # left
			time.sleep(2)
			self.stop()
			time.sleep(.1)
			self.drone.send_rc_control(20, 0, 0, -100) # right
			time.sleep(2)
			self.stop()
			time.sleep(.1)

		self.stop()

	def stop(self):
		self.drone.send_rc_control(0, 0, 0, 0)


if __name__ == '__main__':
	td = TelloDance()
	td.stop()
# from pydub.playback import play
# from pydub import AudioSegment

# TONE=librosa.tone(440, duration=1)
# import numpy as np
# from scipy.io.wavfile import write
# noise = np.random.uniform(-1,1,100000)
# write('noise.wav', len(noise), noise)

# def beat():
#     sound = AudioSegment.from_wav('noise.wav')
#     play(sound)
#     # play('noise')