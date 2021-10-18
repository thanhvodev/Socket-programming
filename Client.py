from tkinter import *
import tkinter.messagebox
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os
import time

from RtpPacket import RtpPacket
#DESKTOP-GNVB183
CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"

class Client:
	INIT = 0
	READY = 1
	PLAYING = 2
	state = INIT
	
	SETUP = 0
	PLAY = 1
	PAUSE = 2
	TEARDOWN = 3

	def __init__(self, master, serveraddr, serverport, rtpport, filename):
		self.master = master
		self.createWidgets()
		self.serverAddr = serveraddr
		self.serverPort = int(serverport)
		self.rtpPort = int(rtpport)
		self.fileName = filename
		self.rtspSeq = 0
		self.sessionId = 0
		self.requestSent = -1
		self.teardownAcked = 0
		self.connectToServer()
		self.frameNbr = 0
		self.delay_time = 0
		
	# Initiatio
	# THIS GUI IS JUST FOR REFERENCE ONLY, STUDENTS HAVE TO CREATE THEIR OWN GUI 	
	def createWidgets(self):
		"""Build GUI."""
		# Create Setup button
		self.setup = Button(self.master, width=20, padx=3, pady=3)
		self.setup["text"] = "Setup"
		self.setup["command"] = self.setupMovie
		self.setup.grid(row=1, column=0, padx=2, pady=2)
		
		# Create Play button		
		self.start = Button(self.master, width=20, padx=3, pady=3)
		self.start["text"] = "Play"
		self.start["command"] = self.playMovie
		self.start.grid(row=1, column=1, padx=2, pady=2)
		
		# Create Pause button			
		self.pause = Button(self.master, width=20, padx=3, pady=3)
		self.pause["text"] = "Pause"
		self.pause["command"] = self.pauseMovie
		self.pause.grid(row=1, column=2, padx=2, pady=2)
		
		# Create Teardown button
		self.teardown = Button(self.master, width=20, padx=3, pady=3)
		self.teardown["text"] = "Teardown"
		self.teardown["command"] =  self.exitClient
		self.teardown.grid(row=1, column=3, padx=2, pady=2)

        # Create Teardown button
		self.slowmotion = Button(self.master, width=20, padx=3, pady=3)
		self.slowmotion["text"] = "Slow motion: OFF"
		self.slowmotion["command"] =  self.slowMotion
		self.slowmotion.grid(row=1, column=4, padx=2, pady=2)

		# Create a label to display the movie
		self.label = Label(self.master, height=19)
		self.label.grid(row=0, column=0, columnspan=4, sticky=W+E+N+S, padx=5, pady=5) 
	
	def setupMovie(self):
		if self.state == self.INIT:
			self.sendRtspRequest(self.SETUP)

	def exitClient(self):
		"""Teardown button handler."""
		self.sendRtspRequest(self.TEARDOWN)			
		self.master.destroy()
		

	def pauseMovie(self):
		if self.state == self.PLAYING:
			self.sendRtspRequest(self.PAUSE)
	
	def playMovie(self):
		"""Play button handler."""
		if self.state == self.READY:
			threading.Thread(target=self.listenRtp).start()
			self.sendRtspRequest(self.PLAY)

	def slowMotion(self):
		if self.delay_time != 0:
			self.delay_time = 0
			self.slowmotion['text'] = "Slow Motion: OFF"
		else:
			self.delay_time = 0.15
			self.slowmotion['text'] = "Slow Motion: ON"	

	def listenRtp(self):		
		"""Listen for RTP packets."""
		while True:
			try:
				print("RECEIVING FRAME...")
				data = self.rtpSocket.recv(20000)
				if data:
					rtpPacket = RtpPacket()
					rtpPacket.decode(data)
					print ("CURRENT FRAME NUMBER: " + str(rtpPacket.seqNum()))
					filename = self.writeFrame(rtpPacket.getPayload())
					self.updateMovie(filename)

			except:
				break
			
			time.sleep(self.delay_time)
			
	def writeFrame(self, data):
		"""Write the received frame to a temp image file. Return the image file."""
		imageFile = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
		file = open(imageFile, "wb")
		file.write(data)
		file.close()
		return imageFile
	
	def updateMovie(self, imageFile):
		"""Update the image file as video frame in the GUI."""
		image = Image.open(imageFile)
		image1 = ImageTk.PhotoImage(image)
		self.label.configure(image = image1, height=288) 
		self.label.image = image1
		
		
	def connectToServer(self):
		"""Connect to the Server. Start a new RTSP/TCP session."""
		self.rtspsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.rtspsocket.connect((self.serverAddr, self.serverPort))

	
	def sendRtspRequest(self, requestCode):
		"""Send RTSP request to the server."""	
		if requestCode == self.SETUP and self.state == self.INIT:
			self.rtspSeq+=1
			threading.Thread(target=self.recvRtspReply).start()
			request = "SETUP movie.Mjpeg RTSP/1.0\n" + f"CSeq: {self.rtspSeq}\n"  + f"Transport: RTP/UDP; client_port= {self.rtpPort}"
			self.requestSent = self.SETUP
		elif not self.INIT and requestCode == self.TEARDOWN:
			self.rtspSeq+=1
			request = "TEARDOWN movie.Mjpeg RTSP/1.0\n" + f"CSeq: {self.rtspSeq}\n"  + f"Session: {self.sessionId}"
			self.requestSent = self.TEARDOWN
		elif self.state == self.READY and requestCode == self.PLAY:
			self.rtspSeq+=1
			request = "PLAY movie.Mjpeg RTSP/1.0\n" + f"CSeq: {self.rtspSeq}\n"  + f"Session: {self.sessionId}"	
			self.requestSent = self.PLAY
		elif self.state == self.PLAYING and requestCode == self.PAUSE:
			self.rtspSeq+=1
			request = "PAUSE movie.Mjpeg RTSP/1.0\n" + f"CSeq: {self.rtspSeq}\n"  + f"Session: {self.sessionId}"	
			self.requestSent = self.PAUSE					

		self.rtspsocket.send(request.encode())
		print ('\nData Sent:\n' + request)

	def recvRtspReply(self):
		"""Receive RTSP reply from the server."""
		while True:
			reply = self.rtspsocket.recv(1024)
			if reply:
				self.parseRtspReply(reply)
			if self.requestSent == self.TEARDOWN:
				self.rtspsocket.close()
				break
	
	def parseRtspReply(self, data):
		"""Parse the RTSP reply from the server."""
		line_list = data.decode().split('\n')
		sequence_number = int(line_list[1].split(' ')[1])
		if sequence_number == self.rtspSeq:
			session_id = int(line_list[2].split(' ')[1])

			if self.sessionId == 0:
				self.sessionId = session_id

			if int(line_list[0].split(' ')[1]) == 200: 
				if self.requestSent == self.SETUP:
					self.state = self.READY
					self.openRtpPort() 

				elif self.requestSent == self.PLAY:
					self.state = self.PLAYING

				elif self.requestSent == self.PAUSE: #Server ngừng gửi rtp packet
					self.state = self.READY

				elif self.requestSent == self.TEARDOWN:
					self.rtpSocket.close()
					os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT)

	
	def openRtpPort(self):
		"""Open RTP socket binded to a specified port."""
		self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		try:
			self.rtpSocket.bind(('',self.rtpPort))
		except:
			print("Error")

