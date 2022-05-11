# Use the sounddevice module
# http://python-sounddevice.readthedocs.io/en/0.3.10/

import numpy as np
import sounddevice as sd
import playsound
import librosa
import vlc

import time

class TelloSound():
	def __init__(self):
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

if __name__ == '__main__':
	tb = TelloSound()
	tb.bip()
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