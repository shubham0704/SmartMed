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

class IndexHandler(RequestHandler):
	@removeslash
	@coroutine
	def get(self):
		self.render('index.html')

class SignupHandler(RequestHandler):

    @removeslash
    @coroutine
    def post(self):
        username = self.get_argument('username_signup')
        password = self.get_argument('password_signup')
        name = self.get_argument('name')
        desig=self.get_argument('designation')
        email = self.get_argument('emailID')
        if not(bool(username) and bool(password) and bool(name) and bool(re.search(r".+@\w+\.(com|co\.in)",email))):
            self.redirect('/?username&email=empty')
            return

        result = yield db.users.find_one({'username':username, 'email':email, 'desig':desig})
        if(bool(result)):
            self.redirect('/?username&email=taken')
        else:
            password=hashingPassword(password)
            password=hashlib.sha256(password).hexdigest()
            now=datetime.now()
            time=now.strftime("%d-%m-%Y %I:%M %p")
            result = yield db.users.insert({'photo_link' : '','username' : username, 'password' : password, 'email' : email, 'name' : name,
                                            'signup' : 0,'social_accounts' : {}, 'joined_on' : time})
            self.set_secure_cookie('user',str(result))
			if desig=="doctor":
				self.redirect('/dashboard/doctor')
            else:
				self.redirect('/dashboard/patient')
            
class LoginHandler(RequestHandler):

    @removeslash
    @coroutine
    def post(self):
        username = self.get_argument('username')
        password = self.get_argument('password')

        password=hashingPassword(password)
        password=hashlib.sha256(password).hexdigest()
        result = yield db.users.find_one({'username': username, 'password': password, 'desig':desig})

        if bool(result):
            self.set_secure_cookie('user', str(result['_id']))
            if result['desig']=="doctor":
				self.redirect('/dashboard/doctor')
            else:
				self.redirect('/dashboard/patient')
               
        else:
            self.redirect('/?credentials=False')
            
class LogoutHandler(RequestHandler):
    @removeslash
    @coroutine
    def get(self):
        if bool(self.get_secure_cookie('user')):
            self.clear_cookie('user')
            self.redirect('/?loggedOut=true')
        else:
            self.redirect('/?activesession=false')
class DoctorDashboardHandler(RequestHandler):
	@removeslash
	@coroutine
	def get(self):
		userInfo=None
		if bool(self.get_secure_cookie('user')):
			current_id = self.get_secure_cookie('user')
            userInfo = yield db.users.find_one({'_id':ObjectId(current_id)})
            print userInfo
            self.render('profile_self.html',result = dict(name='AutoMed',userInfo=userInfo,loggedIn = bool(self.get_secure_cookie("user"))))
        else:
            self.redirect('/?loggedIn=False')
			
class PatientDashboardHandler(RequestHandler):
	@removeslash
	@coroutine
	def get(self):
		userInfo=None
		if bool(self.get_secure_cookie('user')):
			current_id = self.get_secure_cookie('user')
            userInfo = yield db.users.find_one({'_id':ObjectId(current_id)})
            print userInfo
            self.render('profile_self.html',result = dict(name='AutoMed',userInfo=userInfo,loggedIn = bool(self.get_secure_cookie("user"))))
        else:
            self.redirect('/?loggedIn=False')

		
		
settings = dict(
		template_path = os.path.join(os.path.dirname(__file__), "templates"),
		static_path = os.path.join(os.path.dirname(__file__), "static"),
		cookie_secret="35an18y3-u12u-7n10-4gf1-102g23ce04n6",
		debug=True)

application=Application([
(r"/", IndexHandler),
(r"/signup",SignupHandler),
(r"/login",LoginHandler),
(r"/dashboard/patient", PatientDashboardHandler),
(r"/dashboard/doctor",DoctorDashboardHandler) 
],**settings)

if __name__ == "__main__":
	server = HTTPServer(application)
	server.listen(os.environ.get("PORT", 5000))
	IOLoop.current().start()
	
