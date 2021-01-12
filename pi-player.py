#!/usr/bin/python3.7
import sys
import os
import signal
import subprocess
import threading
import pyttsx3
import json
import time
from os import walk
import IrDecoder

class PiPlayer:
	def __init__(self):
		self.PATH_TO_MUSIC = r"/home/pi/Music/moms/workout/"
		self.STATE_FILE_NAME = '/home/pi/Documents/pi-player/lastPlayedTrack.json'
		self.albumnum = 0
		self.tracknum = 0
		self.albumList = []
		getVolCommand = 'amixer -c 0 get Headphone | grep -oP "\[\d*%\]" | sed s:[][%]::g'
		self.volumepercent = int(subprocess.getoutput(getVolCommand))
		self.speakEngine = pyttsx3.init()
		self.procHandle = None
		self.currSongIndex = 0

	def readLastPlaybackState(self):
		if (os.path.isfile(self.STATE_FILE_NAME)):  # TODO learn how to check for file exists in the "with open" below and go on without crashing
			with open(self.STATE_FILE_NAME,'r') as stateFileHandle:
				[self.albumnum, self.tracknum] = json.load(stateFileHandle)

	def writeCurrentPlaybackState(self):
		with open(self.STATE_FILE_NAME,'w') as stateFileHandle:
			json.dump([self.albumnum, self.tracknum],stateFileHandle)

	def speakAlbumName(self):
		fullPathSplit = self.albumList[self.albumnum][self.tracknum].split("/")
		albumName = fullPathSplit[-2]
		self.speakEngine.say(albumName)
		self.speakEngine.runAndWait()

	def playSongFile(self, fileName, songIndex):
		print("Now playing", fileName)
		def onExit():
			print("songIndex", songIndex, "killed. currIndex:", self.currSongIndex)
			if self.currSongIndex == songIndex:
				self.playNextTrack()
		def runInThread(onExit):
			self.writeCurrentPlaybackState()
			self.procHandle = subprocess.Popen(["play", '-q', fileName, '-t', 'alsa'])
			self.procHandle.wait()
			onExit()
			return
		thread = threading.Thread(target=runInThread, args=[onExit]) #todo: if nothing points to this thread, does it die by garbage collection?
		thread.start()

	def playNextTrack(self):
		print("Next track")
		sys.stdout.flush()
		self.currSongIndex += 1
		self.procHandle.terminate()
		if self.tracknum < len(self.albumList[self.albumnum]) - 1:
			self.tracknum += 1
		else:
			self.incrementAlbumNum()

		self.playSongFile(self.albumList[self.albumnum][self.tracknum], self.currSongIndex)

	def playPreviousTrack(self):
		print("Previous track")
		sys.stdout.flush()
		self.currSongIndex += 1
		self.procHandle.terminate()
		if self.tracknum > 0:
			self.tracknum -= 1
		else:
			self.decrementAlbumNum()

		self.playSongFile(self.albumList[self.albumnum][self.tracknum], self.currSongIndex)

	def playNextAlbum(self):
		print("Next Album")
		sys.stdout.flush()
		self.currSongIndex += 1
		self.procHandle.terminate()
		self.incrementAlbumNum()
		self.playSongFile(self.albumList[self.albumnum][self.tracknum], self.currSongIndex)

	def incrementAlbumNum(self):
		if self.albumnum < len(self.albumList) - 1:
			self.albumnum += 1
		else:
			self.albumnum = 0
		self.tracknum = 0
		self.speakAlbumName()

	def playPreviousAlbum(self):
		print("Previous album")
		sys.stdout.flush()
		self.currSongIndex += 1
		self.procHandle.terminate()
		self.decrementAlbumNum()
		self.playSongFile(self.albumList[self.albumnum][self.tracknum], self.currSongIndex)

	def decrementAlbumNum(self):
		if self.albumnum > 0:
			self.albumnum -= 1
		else:
			self.albumnum = len(self.albumList) - 1
		self.tracknum = 0
		self.speakAlbumName()

	def volumeUp(self):
		print("Volume up")
		if self.volumepercent <= 95:
			self.volumepercent += 5
			os.system(f"amixer -c 0 sset Headphone {self.volumepercent}%")
			print(f"volume set to {self.volumepercent} %")
		else:
			print("volume all the way up")

	def volumeDown(self):
		print("Volume down")
		if self.volumepercent >= 5:
			self.volumepercent -= 5
			os.system(f"amixer -c 0 sset Headphone {self.volumepercent}%")
			print(f"volume set to {self.volumepercent} %")
		else:
			print("voluume all the way down")

	def playOrStop(self):
		print("Play or stop")
		if self.songPlaying:
			self.songPlaying = False
			sys.stdout.flush()
			self.currSongIndex += 1
			self.procHandle.terminate()
		else:
			self.songPlaying = True
			self.playSongFile(self.albumList[self.albumnum][self.tracknum], self.currSongIndex)

	def start(self):
		for (dirpath, dirnames, filenames) in os.walk(self.PATH_TO_MUSIC):
			if len(filenames) == 0:
				continue
			album = []
			for filename in filenames:
				album.append(dirpath+"/"+filename)
			self.albumList.append(album)

		self.readLastPlaybackState()
		self.writeCurrentPlaybackState()
		self.songPlaying = True
		self.playSongFile(self.albumList[self.albumnum][self.tracknum], self.currSongIndex)

		while True:
			sys.stdout.flush()
			command = IrDecoder.ConvertHex(IrDecoder.getData())
			sys.stdout.flush()

			if (command == "0x3e0e016e9" or command == "0x300ffe21d"): #next track
				self.playNextTrack()
			elif (command == "0x3e0e048b7" or command == "0x300ff629d"): #next Album
				self.playNextAlbum()
			elif (command == "0x3e0e008f7" or command == "0x300ffc23d"): #prev track
				self.playPreviousTrack()
			elif (command == "0x300ff02fd"): #Prev album
				self.playPreviousAlbum()
			elif (command == "0x3e0e0e01f" or command == "0x300ffa25d"): #volume up
				self.volumeUp()
			elif (command == "0x3e0e0d02f" or command == "0x300ff22dd"): #volume down
				self.volumeDown()
			elif (command == "0x300ff906f"): #play/stop
				self.playOrStop()
			else:
				if (len(command) > 5):
					print(f"command {command} not recognized")
					sys.stdout.flush()

if __name__ == "__main__":
	pi_player = PiPlayer()
	pi_player.start()
