#!/usr/bin/python3.7
import time
import sys
import os
import signal
import subprocess
import RPi.GPIO as GPIO
import pyttsx3
import datetime
import json
from datetime import datetime
from os import walk

global albumnum
albumnum = 0
global tracknum
tracknum = 0
global songplaying
songplaying = 1
global procHandle
global fileNum
fileNum = 0
global maxFileNum
global fileList
fileList = []
global volumepercent
volumepercent = 80
global pathToMusic
pathToMusic = r"/media/pi/Moms Eh/moms/workout/"
global stateFileName
stateFileName = '/home/pi/Documents/python project for mom/lastPlayedTrack.json'
#global stateFileHandle

IRsignalpin = 11
GPIO.setmode(GPIO.BOARD)
GPIO.setup(IRsignalpin,GPIO.IN)


#Defines Subs
def ConvertHex(BinVal): #Converts binary data to hexidecimal
	tmpB2 = int(str(BinVal), 2)
	return hex(tmpB2)

def getData(): #Pulls data from sensor
	num1s = 0 #Number of consecutive 1s
	command = [] #Pulses and their timings
	binary = 1 #Decoded binary command
	previousValue = 0 #The previoos.system("amixer sset HDMI 0%")us pin state
	value = GPIO.input(IRsignalpin) #Current pin state
	
	while value: #Waits until pin is pulled low
		global tracknum
		global albumnum
		value = GPIO.input(IRsignalpin)
		poll = procHandle.poll()
		if poll != None and songplaying == 1:
			if tracknum < len(albumList[albumnum]) - 1:
				tracknum += 1
			else:
				if albumnum < len(albumList) - 1:
					albumnum += 1
				else:
					albumnum = 0
				tracknum = 0
				kickOff(albumList[albumnum][tracknum])
				print(albumList[albumnum][tracknum])
		else: 
			continue 
	
	startTime = datetime.now() #Sets start time
	
	while True:
		if value != previousValue: #Waits until change in state occurs
			now = datetime.now() #Records the current time
			pulseLength = now - startTime #Calculate time in between pulses
			startTime = now #Resets the start time
			command.append((previousValue, pulseLength.microseconds)) #Adds pulse time to array (previous val acts as an alternating 1 / 0 to show whether time is the on time or off time)
		
		#Interrupts code if an extended high period is detected (End Of Command)	
		if value:
			num1s += 1
		else:
			num1s = 0
		
		if num1s > 10000:
			break
		
		#Reads values again
		previousValue = value
		value = GPIO.input(IRsignalpin)
		
	#Covers data to binary
	for (typ, tme) in command:
		if typ == 1:
			if tme > 1000: #According to NEC protocol a gap of 1687.5 microseconds repesents a logical 1 so over 1000 should make a big enough distinction
				binary = binary * 10 + 1
			else:
				binary *= 10
				
	if len(str(binary)) > 34: #Sometimes the binary has two rouge charactes on the end
		binary = int(str(binary)[:34])
		
	return binary

def readLastPlaybackState():
	global albumnum
	global tracknum
	global stateFileName
#	global stateFileHandle
	if (os.path.isfile(stateFileName)):  # TODO learn how to check for file exists in the "with open" below and go on without crashing
		with open(stateFileName,'r') as stateFileHandle:
			[albumnum,tracknum] = json.load(stateFileHandle)

def writeCurrentPlaybackState():
	global albumnum
	global tracknum
#	global stateFileHandle
	global stateFileName
	with open(stateFileName,'w') as stateFileHandle:
		json.dump([albumnum,tracknum],stateFileHandle)

albumList = []
for (dirpath, dirnames, filenames) in os.walk(pathToMusic):
	if len(filenames) == 0:
		continue
	album = []
	for filename in filenames:
		album.append(dirpath+"/"+filename) 
	albumList.append(album)
for album in albumList:
	print("====ALBUM====")
	for track in album:
		print(track)
print("====END=====")

readLastPlaybackState()
writeCurrentPlaybackState()
#stateFileHandle = open(stateFileName,'w')

speakEngine = pyttsx3.init()

def kickOff(fileName):
	global procHandle
	writeCurrentPlaybackState()
	procHandle = subprocess.Popen(["play", '-q', fileName])

kickOff(albumList[albumnum][tracknum])

while True:
	sys.stdout.flush()
	command = ConvertHex(getData())
	sys.stdout.flush()

	if (command == "0x3e0e016e9" or command == "0x300ffe21d"): #next track
		print(f"{command} - Next track")
		sys.stdout.flush()
		os.kill(procHandle.pid, signal.SIGTERM)
		if tracknum < len(albumList[albumnum]) - 1:
			tracknum += 1
		else:
			if albumnum < len(albumList) - 1:
				albumnum += 1
			else:
				albumnum = 0
			tracknum = 0

		kickOff(albumList[albumnum][tracknum])
		print(albumList[albumnum][tracknum])
	
	elif (command == "0x3e0e048b7" or command == "0x300ff629d"): #next Album
		print(f"{command} - Next Album")
		sys.stdout.flush()
		os.kill(procHandle.pid, signal.SIGTERM)

		if albumnum < len(albumList) - 1:
			albumnum += 1
		else:
			albumnum = 0
		tracknum = 0
		
		speakEngine.say(albumList[albumnum][tracknum])
		speakEngine.runAndWait()
		kickOff(albumList[albumnum][tracknum])
		print(albumList[albumnum][tracknum])
		
	elif (command == "0x3e0e008f7" or command == "0x300ffc23d"): #prev track
		print(f"{command} - prev track")
		sys.stdout.flush()
		os.kill(procHandle.pid, signal.SIGTERM)
		if tracknum > 0:
			tracknum -= 1
		else:
			if albumnum > len(albumList) - 1:
				albumnum -= 1
			else:
				albumnum = 0
			tracknum = 0

		kickOff(albumList[albumnum][tracknum])
		print(albumList[albumnum][tracknum])
	
	elif (command == "0x300ff02fd"): #Prev album
		print(f"{command} - Prev album")
		sys.stdout.flush()
		os.kill(procHandle.pid, signal.SIGTERM)

		if albumnum > 0:
			albumnum -= 1
		else:
			albumnum = len(albumList) - 1
		tracknum = 0
		print(f"album[{albumnum}] track[{tracknum}]")

		kickOff(albumList[albumnum][tracknum])
		print(albumList[albumnum][tracknum])
	
	elif (command == "0x3e0e0e01f" or command == "0x300ffa25d"): #volume up 
		print(f"{command}-Volume up")
		if volumepercent <= 95:
			volumepercent += 5
			os.system(f"amixer sset HDMI {volumepercent}%")
			print(f"volume set to {volumepercent} %")
		else:
			print("volume all the way up")

	
	elif (command == "0x3e0e0d02f" or command == "0x300ff22dd"): #volume down
		print(f"{command}-Volume down")
		if volumepercent >= 5:
			volumepercent -= 5
			os.system(f"amixer sset HDMI {volumepercent}%")
			print(f"volume set to {volumepercent} %")
		else:
			print("voluume all the way down")
			
	elif (command == "0x300ff906f"):
		if (songplaying == 1):
			songplaying = 0
			sys.stdout.flush()
			os.kill(procHandle.pid, signal.SIGTERM)
			
		else:
			songplaying = 1
			kickOff(albumList[albumnum][tracknum])
		
	else:
		if (len(command) > 5):
			print(f"{command} not recognized")
			sys.stdout.flush()        
		else:
			continue
			
		#exit
		#how to find the proces wiht play: ps -ef |grep play
