from tornado.ioloop import IOLoop
from tornado.escape import json_encode
from tornado.web import RequestHandler, Application, asynchronous, removeslash
from tornado.httpserver import HTTPServer
from tornado.httpclient import AsyncHTTPClient
from tornado.gen import engine, Task, coroutine
from tornado.websocket import WebSocketHandler
#Other Libraries
import urllib
#from passlib.hash import sha256_crypt as scrypt
import motor
from bson import json_util
import json
import requests
import os
#import urllib2
#import hashlib
from bson.objectid import ObjectId
import re
#import pymongo
#from utilityFunctions import sendMessage,sendRequestToken
import textwrap
import random
from datetime import datetime
import logging
import RPi.GPIO as GPIO

GPIO.setboard(GPIO.BOARD)
for i in range(14):
	GPIO.setup(i,GPIO.OUT)
	GPIO.output(i,False)
class IndexHandler(RequestHandler):
	def get(self):
		self.render("newpage1.html")
		


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
	server.listen(os.environ.get("PORT", 5000))
	IOLoop.current().start()
		
