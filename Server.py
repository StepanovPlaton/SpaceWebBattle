#!/usr/bin/env python3

# -*- coding: utf-8 -*-

from flask import Flask, render_template, send_file, request, jsonify, send_from_directory
from flask_socketio import *
from threading import Thread
import random, time, logging

import eventlet
eventlet.monkey_patch()

random.seed()

GameAreaWidth, GameAreaHeight = 1280, 720

FlaskServer = Flask(__name__, template_folder="web")

WebSocket = SocketIO(FlaskServer, async_mode="eventlet")

app_log = logging.getLogger('werkzeug')
file_handler = logging.FileHandler('Main.log', 'w')
app_log.addHandler(file_handler)
app_log.setLevel(logging.INFO)

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

class Player:
    def __init__(self, sid, X, Y, SpeedX, SpeedY, Angle, ChangeAnrgleSpeed, Team):
        self.id = sid
        self.X = X
        self.Y = Y
        self.SpeedX = SpeedX
        self.SpeedY = SpeedY
        self.Angle = Angle
        self.ChangeAnrgleSpeed = ChangeAnrgleSpeed
        self.TimeOut = time.time()
        self.Team = Team

def CreateChangePackage_for_Player(i):
    return [i, Players[i].id, Players[i].X, Players[i].Y, Players[i].SpeedX,
                  Players[i].SpeedY, Players[i].Angle, Players[i].ChangeAnrgleSpeed, Players[i].Team]

Asteroids = [None for i in range(100)]
NumberOfAsteroids = 0

Lasers = [None for i in range(100)]
NumberOfLasers = 0

Players = [None, None, None, None]
NumberOfPlayers = 0
NumberOfPlayersTeam1 = 0
NumberOfPlayersTeam2 = 0


OldTime, Time, DeltaTime = 0, 0, 0
SyncTime = int(round(time.time() * 1000))
PlayerSync = 0

