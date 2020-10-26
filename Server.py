#!/usr/bin/env python3

# -*- coding: utf-8 -*-

from flask import Flask, render_template, send_file, request, jsonify, send_from_directory
from time import sleep

FlaskServer = Flask(__name__, template_folder="web")

@FlaskServer.route("/")
def index(): return render_template("index.html")

@FlaskServer.route('/<path:path>')
def send_files(path): return send_from_directory(FlaskServer.template_folder, path)

FlaskServer.run(host='0.0.0.0', port=8080)