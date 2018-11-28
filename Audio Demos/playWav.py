"""PyAudio Example: Play a wave file."""
from tkinter import *
import time
import pyaudio
import aubio
import wave
import sys

CHUNK = 1024

if len(sys.argv) < 2:
	print("Plays a wave file.\n\nUsage: %s filename.wav" % sys.argv[0])
	sys.exit(-1)

wf = wave.open(sys.argv[1], 'rb')

speed= 1
startSpeedUpT=time.clock()
returnToNormalSpeed = False

# instantiate PyAudio (1)
p = pyaudio.PyAudio()
file = aubio.source(sys.argv[1], 0, 512)


def callBack(_in_data, _frame_count, _time_info, _status):
	samples,read=file()

	audiobuf = samples.tobytes()
	if read < 512:
		return (audiobuf, pyaudio.paComplete)
	return (audiobuf, pyaudio.paContinue)

stream = p.open(format=pyaudio.paFloat32,
				channels=1,
				frames_per_buffer=512,
				rate=wf.getframerate(),
				output=True,
				stream_callback=callBack)

stream.start_stream()

def init(data):
	data.changedSpeed=False

def timerFired(data):
	global startSpeedUpT
	global speed
	global stream

	speedTime=3 #seconds
	if(time.clock()-startSpeedUpT) > speedTime and data.changedSpeed:
		stream.stop_stream()
		startSpeedUpT=time.clock()
		data.changedSpeed=False
		speed=1
		print(time.clock()-startSpeedUpT > speedTime)
		stream = p.open(format=pyaudio.paFloat32,
				channels=1,
				frames_per_buffer=512,
				rate=wf.getframerate(),
				output=True,
				stream_callback=callBack)
		stream.start_stream()


def mousePressed(event,data):
	pass

def keyPressed(event,data):
	global speed
	global stream
	global startSpeedUpT

	if event.keysym=='Up':
		data.changedSpeed=True
		speed+=0.1
		stream.stop_stream()
		startSpeedUpT = time.clock()
		stream = p.open(format=pyaudio.paFloat32,
						channels=1,
						frames_per_buffer=512,
						rate=int(wf.getframerate()*speed),
						output=True,
						stream_callback=callBack)
		stream.start_stream()


	elif event.keysym=='Down':
		data.changedSpeed=True
		speed-=0.1
		stream.stop_stream()
		startSpeedUpT = time.clock()
		stream = p.open(format=pyaudio.paFloat32,
						channels=1,
						frames_per_buffer=512,
						rate=int(wf.getframerate()*speed),
						output=True,
						stream_callback=callBack)
		stream.start_stream()

def redrawAll(canvas,data):
	canvas.create_rectangle(data.width//2,data.height//2,data.width//2+(data.width//4),data.height//2+(data.height//4))


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
	
print(returnToNormalSpeed)

run()


# stop stream (4)
stream.stop_stream()
stream.close()

# close PyAudio (5)
p.terminate()