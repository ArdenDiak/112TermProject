'''
Name: Arden Diakhate-Palme
Date:12/5/2018

SongRider 15-112 Term Project

Usage:

To play the game, run the following in Terminal:
	python TP3.py <song.wav>

NOTE:
	Autolab does not allow submissions of .wav files
	as they are greater than 10MB, so you'll have to convert
	the .mp3 to .wav files before calling them 

'''

import sys
import math
import random
import copy
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

#fmtAudio stores audio data computed in real-time
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
	def __init__(self,x,y,z,width,depth,offset,speedUp):
		self.x=x
		self.y=y
		self.z=z

		self.width=width
		self.depth=depth
		self.offset=offset

		self.canSpeedUpSong = speedUp
		if self.canSpeedUpSong:
			self.colorVal=2
		else:
			self.colorVal=1

	def draw(self,data,canvas):
		pos=[self.x,self.y,self.z]
		display(canvas,data,pos,self.width,self.depth,self.offset,None,self.colorVal)

	def inBounds(self,data):
		#check if went past player / off the screen
		if self.z <= 0:
			return False
		return True

class Bullet(object):
	def __init__(self,x,y,z,speed,offset):
		self.x=x
		self.y=y
		self.z=z
		self.rad = 3
		self.speed=speed
		self.offset=offset

	def draw(self,canvas,data):
		pos=[self.x,self.y,self.z]
		displayBullet(canvas,data,pos,self.rad,0,'blue')

	def move(self):
		self.z+=self.speed

	def collided(self,other,data):
		if isinstance(other,Block):
		
			a=[self.x,self.y,self.z]
			b=[other.x,other.y,other.z]

			#set z-coordinate to 1 if below 0, to allow for calculations
			if b[2] <=0 or math.isclose(b[2],0.0):
				b[2]=1

			dXB = (data.vanishPt[0])*(b[2]**-1) + other.width

			b[0]+= data.vanishPt[0]+(other.offset*10*b[2]**-1)

			if b[2] < a[2]:
				if(a[0] > b[0]+dXB):
					return False

				if(a[0] < b[0]-dXB):
					return False
				return True

	def inBounds(self,data):
		if self.z > data.vanishPt[2]:
			return False
		return True

