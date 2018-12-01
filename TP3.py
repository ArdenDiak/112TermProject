'''
Name: Arden Diakhate-Palme
Date:11/28/2018

SongRider 15-112 Term Project
Usage:

To play the game, run the following in Terminal:
	python TP2.py <song.wav>

NOTE:
	Autolab does not allow submissions of .wav files
	as they are greater than 10MB, so you'll have to convert
	the .mp3 to .wav files before calling them 

'''

import sys
import math
import random
import time
import pyaudio
import aubio
import numpy as np
from tkinter import *

# sample sizes for each aubio sample and aubio FFT size
winS = 1024 
hopS = 512 

# parse command line arguments
if len(sys.argv) < 1:
	print("Usage: %s <filename> " % sys.argv[0])
	sys.exit(1)

filename = sys.argv[1]

#initialize aubio File, Beat, and Pitch objects
samplerate=0
file = aubio.source(filename, samplerate, hopS)
samplerate = file.samplerate
tolerance = 0.8

pitchO = aubio.pitch("yin", winS, hopS, samplerate)
pitchO.set_unit("freq")
pitchO.set_tolerance(tolerance)

beatO = aubio.tempo("default",winS,hopS,samplerate)

click = 0.7 * np.sin(2. * np.pi * np.arange(hopS) / hopS * samplerate / 3000.)

fmtAudio=[]

songSpeed= 1 #measured in times the default speed 

#This callback function is called whenever pyAudio needs to play the next set of bytes in the song
def callBack(_in_data, _frame_count, _time_info, _status):
	global fmtAudio

	#get aubio pitch and tempo analysis of a single sample of size hopS
	samples, read = file()
	isBeat = beatO(samples)
	pitch = pitchO(samples)[0]
	pitchConf = pitchO.get_confidence()
	beatConf = beatO.get_confidence()

	if pitchConf > 0.5:
		midiPitch=aubio.freqtomidi(pitch)
	else:
		midiPitch=0

	if isBeat and beatConf > 0.1:
		#define beats by negative pitch
		midiPitch=isBeat[0]*-1
	
	fmtAudio+=[midiPitch]
	audiobuf = samples.tobytes()

	#tell pyAudio to continue if the song isn't done, or stop if it is
	if read < hopS:
		return (audiobuf, pyaudio.paComplete)
	return (audiobuf, pyaudio.paContinue)

#initialize pyAudio and establish stream
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paFloat32,
			channels=1,
			frames_per_buffer=hopS,
			rate=samplerate,
			output=True,
			stream_callback=callBack)

stream.stop_stream()

###Graphics Classes and Methods


