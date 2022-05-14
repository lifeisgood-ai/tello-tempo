#!/usr/bin/env python
# -*- coding: utf-8 -*-


# http://python-sounddevice.readthedocs.io/en/0.3.10/
import os
import sys

import numpy as np
import sounddevice as sd
import soundfile as sf
import playsound
import librosa
import vlc

import time
from tello_bridge import TelloBridge

class TelloSound():
	def __init__(self, bridge: TelloBridge):
		# Samples per second
		self.sps = 44100

		# Frequency / pitch
		self.freq_hz = 440.0

		# Duration
		self.duration_s = 0.1

		# Attenuation so the sound is reasonable
		self.atten = 0.3

		# NumpPy magic to calculate the waveform
		self.each_sample_number = np.arange(self.duration_s * self.sps)
		self.waveform = np.sin(2 * np.pi * self.each_sample_number * self.freq_hz / self.sps)
		self.waveform_quiet = self.waveform * self.atten

		self.player = vlc.MediaPlayer()

		self.bridge = bridge
		self.load_libro()

	def play_music(self, name='audio/daddys_car.mp3'):
		if not self.player.is_playing():
			self.player = vlc.MediaPlayer(name)
			self.player.audio_set_volume(100)
			self.player.play()

	def stop_music(self):
		if self.player.is_playing():
			self.player.stop()

	def bip(self):
		# Play the waveform out the speakers
		sd.play(self.waveform_quiet, self.sps)
		time.sleep(self.duration_s)
		sd.stop()


	def load_libro(self):
		name = 'audio/daddys_car.mp3'
		name = 'audio/brahms_hungarian_dance_5.mp3'

		print("Loading file")
		x, sr = librosa.load(name)

		print("Extracting beats")
		tempo, beat_times = librosa.beat.beat_track(x, sr=sr, start_bpm=50, units='time')
		clicks = librosa.clicks(beat_times, sr=sr, length=len(x))
		data = x + clicks
		#print(tempo)
		#print(beat_times)
		self.beat_times = beat_times

		# print("Wriiting result to file")
		# # Write out audio as 24bit PCM WAV
		# output_file = os.path.join(f"{name}.wav")
		# sf.write(output_file, data, sr, subtype='PCM_24')

		# self.play_music(output_file)


	def go(self):
		beat = list(self.beat_times)[::-1]
		beat = [b for i, b in enumerate(beat) if i%2 == 0 ]

		next_beat = beat.pop()
		t = time.time()
		timeout = t + 60
		start_time = t
		#print(beat)
		self.play_music(name='audio/brahms_hungarian_dance_5_beat.wav')
		while True:
			if time.time() - start_time < next_beat:
				pass
			else:
				#self.bip()
				self.bridge.changed_beat = 1
				# TODO envoyer event à thread dance

				next_beat = beat.pop()



if __name__ == '__main__':
	tb = TelloSound()
	tb.load_libro()
	tb.go()



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