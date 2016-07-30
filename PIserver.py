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

db=MotorClient().med

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
											'desig':desig,'signup' : 0,'social_accounts' : {}, 'joined_on' : time})
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
        result = yield db.users.find_one({'username': username, 'password': password})

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
			self.render('DoctorDashboard.html',result = dict(name='AutoMed',userInfo=userInfo,loggedIn = bool(self.get_secure_cookie("user"))))
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
			self.render('PatientDashboard.html',result = dict(name='AutoMed',userInfo=userInfo,loggedIn = bool(self.get_secure_cookie("user"))))
		else:
			self.redirect('/?loggedIn=False')

class ServiceRequestHandler(RequestHandler):

    @coroutine
    @removeslash
    def get(self):

        if not bool(self.get_secure_cookie('user')):
            self.redirect('/?loggedIn=False')
            return

        service = self.get_argument('service')
        cost = self.get_argument('cost')
        email = self.get_argument('email')
        userInfo = yield db.users.find_one({'email':email})
        #validation
        for sinfo in userInfo['services']:
			if sinfo['service']==service and sinfo['cost']==cost:	
				self.render('servicerequest.html', result = {'user' : userInfo['username'], 'service' : service, 'cost' : cost})
				
        
        self.redirect('/profile/'+user)
    @coroutine
    @removeslash
    def post(self):
        service = self.get_argument('service')
        cost = self.get_argument('cost')
        recvUser = self.get_argument('user')
        s=self.get_secure_cookie('user')
        
        now = datetime.now()
        time = now.strftime("%d-%m-%Y %I:%M %p")
        userInfo=yield db.users.find_one({'_id':ObjectId(s)})
        recvInfo=yield db.users.find_one({'username':recvUser})
        #srequest = yield db.serviceRequests.insert({'From' : s, 'To' : recvUser, 'Service' : {'service' : service, 'cost' : cost,'accepted':0}})       
        srequest = yield db.serviceRequests.insert({'aliases':[{'fromid':s},{'toid':recvInfo['_id']}],'Service':[{"accepted":0},{'service':service},{"sentby":userInfo["username"]},{"recievedby":recvInfo["username"]},{"time":time}]})
        if bool(srequest):
            self.redirect('/?sendrequest=True')
        else:
            self.redirect('/?sendrequest=False')
            
class SearchHandler(RequestHandler):
    @coroutine
    @removeslash
    def post(self):
        STRING = self.get_argument('query')
        userlist = list()
        choices=list()
        word_doc = db.users.find({'desig':'doctor'})
        while (yield word_doc.fetch_next):
            doc = word_doc.next_object()
            try:
                choices.append(doc['username'])
            except:
                continue
        probableMatch = process.extract(STRING, choices, limit=5)
        choices = list(set(choices))

        for LIST in probableMatch:
            if LIST[1] > 70:
                pname = LIST[0]
                if pname in choices:
                    choices.remove(pname)
                    doc = db.users.find({'username': pname}, {'username': 1, '_id': 1, 'skills': 1})
                    while (yield doc.fetch_next):
                        wdoc = doc.next_object()
                        l2 = list()
                        l2.append(wdoc["username"])
                        try:
                            l2.append(wdoc['category'])
                        except:
                            pass
                        try:
                            l2.append(wdoc['skills'])
                        except:
                            pass
                        userlist.append(l2)
        self.render('searchresult.html', userlist=userlist)

class AcceptServicesHandler(RequestHandler):
    @removeslash
    @coroutine
    def get(self):
		#srequest=db.serviceRequests.find({})
		msgs=list()
		result=db.serviceRequests.find({'aliases':{'toid':ObjectId(self.get_secure_cookie('user'))}})
		while(yield result.fetch_next):
			doc=result.next_object()
			print doc
			msgs.append(doc)
		self.render("view_services.html",msgs=msgs)
    @removeslash
    @coroutine
    def post(self):
		sid=self.get_argument('sid')
		result=yield db.serviceRequests.find_one({'aliases':{'toid':ObjectId(self.get_secure_cookie('user'))},'_id':ObjectId(sid)})
		if bool(result):
			yield db.serviceRequests.update({'_id':ObjectId(sid)},{'$set':{'Service.0.accepted':1}})
			self.redirect('/?acceptService=True')
		else:
			self.redirect('/?acceptService=False') 			

class UserProfileHandler(RequestHandler):

    @coroutine
    @removeslash
    def get(self, username):
        data = []
        userInfo = None
        userInfo = yield db.users.find_one({'_id' : ObjectId(self.get_secure_cookie('user'))})
        data.append(setUserInfo(userInfo,'username','email','photo_link'))
        userInfo = None

        if username != 'Dummy':

            userInfo = yield db.users.find_one({'username':username})
            if bool(userInfo):
                data.append(json.loads(json_util.dumps(userInfo)))

                if bool(self.get_secure_cookie('user')):
                    self.render('profile_others.html',result= dict(data=data,loggedIn = True))
                else:
                    self.render('profile_others.html',result= dict(data=data,loggedIn = False))
            else:
                self.redirect('/?username=False')
        else:
            userInfo = {}
            self.render('profile_others.html',result= dict(data=data,loggedIn = True))		
settings = dict(
		template_path = os.path.join(os.path.dirname(__file__), "templates"),
		static_path = os.path.join(os.path.dirname(__file__), "static"),
		cookie_secret="35an18y3-u12u-7n10-4gf1-102g23ce04n6",
		debug=True)

application=Application([
(r"/", IndexHandler),
(r"/signup",SignupHandler),
(r"/login",LoginHandler),
(r"/profile/(\w+)",UserProfileHandler),
(r"/dashboard/patient", PatientDashboardHandler),
(r"/dashboard/doctor",DoctorDashboardHandler),	
(r"/search",SearchHandler) 
],**settings)

if __name__ == "__main__":
	server = HTTPServer(application)
	server.listen(os.environ.get("PORT", 5000))
	IOLoop.current().start()
	
