#!/usr/bin/env python3

# -*- coding: utf-8 -*-

from flask import Flask, render_template, send_file, request, jsonify, send_from_directory
from flask_socketio import SocketIO, send, emit
from threading import Thread
import random, time

random.seed()

GameAreaWidth, GameAreaHeight = 1280, 720

FlaskServer = Flask(__name__, template_folder="web")

WebSocket = SocketIO(FlaskServer)

def Random(min, max): return random.random() * (max - min) + min;

class SpaceObject:
	def __init__(self, X, Y, SpeedX, SpeedY, Angle, ChangeAnrgleSpeed, Scale):
		self.X = X
		self.Y = Y
		self.SpeedX = SpeedX
		self.SpeedY = SpeedY
		self.Angle = Angle
		self.ChangeAnrgleSpeed = ChangeAnrgleSpeed
		self.Scale = Scale

def CreateChangePackage_for_Asteroid(i):
	return [i, Asteroids[i].X, Asteroids[i].Y, Asteroids[i].SpeedX,
				Asteroids[i].SpeedY, Asteroids[i].Angle, Asteroids[i].ChangeAnrgleSpeed, Asteroids[i].Scale]

class Laser(SpaceObject):
	def __init__(self, Whose, X, Y, SpeedX, SpeedY, Angle, ChangeAnrgleSpeed):
		super().__init__(X, Y, SpeedX, SpeedY, Angle, ChangeAnrgleSpeed)
		self.Whose = Whose

class Player:
	def __init__(self, sid, X, Y, SpeedX, SpeedY, Angle, ChangeAnrgleSpeed):
		self.id = sid
		self.X = X
		self.Y = Y
		self.SpeedX = SpeedX
		self.SpeedY = SpeedY
		self.Angle = Angle
		self.ChangeAnrgleSpeed = ChangeAnrgleSpeed
		self.LastPackage = time.time()

Asteroids = [None for i in range(100)]
NumberOfAsteroids = 0

Lasers = [None for i in range(100)]

Players = []

def PhysicalCycle():
	time.sleep(2)
	global NumberOfAsteroids
	while True:
		BOOM = False
		for i in range(len(Asteroids)):
			if(Asteroids[i] == None):
				if(NumberOfAsteroids < 15):
					while True:
						X = Random(-10, GameAreaWidth+10)
						Y = Random(-10, GameAreaHeight+10)
						if(X < 0 or X > GameAreaWidth or Y < 0 or Y > GameAreaHeight): break 
					Asteroids[i] = SpaceObject(X, Y, Random(0.05, 0.5), Random(0.05, 0.5), Random(0, 360), Random(0, 1)/15, Random(1, 3.5))
					with FlaskServer.test_request_context('/'):
						WebSocket.emit("ChangeAsteroid", CreateChangePackage_for_Asteroid(i), broadcast=True)
					NumberOfAsteroids += 1
				else: continue
	
			Asteroids[i].X += Asteroids[i].SpeedX
			Asteroids[i].Y += Asteroids[i].SpeedY
			Asteroids[i].Angle += Asteroids[i].ChangeAnrgleSpeed
			if(Asteroids[i].X > GameAreaWidth+10 or Asteroids[i].X < 0 or 
							Asteroids[i].Y > GameAreaHeight+10 or Asteroids[i].Y < 0):
				while True:
					Asteroids[i].X = Random(-10, GameAreaWidth+10)
					Asteroids[i].Y = Random(-10, GameAreaHeight+10)
					if(Asteroids[i].X < 0 or Asteroids[i].X > GameAreaWidth or 
						Asteroids[i].Y < 0 or Asteroids[i].Y > GameAreaHeight): break
				with FlaskServer.test_request_context('/'):
					WebSocket.emit("ChangeAsteroid", CreateChangePackage_for_Asteroid(i), broadcast=True)
			for j in range(len(Asteroids)):
				if(Asteroids[j] == None): continue
				if(abs(Asteroids[j].X - Asteroids[i].X) < 20 and abs(Asteroids[j].Y - Asteroids[i].Y) < 20 and not i == j):
					with FlaskServer.test_request_context('/'):
						WebSocket.emit("BOOM", [(Asteroids[j].X+Asteroids[i].X)/2, (Asteroids[j].Y+Asteroids[i].Y)/2], broadcast=True)
					Asteroids[i] = None
					Asteroids[j] = None
					with FlaskServer.test_request_context('/'):
						WebSocket.emit("ChangeAsteroid", [i, "DESTROY"], broadcast=True)
						WebSocket.emit("ChangeAsteroid", [j, "DESTROY"], broadcast=True)
					NumberOfAsteroids -= 2
	
					BOOM = True
					break
			if(BOOM): break
			# Сделать осколки астероидов!

PhysicalCycleThread = Thread(target=PhysicalCycle)
PhysicalCycleThread.demon = True
PhysicalCycleThread.start()

@FlaskServer.route("/")
def Index(): return render_template("index.html")

@FlaskServer.route('/<path:path>')
def SendFiles(path): return send_from_directory(FlaskServer.template_folder, path)

@WebSocket.on('NewPlayer')
def NewPlayer(Data):
	print("!NEW PLAYER!")
	Players.append(Player(request.sid, Data[0], Data[1], Data[2], Data[3], Data[4], Data[5]))

WebSocket.run(FlaskServer, host="0.0.0.0", port=8090)
#FlaskServer.run(host='0.0.0.0', port=8080)