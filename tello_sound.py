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

import random
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

		self.musics = { "default1" : "audio/daddys_car.mp3",
						"default2": "audio/brahms_hungarian_dance_5.mp3",
						#"default3" : "audio/busta_rhymes_hits_for_days.mp3"
						}

		self.beats = {}
		for k, v in self.musics.items():
			self.beats[k] = self.get_beats(v)

		rand_key = random.choice(list(self.musics.keys()))
		self.random_music = self.musics[rand_key]
		self.random_music_beat_times = self.beats[rand_key]

		self.bridge = bridge

		#
		# to play once
		# self.add_clicks_all()
		# conversion to  wav was needed as on windows we could not load the mp3 music fiel with librosa
		# self.convert_to_wav(mp3file)

	def play_music(self, name="", with_beats=False):
		"""
		Plays music obviously
		Non blocking  call, music will play in background
		need to handle interruption in some way
		Args:
			name:

		Returns:

		"""
		if name == "":
			name = self.random_music

		if with_beats:
			name = name[:-4]+"_beats.wav"

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

	def add_clicks_all(self):
		for m in list(self.musics.keys()):
			self.add_clicks(self.musics[m])

	def add_clicks(self, name):
		print("adding click to", name)
		self.generate_beats_on_track(name)

	def generate_beats_on_track(self, name):
		#name = self.music
		if len(name) > 4 and name[-3:] == 'mp3':
			self.convert_to_wav(name)
			name = f"{name[:-4]}.wav"
		elif len(name) > 4 and name[-3:] == 'wav':
			print("Loadin wav file")
		else:
			print("not tested over this file type - at your own risk")

		print("Loading file ", name)
		x, sr = librosa.load(name)

		print("Extracting beats")
		tempo, beat_times = librosa.beat.beat_track(x, sr=sr, start_bpm=50, units='time')

		# ugly hack to divide by 2 the beat rate
		beat_times = self.sample_half(beat_times)

		clicks = librosa.clicks(beat_times, sr=sr, length=len(x))
		data = x + clicks
		#print(tempo)
		#print(beat_times)
		self.random_music_beat_times = self.sample_half(beat_times)

		output_file = os.path.join(f"{name[:-4]}_beats.wav")
		print("Wriiting clicks to file", output_file)
		# Write out audio as 24bit PCM WAV
		sf.write(output_file, data, sr, subtype='PCM_24')

		# self.play_music(output_file)

	def get_beats(self, name):
		print("Getting beats from file", name)
		x, sr = librosa.load(name)

		print("Extracting beats")
		_, beat_times = librosa.beat.beat_track(x, sr=sr, start_bpm=50, units='time')

		return beat_times


	def convert_to_wav(self, mp3_file):
		if len(mp3_file) > 4 and mp3_file[-3:] == 'mp3':
			x, sr = librosa.load(mp3_file)
			# Write out audio as 24bit PCM WAV
			output_file = os.path.join(f"{mp3_file[:-4]}.wav")
			print(output_file)
			sf.write(output_file, x, sr, subtype='PCM_24')
		else:
			print("not an mp3 file, not converted")

	def sample_half(self, l):
		l = list(l)[::-1]
		l = [b for i, b in enumerate(l) if i%2 == 0 ]
		return l

	def go_for_music(self, key='', rand=False):
		if rand:
			key = random.choice(list(self.musics.keys()))
		else:
			key = ''
		print(key)
		if key == '':
			name = self.random_music
			beats = self.sample_half(self.random_music_beat_times)
		else:
			name = self.musics[key]
			print(name)
			print(key)
			beats = self.sample_half(self.beats[key])
			print(beats)
		print("Launch with beats", name)
		#beats = list(self.beat_times)[::-1]
		#beats = [b for i, b in enumerate(beats) if i%2 == 0 ]

		next_beat = beats.pop()
		t = time.time()
		timeout = t + 60
		start_time = t
		#print(beat)
		self.play_music(name=name, with_beats=True)
		while True:
			if time.time() - start_time < next_beat:
				pass
			else:
				#self.bip()
				self.bridge.changed_beat = 1
				# TODO envoyer event à thread dance

				next_beat = beats.pop()



if __name__ == '__main__':
	tb = TelloSound(TelloBridge())
	tb.add_clicks_all()
	sys.exit(0)
	#tb.play_music(name='audio/daddys_car.mp3', with_beats=True)
	#time.sleep(3)
	#tb.stop_music()
	tb.go_for_music(rand=True)
	time.sleep(3)
	tb.stop_music()
	#tb.convert_to_wav("audio/daddys_car.mp3")
	#print(tb.music)
	#tb.load_libro()
	#tb.go()



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