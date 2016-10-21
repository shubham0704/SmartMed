#Tornado Libraries
from tornado.ioloop import IOLoop,PeriodicCallback
from tornado.escape import json_encode
from tornado.web import RequestHandler, Application, asynchronous, removeslash
from tornado.httpserver import HTTPServer
from tornado.httpclient import AsyncHTTPClient
from tornado.gen import engine, Task, coroutine,sleep
from tornado.websocket import WebSocketHandler
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
from utilityFunctions import hashingPassword,setUserInfo,sendMessage
import textwrap
import random
from datetime import datetime
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from PIL import Image
import logging
#import RPi.GPIO as GPIO

#GPIO.setboard(GPIO.BOARD)
#GPIO.setup(10,GPIO.OUT)
#GPIO.output(10,False)
morning=8
afternoon=16
evening=20
db=MotorClient("mongodb://med:med@ds048719.mlab.com:48719/md")["md"]
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
        contact=self.get_argument('contact')
        if not(bool(username) and bool(password) and bool(name) and bool(re.search(r".+@\w+\.(com|co\.in)",email))):
            self.redirect('/?username&email=empty')
            return
        desig=desig.lower()
        result = yield db.users.find_one({'username':username, 'email':email, 'desig':desig})
        if(bool(result)):
            self.redirect('/?username&email=taken')
        else:
            password=hashingPassword(password)
            password=hashlib.sha256(password).hexdigest()
            now=datetime.now()
            time=now.strftime("%d-%m-%Y %I:%M %p")
            result = yield db.users.insert({'photo_link' : '','username' : username, 'password' : password, 'email' : email, 'name' : name,'services' : [],'contact':contact,
                                            'desig':desig,'signup' : 0,'social_accounts' : {}, 'joined_on' : time})
            self.set_secure_cookie('user',str(result))
            message = 'Hey ' + name + ', Welcome to AutoMed!'
            # message = 'Hey' + name + ', Welcome to AutoMed!'
            sendMessage(contact, message)
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
        validppl=list()
        if bool(self.get_secure_cookie('user')):
            current_id = self.get_secure_cookie('user')
            userInfo = yield db.users.find_one({'_id':ObjectId(current_id)})
            print userInfo
            validmsg=db.serviceRequests.find({'aliases':{'toid':ObjectId(current_id)},'Service.0.accepted':1})
            if validmsg:
             while (yield validmsg.fetch_next):
                         wdoc = validmsg.next_object()
                         print '\nrecieved requests'
                         print wdoc
                         validppl.append(wdoc)
            #validmsg=db.serviceRequests.find({'aliases.0.fromid':ObjectId(current_id),'Service.0.accepted':1})
            #if validmsg:
            # while (yield validmsg.fetch_next):
            #            wdoc = validmsg.next_object()
            #            print '\nsent requests'
            #            print wdoc
            #            validppl1.append(wdoc)

            self.render('doc_dash.html',validppl=validppl,result = dict(name='AutoMed',userInfo=userInfo,loggedIn = bool(self.get_secure_cookie("user"))))
        else:
            self.redirect('/?loggedIn=False')


class PatientDashboardHandler(RequestHandler):
    @removeslash
    @coroutine
    def get(self):
        userInfo=None
        if bool(self.get_secure_cookie('user')):
            current_id = self.get_secure_cookie('user')
            print current_id
            userInfo = yield db.users.find_one({'_id':ObjectId(current_id)})
            print userInfo

            validmsg=db.serviceRequests.find({'aliases':{'toid':ObjectId(current_id)},'Service.0.accepted':1})
            if validmsg:
             while (yield validmsg.fetch_next):
                         wdoc = validmsg.next_object()
                         print '\nrecieved requests'
                         print wdoc
                         validppl.append(wdoc)

            validmsg=db.serviceRequests.find({'aliases.0.fromid':ObjectId(current_id),'Service.0.accepted':1})
            if validmsg:
             while (yield validmsg.fetch_next):
                         wdoc = validmsg.next_object()
                         print '\nsent requests'
                         print wdoc
                         validppl1.append(wdoc)
            prescription=yield db.prescriptions.find_one({'aliases':{'toid':ObjectId(current_id)}})
            print prescription
            self.render('PatientDashboard.html',result = dict(name='AutoMed',userInfo=userInfo,prescription=prescription,loggedIn = bool(self.get_secure_cookie("user"))))
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
        srequest = yield db.serviceRequests.insert({'aliases':[{'fromid':s},{'toid':ObjectId(recvInfo['_id'])}],'Service':[{"accepted":0},{'service':service},{"sentby":userInfo["username"]},{"recievedby":recvInfo["username"]},{"time":time}]})
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
        result=db.serviceRequests.find({'aliases':{'toid':ObjectId(self.get_secure_cookie('user'))},'Service.0.accepted':0})
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

