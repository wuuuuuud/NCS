#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import cgi
import datetime

from google.appengine.ext import db
from google.appengine.api import users

import datamodel
from datamodel import *
from webapp2_extras import sessions

class BaseHandler(webapp2.RequestHandler):
    def dispatch(self):
        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)

        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        # Returns a session using the default cookie key.
        return self.session_store.get_session()



def addBook(_bookname,_owner,_author):
    userkey=db.GqlQuery("SELECT __key__ FROM CS_User WHERE username='"+_owner+"' LIMIT 1").get()
    if (userkey):
        newbook=CS_Book(bookname=_bookname,author=_author)
        newbook.put()
        newrelation=CS_BookUser(bookKey=str(newbook.key()),userKey=str(userkey))
        newrelation.put()
        return "success!"
    else:
        return "no such user!"



class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write('<html><title>Test!</title><body>Hello world!</body></html>')
class TestHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write('good')

class NewUserHandler(webapp2.RequestHandler):
    def get(self):
        Tao=CS_User(username="wtxqgg",password="19921101",email="wtxqgg@gmail.com")
        Tao.put()

class CheckUsersHandler(webapp2.RequestHandler):
    def get (self):
        result=db.GqlQuery("SELECT * FROM CS_User")
        self.response.write(u"中文支持测试，堃")
        for p in result:
            self.response.write(p.username)

class ResetDataStoreHandler(webapp2.RequestHandler):
    def get(self):
        if self.request.get('passkey')=='asdfghjkl':
            db.delete(CS_User.all())
            db.delete(CS_Book.all())
            db.delete(CS_BookUser.all())

class AddBookHandler(webapp2.RequestHandler):
    def get(self):
        result=addBook(self.request.get('bookname'),self.request.get('owner'),self.request.get('author'))
        self.response.write(result);

class ListBookHandler(webapp2.RequestHandler):
    def get(self):
        q=db.GqlQuery("SELECT * FROM CS_Book")
        result=q.fetch(10)
        for r in result:
            self.response.write(r.bookname+r.author+str(r.key())+"<br/>")

class ListSeriesHandler(webapp2.RequestHandler):
    def get(self):
        pass

class RegisterUserHandler(BaseHandler):
    def post(self):
        _username=str(self.request.POST['username'])
        _password=self.request.POST['password']
        _email=self.request.POST['email']
        assumeexist=db.GqlQuery("SELECT __key__ FROM CS_User WHERE username='"+_username+"'").get()
        if (not assumeexist):
            newuser=CS_User(username=_username,password=_password,email=_email)
            newuser.put()
            self.response.write('succeeded in register')
        else:
            self.response.write('username already exists!')

class LoginHandler(BaseHandler):
    def post(self):
        _username=str(self.request.POST['username'])
        _password=self.request.POST['password']
        assumecorrect=db.GqlQuery("SELECT __key__ FROM CS_User WHERE username='"+_username+"' AND password='"+_password+"'").get()
        if (assumecorrect):
            self.session["loggedin"]="yes"
            self.response.write("succeeded in login!")
        else:
            self.response.write("failed on login,please recheck your password or username!")

class LoginTestHandler(BaseHandler):
    def get(self):
        if (self.session.get("loggedin")=="yes"):
            self.response.write("you have logged in!")
        else:
            self.response.write("something wrong must have happened somewhere...")


config = {}
config['webapp2_extras.sessions'] = {
    'secret_key': 'CounterTop',
}

app = webapp2.WSGIApplication([
    ('/reset',ResetDataStoreHandler),
    ('/add/book/*',AddBookHandler),
    ('/list/book*',ListBookHandler),
    ('/register/user/*',RegisterUserHandler),
    ('/login/user/*',LoginHandler),
    ('/check/login*',LoginTestHandler),
    ('/create/tao',NewUserHandler),
    ('/check/1',CheckUsersHandler),
    ('/test/',TestHandler),
    ('/', MainHandler)
], debug=True,config=config)
