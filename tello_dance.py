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
		self.LITTLE_PAUSE = 0.1 # timeout between rc_control commands
		self.speed_side = 20

	def up(self, name="default"):
		#
		pass

	def swing1(self, _):
		#self.dance_right_left(_)
		self.dance_swing2(_)
		# self.patrol()
		# self.draw_spirale()

	def dance_right_left(self, _):
		sign = 1
		while True:
			if self.bridge.changed_beat:
				sign = -1 * sign
				self.bridge.changed_beat = 0
				self.drone.send_rc_control(
					sign * self.speed_side, 0, 0, 0)

		self.stop()

	def dance_swing2(self, _):
		print("Launch swing on music : ")
		speed_side = 20
		speed_up = 40
		sign = 1
		idx = 0
		pos = [(speed_side, 0, speed_up, 0),
			   (-1 * speed_side, 0, -1 * speed_up, 0),
			   (-1* speed_side, 0, speed_up, 0),
			   (speed_side, 0, -speed_up, 0),
			   ]
		rl, fb, td, yaw = pos[0]
		while True:
			if self.bridge.changed_beat:
				self.stop()
				if idx == 4:
					idx = 0
				self.bridge.changed_beat = 0
				rl, fb, td, ya = pos[idx]
				self.drone.send_rc_control(rl, fb, td, yaw)

				idx += 1
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

	#         time.sleep(TEMPO)

	def draw_spirale(self):
		spiral = []
		rayon=100
		for t in np.arange(0, 2*np.pi, 0.1):
			# add (theta, x, y)
			spiral.append( (t, rayon * np.sin(t), rayon * np.cos(t), 0) )

		previous_pos = [spiral[0][1], spiral[0][2], spiral[0][3]]

		for item in spiral	:
			t, x, y, z = item
			pos= [x, y ,z]

			#next_pos = self.difference(previous_pos, pos)
			#x, y, z = next_pos

			print(t, x, y, z)
			print(t, int(x), int(y) , int(z))
			self.drone.go_xyz_speed(int(x), int(y) , int(z), 50)


if __name__ == '__main__':
	td = TelloDance("drone", TelloBridge())
	td.draw_spirale()

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