class PatientProfileHandler(RequestHandler):
    @coroutine
    @removeslash
    def get(self):
        s=self.get_secure_cookie('user')
        obId=self.get_argument('obId')
        if(bool(s)):
            result=db.serviceRequests.find({'aliases':{'fromid':ObjectId(obId),'toid':s},'Service.0.accepted':1})
            if(bool(result)):
                patInfo=yield db.users.find_one({'_id':ObjectId(obId)})
                print patInfo
                self.render('patient.html',patInfo=patInfo)         



class PrescriptionHandler(RequestHandler):
    @coroutine
    @removeslash
    def post(self):
        medname=False
        s=self.get_secure_cookie('user')
        print s
        obId=self.get_argument('obId')
        if(bool(s)):
            db.prescriptions.insert({'aliases':[{'fromid':ObjectId(s)},{'toid':ObjectId(obId)}]})
            mednames=self.get_arguments('med_0')
            mornings=self.get_arguments('Morning')
            afternoons=self.get_arguments('Afternoon')
            evenings=self.get_arguments('Evening')
            
            #durations=self.get_arguments('duration')
            
            mednames=[str(x) for x in mednames]
            mornings=[str(x) for x in mornings]
            afternoons=[str(x) for x in afternoons]
            evenings=[str(x) for x in evenings]
            
            #print "\nMedname: ",mednames
            #print "\nMornings: ",mornings
            #print "\nAfternoons: ",afternoons
            #print "\nEvenings: ",evenings
            daycount=self.get_argument('duration')
            if not daycount:
                daycount=0
            for i in range(5):
            
                if i> len(mednames):
                    break

                try:
                    morning=mornings[i]
                    afternoon=afternoons[i]
                    evening=evenings[i]
                    print morning,afternoon,evening
                    print mednames
                    result=yield db.prescriptions.update({'aliases':[{'fromid':ObjectId(s)},{'toid':ObjectId(obId)}]},{'$push':{'medicines':{'mn':mednames[i],'morning':mornings[i],'afternoon':afternoons[i],'evening':evenings[i],'daycount':int(daycount)}}})
               
                    print '\n',result
                except:
                    pass
                #duration=durations[i]
                
                #morning=self.get_argument('mor_'+str(i))
                #afternoon=self.get_argument('after_'+str(i))
                #evening=self.get_argument('evening_'+str(i))
                #daycount=self.get_argument('daycount_'+str(i))
                #morning=self.get_arguments('Morning')
                #afternoon=self.get_argument('Afternoon')
                #evening=self.get_argument('Evening')
                #daycount=self.get_argument('daycount_'+st)         
            self.redirect('/?addPrescription=True')
        else:
            self.redirect('/?loggedIn=False')
            
#class PItobetold(RequestHandler):
 #   def get(self):
        #pi can access the server from internet if its connected to net download data and store in his own db
        #s=secureid #this is used to configure pi
        # the secureid and the user cookie must be same for the pi to run properly
  #      result=db.prescriptions.find_one({'aliases':{'toid':ObjectId(s)}})
   #     if bool(result):
    #        db=MotorClient().medOfPi
     #       db.insert(result)
      #  else:
       #     self.write("NO prescription written yet")

