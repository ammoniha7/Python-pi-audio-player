#!/usr/bin/python3
import time
import sys
import os
import signal
import subprocess
import RPi.GPIO as GPIO
import datetime
from datetime import datetime
from os import walk



IRsignalpin = 11
global procHandle
global fileNum
global maxFileNum
global fileList
fileNum = 0

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
	previousValue = 0 #The previous pin state
	value = GPIO.input(IRsignalpin) #Current pin state
	
	while value: #Waits until pin is pulled low
		value = GPIO.input(IRsignalpin)
	
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
	
	
fileList = os.listdir(r"/media/pi/MOMSMUSIC/momsmusic/workout/Cardio60")
print(fileList)
#time.sleep(20)

maxFileIndex = len(fileList) -1
print("hi")
print("maxFileIndex[")
print(maxFileIndex)
print("]")
#pro = subprocess.Popen("play " + fileList, stdout=subprocess.PIPE, shell=True, preexec_fn =os.setsid)


def kickOff(fileName):
    global procHandle
    procHandle = subprocess.Popen(["play", '-q', fileName])
    
    
kickOff("/media/pi/MOMSMUSIC/momsmusic/workout/Cardio60/" + fileList[fileNum])

    
while True:
    sys.stdout.flush()
    command = ConvertHex(getData())
    print(command)
    sys.stdout.flush()

    if (command == "0x3e0e016e9L"):
        print("command matched")
        sys.stdout.flush()
        os.kill(procHandle.pid, signal.SIGTERM)
        if fileNum < maxFileIndex:
            fileNum += 1
	    kickOff(fileList[fileNum])
        else:
            fileNum = 0 # start over
        kickOff(fileList[fileNum])
        
    else:
        print("command not recognized, doing nothing")
        sys.stdout.flush()        
        #exit





