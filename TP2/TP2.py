'''
Name: Arden Diakhate-Palme
Date:11/23/2018

SongRider 15-112 Term Project
Usage:

To play the game, run the following in Terminal:
	python TP2.py Files/<song.wav>

NOTE:
	Autolab does not allow submissions of .wav files
	as they are greater than 10MB, so you'll have to convert
	the .mp3 files in Files/ to .wav files before calling them
'''

import math
import time
import pyaudio
import aubio
import random
import wave
import numpy as np
import threading
from threading import Thread
from tkinter import *


###Audio Parsing

# parse command line arguments
if len(sys.argv) < 2:
	print("Usage: %s <filename> " % sys.argv[0])
	sys.exit(1)

filename = sys.argv[1]

wf = wave.open(filename)
duration = wf.getnframes() / float(wf.getframerate())  

#adapted from PyAudio Documentation 
#https://people.csail.mit.edu/hubert/pyaudio/docs/
def playSong():
	p = pyaudio.PyAudio()
	stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
				channels=wf.getnchannels(),
				rate=wf.getframerate(),
				output=True)

	CHUNK=1024
	data = wf.readframes(CHUNK)

	while len(data) > 0:
		stream.write(data)
		data = wf.readframes(CHUNK)
	
	#Stop Streams 
	stream.stop_stream()
	stream.close()
	p.terminate()

def parseAudio():
	winS = 1024 
	hopS = 512 

	samplerate=0
	file = aubio.source(filename, samplerate, hopS)
	samplerate = file.samplerate
	tolerance = 0.8

	pitchO = aubio.pitch("yin", winS, hopS, samplerate)
	pitchO.set_unit("freq")
	pitchO.set_tolerance(tolerance)

	beatO = aubio.tempo("default",winS,hopS,samplerate)
	minBeatConf=0.15		#minimum beat confidence to detect beat

	fmtAudio=[]
	while True:
		samples, read = file()
		isBeat = beatO(samples)
		pitch = pitchO(samples)[0]
		pitchConf = pitchO.get_confidence()
		beatConf = beatO.get_confidence()

		if pitchConf > 0.5:
			midiPitch=aubio.freqtomidi(pitch)
		else:
			midiPitch=0

		if isBeat and beatConf > minBeatConf:
			#define beats by negative pitch
			midiPitch= isBeat[0]*-1

		fmtAudio+=[midiPitch]

		if read < file.hop_size:
			break

	return fmtAudio

###Graphics Classes and Methods

class Block(object):
	def __init__(self,x,y,width,height):
		self.x=x
		self.y=y
		self.height=height
		self.width=width
		self.color='red'

	def draw(self,canvas):
		canvas.create_rectangle(self.x,self.y,self.x+self.width,self.y+self.height,fill=self.color)

	def inBounds(self,data):
		if self.x + self.width > data.width:
			return False
		elif self.y + self.height > data.height:
			return False
		return True


