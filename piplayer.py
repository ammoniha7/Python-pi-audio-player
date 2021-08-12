#!/usr/bin/python3.7
import json
import os
import subprocess

import playsound
from gtts import gTTS

import userinput
from playsong import PlaySong

# todo: make sure stereo channels working

class PiPlayer:
	MUSIC_PATH = "/home/pi/Music/moms/workout/"
	# MUSIC_PATH = r"/media/pi/Moms Eh/moms/workout/"
	STATE_FILE_NAME = "/home/pi/Documents/piplayer/lastPlayedTrack.json" # todo: can I just use a relative path for this?
	SPOKEN_ALBUM_FILE = "/home/pi/Documents/piplayer/currAlbumName.mp3"

	def __init__(self):
		self.album_num = 0
		self.track_num = 0
		self.album_list = []
		self.volume_percent = self._get_curr_vol_percent()
		self.volume_percent = 95
		self.play_song_thread = None
		self.read_last_playback_state()

		for dirpath, dirnames, filenames in os.walk(PiPlayer.MUSIC_PATH):
			if len(filenames) == 0:
				continue
			album = []
			for filename in filenames:
				album.append(os.path.join(dirpath, filename))
			self.album_list.append(album)

	def _get_curr_vol_percent(self):
		GET_VOL_CMD = 'amixer -c 0 get Headphone | grep -oP "\[\d*%\]" | sed s:[][%]::g'
		return int(subprocess.getoutput(GET_VOL_CMD))

	def read_last_playback_state(self):
		if (os.path.isfile(PiPlayer.STATE_FILE_NAME)):  # TODO learn how to check for file exists in the "with open" below and go on without crashing
			with open(PiPlayer.STATE_FILE_NAME,'r') as stateFileHandle: # todo: if last playback is now out of range (maybe user deleted some albums/songs), set to 0
				[self.album_num, self.track_num] = json.load(stateFileHandle)

	def write_current_playback_state(self):
		with open(PiPlayer.STATE_FILE_NAME,'w') as stateFileHandle:
			json.dump([self.album_num, self.track_num], stateFileHandle)

	def speak_album_name(self):
		full_path_split = self.album_list[self.album_num][self.track_num].split("/")
		album_name = full_path_split[-2]
		tts = gTTS(text=album_name, lang="en")
		filename = PiPlayer.SPOKEN_ALBUM_FILE
		tts.save(filename) # todo: play album name directly without saving to file first.
		playsound.playsound(filename)

	def play_song_file(self, file_name):
		print("now playing: album_num=", self.album_num, "track_num=", self.track_num, file_name, flush=True)
		self.write_current_playback_state()
		self.play_song_thread = PlaySong(self, file_name)
		self.play_song_thread.start()

	def play_new_song(self, song_index_changer):
		self.play_song_thread.user_stop()
		song_index_changer()
		self.play_song_file(self.album_list[self.album_num][self.track_num])

	def play_next_song(self):
		print("next song", flush=True)
		def song_index_changer():
			if self.track_num < len(self.album_list[self.album_num]) - 1:
				self.track_num += 1
			else:
				self._increment_album_num()
		self.play_new_song(song_index_changer)

	def play_previous_song(self):
		print("previous song", flush=True)
		def song_index_changer():
			if self.track_num > 0:
				self.track_num -= 1
			else:
				self._decrement_album_num()
		self.play_new_song(song_index_changer)

	def play_next_album(self):
		print("next album", flush=True)
		self.play_new_song(self._increment_album_num)

	def play_previous_album(self):
		print("previous album", flush=True)
		self.play_new_song(self._decrement_album_num)

	def _increment_album_num(self):
		if self.album_num < len(self.album_list) - 1:
			self.album_num += 1
		else:
			self.album_num = 0
		self.track_num = 0
		self.speak_album_name()

	def _decrement_album_num(self):
		if self.album_num > 0:
			self.album_num -= 1
		else:
			self.album_num = len(self.album_list) - 1
		self.track_num = 0
		self.speak_album_name()

	def volume_up(self):
		print("volume up", flush=True)
		if self.volume_percent <= 95:
			self.volume_percent += 5
			os.system(f"amixer -c 0 sset Headphone {self.volume_percent}%") # todo: isn't os.system deprecated?
			print(f"volume set to {self.volume_percent}%", flush=True)
		else:
			print("volume all the way up", flush=True)

	def volume_down(self):
		print("volume down", flush=True)
		if self.volume_percent >= 5:
			self.volume_percent -= 5
			os.system(f"amixer -c 0 sset Headphone {self.volume_percent}%")
			print(f"volume set to {self.volume_percent}%", flush=True)
		else:
			print("volume all the way down", flush=True)

	def song_play_pause(self):
		print("play/pause", flush=True)
		self.play_song_thread.user_play_pause()

	def start(self, input_device):
		self.play_song_file(self.album_list[self.album_num][self.track_num])
		while True:
			input_device.wait_for_input(self)

	def _print_current_state_debug(self):
		print("album num:", self.album_num)
		print("track num:", self.track_num)
		print("vol percent:", self.volume_percent)
		print("play song thread:", self.play_song_thread)

if __name__ == "__main__":
	control = userinput.IRRemoteControl()
	PiPlayer().start(control)
