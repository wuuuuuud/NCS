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
        Tao=CS_User(id=1,username="wtxqgg",password="19921101",email="wtxqgg@gmail.com")
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


app = webapp2.WSGIApplication([
    ('/reset',ResetDataStoreHandler),
    ('/add/book/*',AddBookHandler),
    ('/list/book*',ListBookHandler),
    ('/create/tao',NewUserHandler),
    ('/check/1',CheckUsersHandler),
    ('/test/',TestHandler),
    ('/', MainHandler)
], debug=True)