class Player(object):

	def __init__(self,x,y,speed):
		self.x=x
		self.y=y
		self.speed=speed
		self.score=0
		self.width=20
		self.height=30
		self.color='green'

	def moveLeft(self):
		self.x-=self.speed

	def moveRight(self):
		self.x+=self.speed

	def draw(self,canvas):
		canvas.create_rectangle(self.x,self.y,self.x+self.width,self.y+self.height,fill=self.color)
		canvas.create_text(self.x+self.width//2,self.y+self.height//2,text=str(self.score))

	def collided(self,other):
		if other.x > self.x:
			if other.x < self.x + self.width:
				if other.y > self.y and other.y < self.y+self.height:
					return True
				elif other.y+other.height > self.y and other.y+other.height < self.y + self.height:
					return True
		elif other.x+other.width > self.x:
			if other.x + other.width < self.x + self.width:
				if other.y > self.y and other.y < self.y+self.height:
					return True
				elif other.y+other.height > self.y and other.y+other.height < self.y + self.height:
					return True
		return False

class PowerUp(Block):
	def __init__(self,x,y,width,height):
		super().__init__(x,y,width,height)
		self.color='yellow'
	
	def draw(self,canvas):
		canvas.create_oval(self.x,self.y,self.x+self.width,self.y+self.height,fill=self.color)

class GameBlock(Block):
	def __init__(self,x,y,width,height):
		super().__init__(x,y,width,height)
		self.color='green'

	def draw(self,canvas):
		canvas.create_polygon(self.x,self.y,self.x-self.width,self.y+self.height,self.x+self.width,self.y+self.height,fill=self.color)

###TKinter Functions

def init(data):
	data.timerCalled=0
	data.lastBeat=0
	data.currBeat=0

	data.scrollSpeed=2
	data.blocks=[]

	data.player1= Player(data.width//2,data.height//2,20)
	data.startTime=time.clock()

def redrawAll(canvas,data):
	canvas.create_line(data.width//6,0,data.width//6,data.height)
	canvas.create_line(data.width - data.width//6,0,data.width - data.width//6,data.height)

	data.player1.draw(canvas)
	for block in data.blocks:
		block.draw(canvas)

def mousePressed(event,data):
	pass

def keyPressed(event,data):
	if event.keysym == 'Right':
		data.player1.moveRight()

	elif event.keysym == 'Left':
		data.player1.moveLeft()

def timerFired(data,fmtAudio):
	data.timerCalled+=1

	RATE=10

	dataMax=data.width - data.width//4
	dataMin=data.width//4

	for block in data.blocks:
		if data.player1.collided(block):
			if isinstance(block,PowerUp):
				data.player1.score+=5
				data.player1.color='green'
			elif isinstance(block,GameBlock):
				data.player1.score=0
				data.scrollSpeed=2
				data.player1.color='red'
			else:
				data.player1.score=0
				data.scrollSpeed=2
				data.player1.color='red'
				
	if data.timerCalled % 230 == 0:
		randX= random.randint(dataMin,dataMax)
		randSize= random.randint(10,30)
		data.blocks+=[PowerUp(randX,10,randSize,randSize)]

	if data.timerCalled % 100 == 0:
		data.player1.score+=1

		randX= random.randint(dataMin,dataMax)
		randY= random.randint(10,data.height-10)
		randSize= random.randint(10,30)
		data.blocks+=[GameBlock(randX,randY,randSize,randSize)]
	
	j=0
	while j < len(data.blocks):
		if not data.blocks[j].inBounds(data):
			data.blocks.pop(j)
		j+=1

	pitchRange=np.ptp(abs(np.array(fmtAudio)))
	
	sample = fmtAudio[RATE*data.timerCalled:RATE*data.timerCalled+RATE]
	setSample=set(sample)

	i=0
	while i < len(sample):
		if sample[i] < 0:
			if len(setSample) <= 4:
				data.currBeat=abs(sample[i])
			sample=sample[:i] + sample[i+1:]
		i+=1

	avgPitch=np.average(np.array(sample))
	if avgPitch != 0:
		val = ((avgPitch / pitchRange)*(dataMax-dataMin)) + dataMin
	else:
		val=0

	if data.currBeat != data.lastBeat and data.currBeat != 0:
		data.lastBeat=data.currBeat

	startT=time.clock()
	speedDiff=0

	if (time.clock()-startT) > data.currBeat and np.isfinite(val) and val!=0:
		print('------------>',val)
		data.blocks+=[Block(int(val),10,30,30)]
		startT=time.clock()
	else:

		for block in data.blocks:
			block.y+=data.scrollSpeed


###15-112 Run Function
def run(fmtAudio,width=500, height=600):
	def redrawAllWrapper(canvas, data):
		canvas.delete(ALL)
		canvas.create_rectangle(0, 0, data.width, data.height,
								fill='white', width=0)
		redrawAll(canvas, data)
		canvas.update()

	def mousePressedWrapper(event, canvas, data):
		mousePressed(event, data)
		redrawAllWrapper(canvas, data)

	def keyPressedWrapper(event, canvas, data):
		keyPressed(event, data)
		redrawAllWrapper(canvas, data)

	def timerFiredWrapper(canvas, data):
		timerFired(data,fmtAudio)
		redrawAllWrapper(canvas, data)
		# pause, then call timerFired again
		canvas.after(data.timerDelay, timerFiredWrapper, canvas, data)
	# Set up data and call init
	class Struct(object): pass
	data = Struct()
	data.width = width
	data.height = height
	data.timerDelay = 10 # milliseconds
	root = Tk()
	root.resizable(width=False, height=False) # prevents resizing window
	init(data)
	# create the root and the canvas
	canvas = Canvas(root, width=data.width, height=data.height)
	canvas.configure(bd=0, highlightthickness=0)
	canvas.pack()
	# set up events
	root.bind("<Button-1>", lambda event:
							mousePressedWrapper(event, canvas, data))
	root.bind("<Key>", lambda event:
							keyPressedWrapper(event, canvas, data))
	timerFiredWrapper(canvas, data)
	# and launch the app
	root.mainloop()  # blocks until window is closed
	print("bye!")


### Main Thread
if __name__ == '__main__':
	fmtAudio = parseAudio()
	startT=time.clock()

	Thread(target = playSong).start()
	Thread(target =run(fmtAudio)).start()