class Block(object):
	def __init__(self,x,y,width,height,speedUp):
		self.x=x
		self.y=y
		self.height=height
		self.width=width
		self.canSpeedUpSong = speedUp
		if self.canSpeedUpSong:
			self.color='purple'
		else:
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
		self.maxScore=0
		self.width=20
		self.height=30
		self.color='green'
		self.textColor='black'
		self.protected=0
		self.isActive=False

	def moveLeft(self):
		self.x-=self.speed

	def moveRight(self):
		self.x+=self.speed

	def draw(self,canvas):
		canvas.create_rectangle(self.x,self.y,self.x+self.width,self.y+self.height,fill=self.color)
		canvas.create_text(self.x+self.width//2,self.y+self.height//2,text=str(self.score),fill=self.textColor)

	#checks collisions with a block class, of which each other game element is a subclass 
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

	#PLayer can only shoot bullets if the powerUpShoot is still active
	def shoot(self,angle):
		if self.isActive:
			return Bullet(self.x+self.width//2,self.y,angle)


class Bullet(object):
	def __init__(self,x,y,angle):
		self.x=x
		self.y=y
		self.angle=angle
		self.speed=4
		self.size=10
		self.width=self.size
		self.height=self.size

	def move(self):
		self.x+= self.speed*math.cos(self.angle) 
		self.y-= self.speed*math.sin(self.angle)

	def inBounds(self,data):
		if self.x + self.size > data.width or self.x < 0:
			return False
		elif self.y + self.size > data.height or self.y < 0:
			return False
		return True

	#detect collisions between bullets and game objects
	def collided(self,other):
		#assuming other is a block
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

	def draw(self,canvas):
		canvas.create_oval(self.x,self.y,self.x+self.size,self.y+self.size)

class PowerUp(Block):
	def __init__(self,x,y,width,height):
		super().__init__(x,y,width,height,False)
		self.color='yellow'
	
	def draw(self,canvas):
		canvas.create_oval(self.x,self.y,self.x+self.width,self.y+self.height,fill=self.color)

class PowerUpShoot(Block):
	def __init__(self,x,y,width,height):
		super().__init__(x,y,width,height,False)
		self.color='orange'
	
	def draw(self,canvas):
		canvas.create_oval(self.x,self.y,self.x+self.width,self.y+self.height,fill=self.color)


class GameBlock(Block):
	def __init__(self,x,y,width,height):
		super().__init__(x,y,width,height,False)
		self.color='green'

	def draw(self,canvas):
		canvas.create_polygon(self.x,self.y,self.x-self.width,self.y+self.height,self.x+self.width,self.y+self.height,fill=self.color)

###TKinter Functions

def init(data):
	#variables for timing addBlocks()
	data.timerCalled=0
	data.lastBeat=0
	data.currBeat=0

	data.scrollSpeed=2 #defalut scrollspeed
	data.blocks=[]
	data.bullets=[]

	data.player1= Player(data.width//2,data.height//2,20)
	data.startShootT= 0

	data.gameStarted=False
	data.gameEnded=False

	data.changedSongSpeed=False

def redrawAll(canvas,data):
	if data.gameStarted:
		canvas.create_line(data.width//6,0,data.width//6,data.height)
		canvas.create_line(data.width - data.width//6,0,data.width - data.width//6,data.height)

		canvas.create_rectangle(data.width//2-30,0,data.width//2+30,30,fill='white')
		canvas.create_text(data.width//2,15,text="Score: "+str(data.player1.maxScore))

		data.player1.draw(canvas)
		for block in data.blocks:
			block.draw(canvas)

		for bullet in data.bullets:
			bullet.draw(canvas)

	#if game not yet begun, display beginning pannel 
	elif not data.gameEnded:
		canvas.create_rectangle(data.width//2-data.width//4,data.height//2-data.height//4,data.width//2+data.width//4,data.height//2+data.height//4,fill='white')
		canvas.create_text(data.width//2,data.height//2,text="Songrider",font="Arial 32")

		#format filename
		fmtFileName = str(filename)
		fmtFileName = fmtFileName[fmtFileName.find('/')+1:fmtFileName.find('.wav')]

		canvas.create_text(data.width//2,data.height//2+data.height//8,text="Song: "+fmtFileName,font="Arial 20")

		canvas.create_rectangle(data.width//2-data.width//4,data.height//2+data.height//6,data.width//2,data.height//2+data.height//4)
		canvas.create_text(data.width//2-data.width//6,data.height//2+data.height//5,text="Start")

	#if the game is over, display the end pannel and show the ultimate score
	elif data.gameEnded:
		canvas.create_rectangle(data.width//2-data.width//4,data.height//2-data.height//4,data.width//2+data.width//4,data.height//2+data.height//4,fill='white')
		canvas.create_text(data.width//2,data.height//2,text="Game Over",font="Arial 32")
		canvas.create_text(data.width//2,data.height//2+data.width//6,text="Score:"+ str(data.player1.maxScore),font="Arial 20")

def mousePressed(event,data):
	if not data.gameStarted and not data.gameEnded:
		#check if clicked on Start button 
		if event.x > data.width//2-data.width//4 and event.x < data.width//2:
			if event.y > data.height//2+data.height//6 and event.y < data.height//2 +data.height//4:
				data.gameStarted =True


	playerX = data.player1.x + data.player1.width//2
	playerY = data.player1.y

	#calculate the angle at which the bullet is fired 
	if event.x-playerX < 0:
		angle = math.pi + math.atan((playerY - event.y) / (event.x - playerX) )
	elif event.x-playerX == 0:
		angle = math.radians(90)
	else:
		angle = math.atan((playerY - event.y) / (event.x - playerX) )

	#check if the player can still shoot bullets 
	if data.player1.shoot(abs(angle)) != None:
		data.bullets += [data.player1.shoot(abs(angle))]

def keyPressed(event,data):
	if event.keysym == 'Right':
		data.player1.moveRight()

	elif event.keysym == 'Left':
		data.player1.moveLeft()

	#quit the game if the user presses 'q'
	elif event.char == 'q':
		data.gameStarted=False
		data.gameEnded = True

#this helper function handles block movement for each
#timerFired call
def manipBlocks(data,dataMin,dataMax):
	#check bullet - block collisons
	z=0
	while z < len(data.bullets):
		i=0
		while i < len(data.blocks):
			bullet = data.bullets[z]
			block = data.blocks[i]
			if bullet.collided(block):
				data.player1.score+=1
				data.blocks.pop(i)
			i+=1	
		z+=1

	#handle player - block collisons
	k=0
	while k < len(data.blocks):
		block=data.blocks[k]
		if data.player1.collided(block):
			if isinstance(block,PowerUp):
				data.blocks.pop(k)
				data.player1.protected+=1
				data.player1.color = 'yellow'
				data.player1.textColor='black'

			elif isinstance(block,PowerUpShoot):
				data.startShootT= data.timerCalled
				data.player1.isActive=True
				data.blocks.pop(k)
				data.player1.color = 'orange'
				data.player1.textColor='black'

			elif isinstance(block,GameBlock):
				#if the player is shielded (by a powerUp)
				#the score and scrollSpeed stay constant
				#game block is removed
				if data.player1.protected > 0:
					data.player1.color= 'green'
					data.player1.textColor='white'
					data.player1.protected-=1
					data.blocks.pop(k)
				else:
					data.player1.color = 'red'
					data.player1.textColor='black'
					data.player1.score=0
					data.scrollSpeed=2
			else:
				#if the player is shielded (by a powerUp)
				#the score and scrollSpeed stay constant
				#game block is removed

				if data.player1.protected > 0:
					data.player1.color = 'green'
					data.player1.textColor='white'
					data.player1.protected-=1
					data.blocks.pop(k)
				else:
					data.player1.score=0

					#handle song acceleration
					if block.canSpeedUpSong:
						data.player1.color = 'purple'
						data.player1.textColor='white'
						data.blocks.pop(k)
						
						global songSpeed
						global stream
						global startSpeedUpT

						data.changedSongSpeed=True
						songSpeed+=0.2
						stream.stop_stream()
						startSpeedUpT = time.clock()

						stream = p.open(format=pyaudio.paFloat32,
										channels=1,
										frames_per_buffer=hopS,
										rate=int(samplerate*songSpeed),
										output=True,
										stream_callback=callBack)
						stream.start_stream()
						
						#make changes to game based on sped-up song
						data.scrollSpeed*=songSpeed*6

					else:
						#if the player didn't hit a music block and didn't have a powerup
						data.player1.color = 'red'
						data.player1.textColor='black'
						data.scrollSpeed=2
		k+=1

	shootingT = 200 #tens of milliseconds
	if data.player1.isActive:
		if data.timerCalled - data.startShootT > shootingT:
			data.player1.isActive= False
		else:
			data.player1.isActive=True

	#add a powerUpShoot object every 5100 milliseconds
	if data.timerCalled % 510 ==0:
		randX= random.randint(dataMin,dataMax)
		randSize= random.randint(10,30)
		data.blocks+=[PowerUpShoot(randX,10,randSize,randSize)]

	#add a powerUp object every 2300 milliseconds
	if data.timerCalled % 230 == 0:
		randX= random.randint(dataMin,dataMax)
		randSize= random.randint(10,30)
		data.blocks+=[PowerUp(randX,10,randSize,randSize)]

	if data.timerCalled % 100 == 0:
		#score increase based on game speed
		data.player1.score+= data.scrollSpeed//3
		if data.player1.score > data.player1.maxScore:   #update maxScore 
			data.player1.maxScore=data.player1.score

		randX= random.randint(dataMin,dataMax)
		randSize= random.randint(10,30)
		data.blocks+=[GameBlock(randX,10,randSize,randSize)]
	
	#update bullets
	for bullet in data.bullets:
		bullet.move()
	z=0
	while z < len(data.bullets):
		if not data.bullets[z].inBounds(data):
			data.bullets.pop(z)
		z+=1

	#remove blocks that go off the screen
	j=0
	while j < len(data.blocks):
		if not data.blocks[j].inBounds(data):
			data.blocks.pop(j)
		j+=1

	#move blocks down the screen
	for block in data.blocks:
		block.y+=data.scrollSpeed

def addBlock(data,val):
	size = int(data.currBeat*20)
	#add a speed-up-song block every 10 blocks added
	if len(data.blocks) % 5 == 0 and len(data.blocks) != 0:
		data.blocks+=[Block(val,10,20,size,True)]
	else:
		data.blocks+=[Block(val,10,20,size,False)]

def timerFired(data):
	#handle song acceleration
	global startSpeedUpT
	global songSpeed
	global stream

	speedTime=1.5 #seconds for how long the song should be sped up for
	if(time.clock()-startSpeedUpT) > speedTime and data.changedSongSpeed:
		#reset speedUp time and reset speed-changed Flag
		startSpeedUpT=time.clock()
		data.changedSongSpeed=False
		songSpeed=1
		stream.stop_stream()
		stream = p.open(format=pyaudio.paFloat32,
				channels=1,
				frames_per_buffer=hopS,
				rate=samplerate,
				output=True,
				stream_callback=callBack)
		stream.start_stream()

	if data.gameStarted and not data.gameEnded:
		if not stream.is_active():
			stream.start_stream()
		data.timerCalled+=1

		#set bounds for pitches rescaling to data
		dataMax=data.width - data.width//4
		dataMin=data.width//4

		manipBlocks(data,dataMin,dataMax)

		global fmtAudio
		if len(fmtAudio) > 0:
			lastSample = fmtAudio[-1]
		else:
			lastSample = -0.5

		#only calculate pitchRange if there are over 200 beat/pitch samples
		if len(fmtAudio) > 200:
			pitchRange=np.ptp(abs(np.array(fmtAudio[-100:])))
		else:
			pitchRange=200


		if lastSample < 0:
			data.currBeat=abs(lastSample)
			val = dataMin
		elif lastSample > 0:
			avgPitch= np.average(np.array(fmtAudio[-10:]))
			val = ((avgPitch / pitchRange)*(dataMax-dataMin)) + dataMin
		else:
			val=dataMin

		global startT
		if data.currBeat == data.lastBeat and data.currBeat != 0:
			#only add a block on intervals of the song tempo (calculated in data.currBeat)
			if time.time()-startT > data.currBeat:
				addBlock(data,val)
				newSpeed=abs(10-int(data.currBeat*20)//3 + 2)
				data.scrollSpeed=newSpeed
				startT=time.time()

		data.lastBeat= data.currBeat

	elif data.gameEnded:
		stream.stop_stream()


def run(width=500, height=600):
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
		timerFired(data)
		redrawAllWrapper(canvas,data)
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

#time inits for timers
startT=time.time()
startSpeedUpT=time.clock()

run()

#close pyAudio Stream instance and terminate object
stream.stop_stream()
stream.close()
p.terminate()