def PhysicalCycle():
    time.sleep(2)
    global NumberOfAsteroids, Time, OldTime, DeltaTime, SyncTime, PlayerSync, NumberOfLasers, NumberOfPlayers, NumberOfPlayersTeam1, NumberOfPlayersTeam2
    while True:
        BOOM = False  

        OldTime = Time
        Time = int(round(time.time() * 1000))
        DeltaTime = Time - OldTime

        for i in range(len(Lasers)):
            if(Lasers[i] is None): continue
            
            Lasers[i].X += Lasers[i].SpeedX * DeltaTime/10
            Lasers[i].Y += Lasers[i].SpeedY * DeltaTime/10
            Lasers[i].Angle += Lasers[i].ChangeAnrgleSpeed * DeltaTime/10
            
            if(Lasers[i].X < 0 or Lasers[i].Y < 0 or Lasers[i].X > GameAreaWidth or Lasers[i].Y > GameAreaHeight):
                with FlaskServer.test_request_context('/'): WebSocket.emit("DestroyLaser", [i], broadcast=True)
                Lasers[i] = None
                NumberOfLasers -= 1
                break

            for j in range(len(Players)):
                if(Players[j] is None): continue
                if((Lasers[i].X - Players[j].X)**2 + (Lasers[i].Y - Players[j].Y)**2 < 20**2):
                    with FlaskServer.test_request_context('/'):
                        WebSocket.emit("DestroyLaser", [i], broadcast=True)
                        WebSocket.emit("DestroyPlayer", CreateChangePackage_for_Player(j), broadcast=True)
                        WebSocket.emit("BOOM", [Players[j].X, Players[j].Y], broadcast=True)
                    if(Players[j].Team == 1): NumberOfPlayersTeam2 -= 1
                    else: NumberOfPlayersTeam1 -= 1
                    Players[j] = None
                    NumberOfPlayers -= 1
                    Lasers[i] = None
                    BOOM = True
                    break
            if(BOOM): break
            for j in range(len(Asteroids)):
                if(Asteroids[j] is None): continue
                if((Lasers[i].X - Asteroids[j].X)**2 + (Lasers[i].Y - Asteroids[j].Y)**2 < (Asteroids[j].Scale*10)**2):
                    with FlaskServer.test_request_context('/'):
                        WebSocket.emit("DestroyLaser", [i], broadcast=True)
                        WebSocket.emit("DestroyAsteroid", ["DESTROY", j, -1], broadcast=True)
                        WebSocket.emit("BOOM", [Asteroids[j].X, Asteroids[j].Y], broadcast=True)
                    Lasers[i] = None
                    Asteroids[j] = None
                    NumberOfLasers -= 1
                    NumberOfAsteroids -= 1
                    BOOM = True
                    break
            if(BOOM): break
        BOOM = False
        for i in range(len(Asteroids)):
            if(Asteroids[i] == None):
                if(NumberOfAsteroids < 15):
                    while True:
                        X = Random(-10, GameAreaWidth+10)
                        Y = Random(-10, GameAreaHeight+10)
                        if(X < 0 or X > GameAreaWidth or Y < 0 or Y > GameAreaHeight): break
                    Asteroids[i] = SpaceObject(X, Y, Random(-0.05, 0.05), Random(-0.05, 0.05), Random(0, 360), Random(0, 1)/15, Random(1.5, 4.5))
                    with FlaskServer.test_request_context('/'): WebSocket.emit("CreateAsteroid", CreateChangePackage_for_Asteroid(i), broadcast=True)
                    NumberOfAsteroids += 1
                else: continue

            Asteroids[i].X += Asteroids[i].SpeedX * DeltaTime/20
            Asteroids[i].Y += Asteroids[i].SpeedY * DeltaTime/20
            Asteroids[i].Angle += Asteroids[i].ChangeAnrgleSpeed * DeltaTime/20
            
            if(Asteroids[i].X > GameAreaWidth+10 or Asteroids[i].X < -10 or
                   Asteroids[i].Y > GameAreaHeight+10 or Asteroids[i].Y < -10):
                while True:
                    Asteroids[i].X = Random(-10, GameAreaWidth+10)
                    Asteroids[i].Y = Random(-10, GameAreaHeight+10)
                    if(Asteroids[i].X < 0 or Asteroids[i].X > GameAreaWidth or
                            Asteroids[i].Y < 0 or Asteroids[i].Y > GameAreaHeight): break
                Asteroids[i].SpeedX = Random(-0.5, 0.5)
                Asteroids[i].SpeedY = Random(-0.5, 0.5)
                Asteroids[i].ChangeAnrgleSpeed = Random(0, 1)/15
                with FlaskServer.test_request_context('/'): WebSocket.emit("UpdateAsteroid", CreateChangePackage_for_Asteroid(i), broadcast=True)
            for j in range(len(Asteroids)):
                if(Asteroids[j] == None): continue

                if((Asteroids[j].X - Asteroids[i].X)**2 + (Asteroids[j].Y - Asteroids[i].Y)**2 < (max(Asteroids[j].Scale, Asteroids[i].Scale)*10)**2 and not i == j):
                    with FlaskServer.test_request_context('/'):
                        WebSocket.emit("BOOM", [(Asteroids[j].X+Asteroids[i].X)/2, (Asteroids[j].Y+Asteroids[i].Y)/2], broadcast=True)

                    Asteroids[i] = None
                    Asteroids[j] = None
                    with FlaskServer.test_request_context('/'):
                        WebSocket.emit("DestroyAsteroid", ["DESTROY", i, j], broadcast=True)

                    NumberOfAsteroids -= 2

                    BOOM = True
                    break
            if(BOOM): break
            for j in range(len(Players)):
                if(Players[j] is None): continue
                if(time.time() - Players[j].TimeOut > 1000):
                    Players[j] = None
                    print("Player", j, "Time Out")
                    continue
                Players[j].X += Players[j].SpeedX
                Players[j].Y += Players[j].SpeedY
                Players[j].Angle += Players[j].ChangeAnrgleSpeed
                if(Time - SyncTime < 100):
                    with FlaskServer.test_request_context('/'):
                        WebSocket.emit("UpdatePlayer", CreateChangePackage_for_Player(j), broadcast=True)
                
                if((Asteroids[i].X - Players[j].X)**2 + (Asteroids[i].Y - Players[j].Y)**2 < (Asteroids[i].Scale*10)**2):
                    with FlaskServer.test_request_context('/'):
                        WebSocket.emit("DestroyPlayer", CreateChangePackage_for_Player(j), broadcast=True)
                        WebSocket.emit("DestroyAsteroid", ["DESTROY", i, -1], broadcast=True)
                    Asteroids[i] = None
                    if(Players[j].Team == 1): NumberOfPlayersTeam1 -= 1
                    else: NumberOfPlayersTeam2 -= 1
                    Players[j] = None
                    NumberOfPlayers -= 1
                    break
                if(Players[j].X > GameAreaWidth or Players[j].X < 0 or Players[j].Y > GameAreaHeight or Players[j].Y < 0):
                    with FlaskServer.test_request_context('/'):
                        WebSocket.emit("DestroyPlayer", CreateChangePackage_for_Player(j), broadcast=True)
                    if(Players[j].Team == 1): NumberOfPlayersTeam1 -= 1
                    else: NumberOfPlayersTeam2 -= 1
                    Players[j] = None
                    NumberOfPlayers -= 1
                    break
            SyncTime = Time
        WebSocket.sleep(0.1)
            # Сделать осколки астероидов!