class UserProfileHandler(RequestHandler):

    @coroutine
    @removeslash
    def get(self,username):
        data = []
        userInfo = None
        #userInfo = yield db.users.find_one({'_id' : ObjectId(self.get_secure_cookie('user'))})
        #data.append(setUserInfo(userInfo,'username','email','photo_link'))


        #if username != 'Dummy':

        userInfo = yield db.users.find_one({'username':username})
        if bool(userInfo):
            data.append(json.loads(json_util.dumps(userInfo)))

            if bool(self.get_secure_cookie('user')):
                print '\nData:',data,'\n'
                self.render('doc_others.html',result= dict(data=data,loggedIn = True))
            else:
                self.render('doc_others.html',result= dict(data=data,loggedIn = False))
        else:
            self.redirect('/?username=False')
        #else:
         #   userInfo = {}
          #  self.render('profile_others.html',result= dict(data=data,loggedIn = True))


class PItobetold(RequestHandler):
    @coroutine
    @removeslash
    def get(self):
        #pi can access the server from internet if its connected to net download data and store in his own db
        #s=secureid #this is used to configure pi
        # the secureid and the user cookie must be same for the pi to run properly

        db=MotorClient().med
        #s=ObjectId("57e42085f660382cb0b4dc51")
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
            #GPIO.output(int(message),True)
            self.write_message("Your Message: {}".format(message))

"""class BaseHandler(RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie('user')


class checkTime(BaseHandler):
    @coroutine
    def checkTimeAndSay(self):
        print 'yes'
        try: 
            s=self.get_current_user
            print '\n',s
        except:
            pass
        #prescription=yield db.prescriptions.find_one({'aliases':{'toid':ObjectId(s)}})
         try:
            prescription=yield db.prescriptions.find_one({'aliases':{'toid':ObjectId(s)}})
            print prescription
        except:
        time1=12
        t=datetime.now().hour
        if t==time1:
             #logging.info(t)
             print 'medicine time is',t
             #GPIO.output(10,True)
        else:
             print 'still checking'

        """
@coroutine
def minute_loop2():
    while True:
        nxt = sleep(60) # Start the clock.
        #user=current_user # Run while the clock is ticking.
        #print user
        #s=ObjectId('57a612faf66038127990ddb4')
        s=ObjectId("57e42085f660382cb0b4dc51")
        prescription=yield db.prescriptions.find_one({'aliases':{'toid':ObjectId(s)}})
        userInfo=yield db.users.find_one({'_id':s})
        #print userInfo
        #print prescription
        t=datetime.now().hour
        print t
        print prescription['medicines'][0]['afternoon']
        if bool(prescription['medicines'][0]['morning']) and t==morning:
            #sendMessage(userInfo['contact'],'time for medicine')
            pass
        elif bool(prescription['medicines'][0]['afternoon']) and t==afternoon:
            pass
            #sendMessage(userInfo['contact'],'time for medicine')
        elif bool(prescription['medicines'][0]['evening']) and t==evening:
            pass
            #sendMessage(userInfo['contact'],'time for medicine')
            
        yield nxt # Wait for the timer to run out.        
    
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
(r"/search",SearchHandler),
(r"/acceptService",AcceptServicesHandler),
(r"/serviceRequest",ServiceRequestHandler),
(r"/patient",PatientProfileHandler), 
(r"/prescribe",PrescriptionHandler),
(r"/echo",LedWs),
(r"/commandPi",CommandPi),
(r"/tellpi",PItobetold)
],**settings)

if __name__ == "__main__":
    server = HTTPServer(application)
    server.listen(os.environ.get("PORT", 5000))
    #IOLoop.instance().stop()
    main_loop=IOLoop.instance()
    #PeriodicCallback(checkTime.checkTimeAndSay,500,main_loop).start()
    IOLoop.current().spawn_callback(minute_loop2)
    IOLoop.current().start()
    
    

