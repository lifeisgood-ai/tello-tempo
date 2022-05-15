#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Use the sounddevice module
# http://python-sounddevice.readthedocs.io/en/0.3.10/

import time
import numpy as np

from tello_bridge import TelloBridge

class TelloDance():
	def __init__(self, drone, bridge: TelloBridge):
		self.drone = drone
		self.bridge = bridge

	def up(self, name="default"):
		#
		pass

	def swing1(self, _):
		print("Launch swing on music : ")
		speed_side = 20
		sign = 1
		while True:
			if self.bridge.changed_beat:
				sign = -1 * sign
				self.bridge.changed_beat = 0
				self.drone.send_rc_control(sign * speed_side, 0, 0, 0)


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

	def patrol(self):
		"""
        Dessine un arc de cercle et se retourne
        Espae nécessaire environ 1.5m
        """
		self.drone.curve_xyz_speed(25, -25, 0, 150, 25, 0, 50)
		time.sleep(1)
		self.drone.stop()
		self.drone.curve_xyz_speed(-25, 25, 0, -150, -25, 0, 50)
		time.sleep(1)
		self.stop()

	def stop(self):
		self.drone.send_rc_control(0, 0, 0, 0)
		time.sleep(.1)

	def move_spirale(self, t, pos):
		return [np.cos(t) * 10, np.sin(t) * 10, pos[2] + t, 0]

	def difference(self, list1, list2):
		zip_object = zip(list1, list2)
		difference = []
		for list1_i, list2_i in zip_object:
			difference.append(list2_i - list1_i)
		return difference

	def run_spirale(self):
		TEMPO=0.05
		t=0
		pos=[20, 20, 0, 0]
		speed=50
		PADDING=10

		next_pos = pos
		for k in range(5):
			t+=1
			pos_ = self.move_spirale(t, next_pos)
			next_pos = self.difference(next_pos, pos_)
			if next_pos[0] > 0:
				next_pos[0]+=PADDING
			else:
				next_pos[0]-=PADDING
			if next_pos[1] > 0:
				next_pos[1]+=PADDING
			else:
				next_pos[1]-=PADDING
			print(t, next_pos)
			print('before move')

			self.drone.go_xyz_speed(int(next_pos[0]), int(next_pos[1]), int(next_pos[2])+PADDING, speed)
			print("move " , int(next_pos[0]), int(next_pos[1]), int(next_pos[2])+PADDING, speed)
			print('move done')
	#         time.sleep(TEMPO)

if __name__ == '__main__':
	td = TelloDance("drone", TelloBridge())
	td.spirale("b")

	#td.stop()
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