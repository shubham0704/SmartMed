#Tornado Libraries
from tornado.ioloop import IOLoop
from tornado.escape import json_encode
from tornado.web import RequestHandler, Application, asynchronous, removeslash
from tornado.httpserver import HTTPServer
from tornado.httpclient import AsyncHTTPClient
from tornado.gen import engine, Task, coroutine

#Other Libraries
import urllib
from passlib.hash import sha256_crypt as scrypt
from motor import MotorClient
from bson import json_util
import json
import requests
import os, uuid, sys
import urllib2
import hashlib
from bson.objectid import ObjectId
import re
import pymongo
from utilityFunctions import hashingPassword
import textwrap
import random
from datetime import datetime
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from PIL import Image
import logging
import RPi.GPIO as GPIO
db=MotorClient().medOfPi
#set time values of morning,afternoon,evening
#format hr,min
morning=(8,30)
afternoon=(1,30)
evening=(8,0)
GPIO.setboard(GPIO.BOARD)
GPIO.setup(10,GPIO.OUT)
GPIO.output(10,False)
class PItobetold(RequestHandler):
	@coroutine
	@removeslash
	def get(self):
		#pi can access the server from internet if its connected to net download data and store in his own db
		#s=secureid #this is used to configure pi
		# the secureid and the user cookie must be same for the pi to run properly
		s='57a8a71bf6603810dea8c957'
		db=MotorClient().med
		result=yield db.prescriptions.find_one({'aliases':{'toid':ObjectId(s)}})
		if bool(result):
			db=MotorClient().medOfPi
			resultLocal=db.prescriptions.find()
			if bool(resultLocal) and resultLocal!=result:
			    db.prescriptions.remove({})
			yield db.prescriptions.insert(result)
			now=datetime.now()
			time=now.strftime("%d-%m-%Y %I:%M %p")
			yield db.prescriptions.findOneAndUpdate({'$set':{'startTime':time}})
		else:
			self.write("NO prescription written yet")
		self.redirect('/commandPi')
class CommandPi(RequestHandler):
	def get(self):
		result=db.prescriptions.find_one()
		
		
		
class LedWs(WebSocketHandler):
		

	def get_compression_options(self):
        # Non-None enables compression with default options.
		return {}

	def open(self):
		print "Connection open"
		self.write_message("Connection opened right now !")
		
	def on_close(self):
		logging.info("Connection closed from server side")
	def on_message(self,message):
		print "Message Recieved: {}".format(message)
		if (bool(int(message))):
			GPIO.output(int(message),True)
			self.write_message("Your Message: {}".format(message))
			

		
		
settings = dict(
		template_path = os.path.join(os.path.dirname(__file__), "templates"),
		static_path = os.path.join(os.path.dirname(__file__), "static"),
		debug=True)

application=Application([
(r"/", IndexHandler),
(r"/echo",LedWs)
],**settings)

if __name__ == "__main__":
	server = HTTPServer(application)
	server.listen(os.environ.get("PORT", 8000))
	IOLoop.current().start()
		
		