class Player(object):

	def __init__(self,x,y,z,speed):
		self.x=x
		self.y=y
		self.z=z
		self.speed=speed
		self.score=0
		self.maxScore=0
		self.width=2
		self.height=5
		self.depth=1

		self.colorVal=0      #indexes the color scheme values
		self.protected=0
		self.isActive=False  #checks if the player can shoot

	def moveLeft(self):
		if self.x > -220:
			self.x-=self.speed

	def moveRight(self):
		if self.x < 250:
			self.x+=self.speed

	def draw(self,data,canvas):
		pos=[self.x,self.y,self.z]
		if self.isActive:
			display(canvas,data,pos,self.width,self.depth,0,self.score,3)
		else:
			display(canvas,data,pos,self.width,self.depth,0,self.score,self.colorVal)

	#gets bullet objects to shoot from player
	def shoot(self,data):
		a=[self.x,self.y,self.z]
		if a[2] <= 0:
			a[2] = 1
		screenY = ((data.height*2)/a[2]) + (data.vanishPt[1])
		dX = (data.vanishPt[0])*(a[2]**-1) + self.width
		dY = (data.vanishPt[1])*(a[2]**-1) + a[1]
		a[0]+=data.vanishPt[0]
		
		if self.isActive:
			return Bullet(a[0]+dX//2,screenY+dY//2,a[2],2,data.width//2)

	#checks collisions with a block class, of which each other game element is a subclass 
	def collided(self,other,data):
		a=[self.x,self.y,self.z]
		b=[other.x,other.y,other.z]

		if a[2] <=0:
			a[2]=1

		if b[2] <0 or math.isclose(b[2],0.0):
			b[2]=1

		#calculate 3D graphics changes in position
		dX = (data.vanishPt[0])*(self.z**-1) + self.width
		dXB = (data.vanishPt[0])*(b[2]**-1) + other.width

		a[0]+= data.vanishPt[0]
		b[0]+= data.vanishPt[0]+(other.offset*10*b[2]**-1)

		if b[2] < a[2]:
			if(a[0]-dX > b[0]+dXB):
				return False

			if(a[0]+dX < b[0]-dXB):
				return False
			return True

class PowerUp(Block):
	def __init__(self,z,rad,offset):
		super().__init__(0,0,z,rad,rad,offset,False)
		self.color='yellow'
	
	def draw(self,data,canvas):
		pos=[self.x,self.y,self.z]
		displaySphere(canvas,data,pos,self.width,self.offset,self.color)

class PowerUpShoot(Block):
	def __init__(self,z,rad,offset):
		super().__init__(0,0,z,rad,rad,offset,False)
		self.color='orange'
	
	def draw(self,data,canvas):
		pos=[self.x,self.y,self.z]
		displaySphere(canvas,data,pos,self.width,self.offset,self.color)

def init(data):
	#variables for timing addBlocks()
	data.timerCalled=0
	data.lastBeat=0
	data.currBeat=0

	data.scrollSpeed=2 #defalut scrollspeed
	data.blocks=[]
	data.bullets=[]
	data.roadColor=''

	data.player1= Player(0,20,5,30)
	data.startShootT= 0

	data.gameStarted=False
	data.gameEnded=False

	data.changedSongSpeed=False

	#3D
	data.vanishPt = [data.width//2,data.height//3,200]
	data.roadGap = 10
	data.worldZ=data.vanishPt[2]
	data.raceCarImg= PhotoImage(file="formula1.gif")
	data.raceCarBumper= PhotoImage(file="bumper.gif")
	data.skyImage=PhotoImage(file="sky.gif")
	data.rise=20 #calculates the road rise

#display function for 3D pseudo-graphic rendering of blocks
def display(canvas,data,a,width,depth,offset,score,colorVal):
	#colors for blocks and surfaces
	colorScheme = {
	0:['blue','orange','green','red'],
	1:['yellow','purple','brown','white'],
	2:['pink','blue','orange','green'],
	3:['medium spring green','forest green','green yellow','dark sea green']
	}

	aP = copy.copy(a)
	if a[2] <= 0:
		a[2] = 1

	if depth > 0:
		aP[2] = a[2] + depth
	else:
		aP[2] = a[2] + 1

	aP[1] = (a[2]/aP[2]) * a[1]
	aP[0]= (a[2]/aP[2]) * a[0]

	screenY = ((data.height*2)/a[2]) + (data.vanishPt[1])
	screenYP = ((data.height*2)/aP[2]) + (data.vanishPt[1])

	#calculates changes in X and Y as the object moves in z space
	dX = (data.vanishPt[0])*(a[2]**-1) + width
	dXP= (data.vanishPt[0])*(aP[2]**-1) + width

	dY = (data.vanishPt[1])*(a[2]**-1) + a[1]
	dYP = (data.vanishPt[1])*(aP[2]**-1) + aP[1]

	a[0]+= data.vanishPt[0]+(offset*10*a[2]**-1)
	aP[0]+= data.vanishPt[0]+(offset*10*aP[2]**-1)

	#create cube faces
	canvas.create_polygon(aP[0]+dXP,screenYP-dYP,a[0]+dX,screenY-dY,a[0]+dX,screenY+dY,aP[0]+dXP,screenYP+dYP,fill=colorScheme[colorVal][0])
	canvas.create_polygon(aP[0]-dXP,screenYP+dYP,aP[0]-dXP,screenYP-dYP,a[0]-dX,screenY-dY,a[0]-dX,screenY+dY,fill=colorScheme[colorVal][1])
	canvas.create_polygon(aP[0]+dXP,screenYP-dYP,a[0]+dX,screenY-dY,a[0]-dX,screenY-dY,aP[0]-dXP,screenYP-dYP,fill=colorScheme[colorVal][2])
	canvas.create_rectangle(a[0]-dX,screenY-dY,a[0]+dX,screenY+dY,fill=colorScheme[colorVal][3])
	
	#displays score
	if score != None:
		canvas.create_rectangle(a[0]-dX,screenY-dY,a[0]+dX,screenY+dY,fill='white')
		canvas.create_image(a[0],screenY,anchor=CENTER,image=data.raceCarBumper)
		canvas.create_text(a[0],screenY-20,text=str(score),font='Arial 32')
	else:
		canvas.create_rectangle(a[0]-dX,screenY-dY,a[0]+dX,screenY+dY,fill=colorScheme[colorVal][3])

#3D rendering of Powerups
def displaySphere(canvas,data,a,rad,offset,color):
	if a[2] <= 0:
		a[2] = 1
	screenY = ((data.height*2)/a[2]) + (data.vanishPt[1])
	dR = (data.vanishPt[0])*(a[2]**-1) 
	a[0] += data.vanishPt[0]+(offset*10*a[2]**-1)

	canvas.create_oval(a[0]-dR,screenY+dR,a[0]+dR,screenY-dR,fill=color)

#3D rendering of Bullets
def displayBullet(canvas,data,a,rad,offset,color):
	if a[2] <= 0:
		a[2] = 1
	screenY = ((data.height*2)/a[2]) + (data.vanishPt[1])
	dR = (data.vanishPt[0])*(a[2]**-1) 
	posX= (data.vanishPt[0]-a[0])*(a[2]/200) + a[0]
	canvas.create_oval(posX-dR,screenY-dR,posX+dR,screenY+dR,fill='yellow')

def redrawAll(canvas,data):
	if data.gameStarted:
		#sky
		canvas.create_polygon(0,0,data.width,0,data.width,data.vanishPt[1],0,data.vanishPt[1],fill='SkyBlue1')

		#draws the scoreBoard
		canvas.create_rectangle(data.width//2-80,0,data.width//2+80,40,fill='white')
		canvas.create_text(data.width//2-45,15,text="Score: "+str(data.player1.maxScore))
		canvas.create_text(data.width//2+35,15,text="Protected: "+str(data.player1.protected))
		if data.player1.isActive:
			canvas.create_rectangle(data.width//2-40,40,data.width//2+40,100,fill='white')
			canvas.create_text(data.width//2,70,text="FIRE!",fill='red',font='Arial 20')


		#draw a 3d road
		canvas.create_polygon(data.vanishPt[0]-data.roadGap,data.vanishPt[1],0,data.height-data.rise,data.width,data.height-data.rise,
			data.vanishPt[0]+data.roadGap,data.vanishPt[1],fill=data.roadColor)
		canvas.create_polygon(0,data.height-data.rise,data.width,data.height-data.rise,data.width,data.height,0,data.height, fill=data.roadColor)
		canvas.create_line(0,data.vanishPt[1],data.width,data.vanishPt[1])

		data.player1.draw(data,canvas)

		for block in data.blocks:
			block.draw(data,canvas)

		for bullet in data.bullets:
			bullet.draw(canvas,data)
	
	#if game not yet begun, display beginning pannel 
	elif not data.gameEnded:
		canvas.create_image(0,data.height//2-250, anchor=NW,image=data.raceCarImg)
		#canvas.create_rectangle(data.width//2-data.width//4,data.height//2-data.height//4,data.width//2+data.width//4,data.height//2+data.height//4,fill='white')
		canvas.create_text(data.width//2,data.height//2,text="Songrider",font="Arial 40",fill='white')

		#format filename
		fmtFileName = str(filename)
		fmtFileName = fmtFileName[fmtFileName.find('/')+1:fmtFileName.find('.wav')]

		#explain game rules
		canvas.create_rectangle(0,332,data.width,510)
		canvas.create_text(data.width//2,data.height//2+data.height//8,text="Song: "+fmtFileName,font="Arial 20")
		canvas.create_text(data.width//2,data.height//2+160,\
			text="* Avoid and destroy the blocks to increase your score\n"+\
			"* Yellow powerups protect you from blocks\n* Orange powerups let you fire\n" +\
			"* Press \'space\' to fire to destroy blocks" ,font='Arial 20')
		
		canvas.create_rectangle(data.width//2-data.width//4,data.height-data.height//7,data.width//2+data.width//4,data.height-5)
		canvas.create_text(data.width//2,557,text="Start",font='Arial 40')

	#if the game is over, display the end pannel and show the ultimate score
	elif data.gameEnded:
		canvas.create_rectangle(data.width//2-data.width//4,data.height//2-data.height//4,data.width//2+data.width//4,data.height//2+data.height//4,fill='white')
		canvas.create_text(data.width//2,data.height//2,text="Game Over",font="Arial 32")
		canvas.create_text(data.width//2,data.height//2+data.width//6,text="Score:"+ str(data.player1.maxScore),font="Arial 20")

def manipBlocks(data,dataMin,dataMax):
	#add a powerUp object every 2300 milliseconds
	if data.timerCalled % 230 == 0:
		randOffset= random.randint(dataMin,dataMax)
		randSize= random.randint(10,20)
		data.blocks+=[PowerUp(data.worldZ,randSize,randOffset)]

	#add a powerUpShoot object every 2 seconds
	if data.timerCalled % 200 == 0:
		randOffset= random.randint(dataMin,dataMax)
		randSize= random.randint(10,20)
		data.blocks+=[PowerUpShoot(data.worldZ,randSize,randOffset)]

	if data.timerCalled % 100 == 0:
		#score increase based on game speed
		data.player1.score+= data.scrollSpeed
		if data.player1.score > data.player1.maxScore:   #update maxScore 
			data.player1.maxScore=data.player1.score
	
	#handle bullet-block collisions
	z=0
	while z < len(data.bullets):
		w=0
		while w < len(data.blocks):
			bullet = data.bullets[z]
			block = data.blocks[w]
			if bullet.collided(block,data):
				data.player1.score+=1
				data.blocks.pop(w)
			w+=1	
		z+=1

	#delete blocks that move off the screen
	i=0
	while i < len(data.blocks):
		block = data.blocks[i]
		if not block.inBounds(data):
			data.blocks.pop(i)
		i+=1

	#delete blocks that move out of the world
	j=0
	while j < len(data.bullets):
		bullet = data.bullets[j]
		if not bullet.inBounds(data):
			data.bullets.pop(j)
		j+=1
	
	#handle player-block collisions
	k=0
	while k < len(data.blocks):
		block=data.blocks[k]
		if data.player1.collided(block,data):

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
						#print(block.offset)
						data.player1.colorVal=2
						data.blocks.pop(k)	
		k+=1

	#limits the time the player can shoot for
	shootingT = 80 #tens of milliseconds
	if data.player1.isActive:
		if data.timerCalled - data.startShootT > shootingT:
			data.player1.isActive= False
		else:
			data.player1.isActive=True

	for block in data.blocks:
		block.z-=data.scrollSpeed//3

	for bullet in data.bullets:
		bullet.move()

#adds a block to the game
def addBlock(data,val):
	size = int(data.currBeat*20)
	#add a speed-up-song block every 3 sec
	if data.timerCalled%300==0 and len(data.blocks) != 0:
		data.blocks+=[Block(0,size,data.worldZ,10,size,val,True)]
	else:
		data.blocks+=[Block(0,size,data.worldZ,10,size,val,False)]

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
		dataMax=50
		dataMin=-50

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

		#calculate discrete pitch
		if lastSample < 0:
			data.currBeat=abs(lastSample)
			avgPitch = 0
		elif lastSample > 0:
			avgPitch= np.average(np.array(fmtAudio[-10:]))
			
			#update road color every .1 seconds
			color= int((avgPitch / pitchRange)*(255))
			if data.timerCalled % 2 == 0:
				data.roadColor = '#%02x%02x%02x' % ((color,0,0))
		else:
			avgPitch=0

		global startT
		if data.currBeat == data.lastBeat and data.currBeat != 0:
			#only add a block on intervals of the song tempo (calculated in data.currBeat)
			if time.time()-startT > data.currBeat:
				data.rise = int(data.currBeat*200)
				if 30-data.rise > -50:
					dataMin,dataMax=-100,100
				else:
					dataMin,dataMax=30-data.rise,data.rise+30
				val = ((avgPitch / pitchRange)*(dataMax-dataMin)) + dataMin
				addBlock(data,val)
				#update scrollSpeed depending on pitch
				newSpeed=abs(10-int(data.currBeat*20)//3 + 2)
				data.scrollSpeed=newSpeed
				startT=time.time()

		data.lastBeat= data.currBeat

	elif data.gameEnded:
		stream.stop_stream()

def mousePressed(event,data):
	if not data.gameStarted and not data.gameEnded:
		#check if clicked on Start button 
		if event.x > data.width//2-data.width//4 and event.x < data.width//2+data.width//4:
			if event.y > data.height-data.height//7 and event.y < data.height-5:
				data.gameStarted =True

def keyPressed(event,data):
	if event.keysym == 'Right':
		data.player1.moveRight()

	elif event.keysym == 'Left':
		data.player1.moveLeft()

	elif event.keysym == 'space':
		if data.player1.shoot(data) != None:
			data.bullets+=[data.player1.shoot(data)]

		#quit the game if the user presses 'q'
	if event.char == 'q':
		data.gameStarted=False
		data.gameEnded = True
		
	
#The run() function taken from the CMU's 15-112 Course website
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