PhysicalCycleThread = Thread(target=PhysicalCycle)
PhysicalCycleThread.demon = True
PhysicalCycleThread.start()

@FlaskServer.route("/")
def Index(): return render_template("index.html")

@FlaskServer.route('/<path:path>')
def SendFiles(path): return send_from_directory(FlaskServer.template_folder, path)

@WebSocket.on('PlayerData')
def PlayerData(Data):
    for i in range(len(Players)):
        if(not Players[i] is None):
            if(Players[i].id == request.sid):
                if(Players[i].X == 0 and Players[i].Y == 0):
                    emit("CreatePlayer", CreateChangePackage_for_Player(i), broadcast=True)
                Players[i].X = Data[0]
                Players[i].Y = Data[1]
                Players[i].SpeedX = Data[2]
                Players[i].SpeedY = Data[3]
                Players[i].Angle = Data[4]
                Players[i].ChangeAnrgleSpeed = Data[5]
                Players[i].TimeOut = time.time()

@WebSocket.on('Fire')
def Fire(Data):
    global NumberOfLasers
    for i in range(len(Lasers)):
        if(Lasers[i] is None):
            Lasers[i] = SpaceObject(Data[0], Data[1], Data[2], Data[3], Data[4], Data[5], 0)
            emit("CreateLaser", [i, Data[0], Data[1], Data[2], Data[3], Data[4], Data[5]], broadcast=True)
            NumberOfLasers += 1
            break
            
@WebSocket.on('NewPlayer')
def NewPlayer():
    global NumberOfPlayers, NumberOfPlayersTeam1, NumberOfPlayersTeam2
    for i in range(len(Players)):
        if(Players[i] is None):
            team =0
            if(NumberOfPlayersTeam1 > NumberOfPlayersTeam2):
                team = 1
                NumberOfPlayersTeam2 += 1
            else:
                team = -1
                NumberOfPlayersTeam1 += 1
            emit("You", [i, request.sid, team])
            Players[i] = Player(request.sid, 0, 0, 0, 0, 0, 0, team)
            NumberOfPlayers += 1
            break
    for i in range(len(Players)):
        if(not Players[i] is None): emit("CreatePlayer", CreateChangePackage_for_Player(i))
    for i in range(len(Asteroids)):
        if(not Asteroids[i] is None): emit("CreateAsteroid", CreateChangePackage_for_Asteroid(i))

WebSocket.run(FlaskServer, host="0.0.0.0", port=8080, log_output=True)
