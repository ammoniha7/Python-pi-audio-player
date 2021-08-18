#!/usr/bin/python3.7
import json
import os
import subprocess
from pathlib import Path

import userinput
from playsong import PlaySong
from speaktext import speak_text


# todo: make sure stereo channels working

class PiPlayer:
	MUSIC_PATH = "/home/pi/Music/Dynamix"
	# MUSIC_PATH = r"/media/pi/Moms Eh/Music/Dynamix"
	STATE_FILE_PATH = os.path.join(Path(__file__).resolve().parent, "state.json")
	VOLUME_CHANGE_DELTA = 5

	def __init__(self):
		self.album_num = 0
		self.track_num = 0
		self.album_list = []
		self.volume_percent = self._get_curr_vol_percent()
		self.play_song_thread = None
		self._build_album_list()
		self._read_last_playback_state()

	def _build_album_list(self):
		for dirpath, dirnames, filenames in os.walk(PiPlayer.MUSIC_PATH):
			if len(filenames) == 0:
				continue
			album = []
			for filename in filenames:
				album.append(os.path.join(dirpath, filename))
			album.sort(key=lambda path: path.split("/")[-1])
			self.album_list.append(album)
		self.album_list.sort(key=lambda album: album[0].split("/")[-2])
		if len(self.album_list) == 0:
			raise Exception("No audio found at path: " + PiPlayer.MUSIC_PATH)

	def _get_curr_vol_percent(self):
		GET_VOL_CMD = 'amixer -c 0 get Headphone | grep -oP "\[\d*%\]" | sed s:[][%]::g'
		return int(subprocess.getoutput(GET_VOL_CMD))

	def _read_last_playback_state(self):
		if os.path.isfile(PiPlayer.STATE_FILE_PATH):
			with open(PiPlayer.STATE_FILE_PATH, 'r') as state:
				[self.album_num, self.track_num] = json.load(state)
			# in case the user deleted some albums/tracks since last state save, check that indexes are within range
			if self.album_num > len(self.album_list) - 1 or self.track_num > len(self.album_list[self.album_num]) - 1:
				self.album_num = 0
				self.track_num = 0

	def _write_current_playback_state(self):
		with open(PiPlayer.STATE_FILE_PATH, 'w') as state:
			json.dump([self.album_num, self.track_num], state)

	def _speak_album_name(self):
		full_path_split = self.album_list[self.album_num][self.track_num].split("/")
		album_name = full_path_split[-2]
		speak_text(album_name)

	def play_song_file(self, file_name):
		print("now playing: album_num=", self.album_num, "track_num=", self.track_num, file_name, flush=True)
		self._write_current_playback_state()
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
		self._speak_album_name()

	def _decrement_album_num(self):
		if self.album_num > 0:
			self.album_num -= 1
		else:
			self.album_num = len(self.album_list) - 1
		self.track_num = 0
		self._speak_album_name()

	def volume_up(self):
		print("volume up", flush=True)
		self._set_volume_percent(PiPlayer.VOLUME_CHANGE_DELTA)

	def volume_down(self):
		print("volume down", flush=True)
		self._set_volume_percent(-PiPlayer.VOLUME_CHANGE_DELTA)

	def _set_volume_percent(self, delta):
		MAX_VOL_PERCENT = 100
		MIN_VOL_PERCENT = 0
		self.volume_percent += delta
		self.volume_percent = max(MIN_VOL_PERCENT, min(self.volume_percent, MAX_VOL_PERCENT))
		SET_VOL_CMD = ["amixer", "-c", "0", "sset", "Headphone", str(self.volume_percent) + "%"]
		self.song_play_pause()
		subprocess.run(SET_VOL_CMD)
		speak_text(str(self.volume_percent) + " percent")
		self.song_play_pause()

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
