#Tornado Libraries
from tornado.ioloop import IOLoop
from tornado.escape import json_encode
from tornado.web import RequestHandler, Application, asynchronous, removeslash
from tornado.httpserver import HTTPServer
from tornado.httpclient import AsyncHTTPClient
from tornado.gen import engine, Task, coroutine,sleep

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
#set time values of morning,afternoon,evening
#format hr,min
'''
morning=(8,30)
afternoon=(1,30)
evening=(8,0)
'''
GPIO.setboard(GPIO.BOARD)
GPIO.setup(18,GPIO.OUT)
GPIO.output(18,False)

morning=8
afternoon=16
evening=20

#db=MotorClient().localPi
'''
class CommandPi(RequestHandler):
    def get(self):
        self.render('index.html')
'''
try:
    db=MotorClient("mongodb://med:med@ds048719.mlab.com:48719/md")["md"]
except:
    db=MotorClient().localPi
@coroutine
def checkUpdate():
    #pi can access the server from internet if its connected to net download data and store in his own db
    #s=secureid #this is used to configure pi
    # the secureid and the user cookie must be same for the pi to run properly
    print("inside checkUpdate")
    db=MotorClient().localPi
    s=ObjectId("57e42085f660382cb0b4dc51")
    result=yield db.prescriptions.find_one({'aliases':{'toid':s}})
    if bool(result):
        print result
    try:
        db2=MotorClient("mongodb://med:med@ds048719.mlab.com:48719/md")["md"]
        resultOnline=yield db2.prescriptions.find_one({'aliases':{'toid':ObjectId(s)}})
        x=yield db2.prescriptions.find_one()
        print x
        print 'hkjsdhlf'
        print resultOnline
        if bool(resultOnline):
            print resultOnline
        #if bool(resultOnline) and resultOnline!=result:
            #db.prescriptions.remove({})
            #yield db.prescriptions.insert(result)
            #now=datetime.now()
            #time=now.strftime("%d-%m-%Y %I:%M %p")
            #yield db.prescriptions.findOneAndUpdate({'$set':{'startTime':time}})
        else:
            print("up to date")
    except:
        pass
    print 'outside it'   
    
@coroutine
def minute_loop2():
    db=MotorClient("mongodb://med:med@ds048719.mlab.com:48719/md")["md"]
    while True:
        nxt = sleep(60) # Start the clock.
        s=ObjectId("57e42085f660382cb0b4dc51")
        prescription=yield db.prescriptions.find_one({'aliases':{'toid':ObjectId(s)}})
        t=datetime.now().hour
        print t
        try:
            print prescription['medicines'][0]['afternoon']
        except:
            try:
                db=MotorClient("mongodb://med:med@ds048719.mlab.com:48719/md")["md"]
                prescription=yield db.prescriptions.find_one({'aliases':{'toid':ObjectId(s)}})
            except:
                pass    
                
        if bool(prescription['medicines'][0]['morning']) and t==morning:
            sendMessage(userInfo['contact'],'time for medicine')
            GPIO.output(18,True)
            
        elif bool(prescription['medicines'][0]['afternoon']) and t==afternoon:
            sendMessage(userInfo['contact'],'time for medicine')
            GPIO.output(18,True)
        elif bool(prescription['medicines'][0]['evening']) and t==evening:
            sendMessage(userInfo['contact'],'time for medicine')
            GPIO.output(18,True)
        yield nxt # Wait for the timer to run out.      
#to be implemented later        
'''     
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
            
'''

                
'''        
settings = dict(
        template_path = os.path.join(os.path.dirname(__file__), "templates"),
        static_path = os.path.join(os.path.dirname(__file__), "static"),
        debug=True)

application=Application([
(r"/",CommandPi)
],**settings)
'''
if __name__ == "__main__":
    #server = HTTPServer(application)
    #server.listen(os.environ.get("PORT", 8000))
    #IOLoop.current().start()
    main_loop=IOLoop.instance()
    #PeriodicCallback(checkTime.checkTimeAndSay,500,main_loop).start()
    IOLoop.current().run_sync(checkUpdate)
    IOLoop.current().spawn_callback(minute_loop2)
    
    IOLoop.current().start()    
        
