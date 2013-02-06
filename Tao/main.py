﻿#!/usr/bin/env python
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
import jinja2
import os
import re

from google.appengine.ext import db
from google.appengine.api import users

import datamodel
from  toDict import *
from datamodel import *
from webapp2_extras import sessions
from webapp2_extras import json

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

class Utility:
    __keypattern=re.compile(r'(\w*-*[\w\-]*)')
    __intpattern=re.compile(r'(-?[0-9]+)')
    __listpattern=re.compile(r'(\w*-\w*)+')
    @staticmethod
    def getSafeKey(_in):
        _re=Utility.__keypattern.match(_in).group()
        return _re
    @staticmethod
    def getSafeInt(_in):
        _re=Utility.__intpattern.match(_in)
        if (_re):
            return int(_re.group())
        else:
            return -1
    __celllist={
                'english':['book','series','volume','part','chapter','node','paragraph'],
                'chinese':[u"书籍",u"系列",u"卷",u"部",u"章",u"节",u"段"],
                'tablename':['CS_Book','CS_Series','CS_Volume','CS_Part','CS_Chapter','CS_Node','CS_Paragraph'],
                }

def topNavigator(self,_leafkey=""):
    template_values = {
                'username': self.session.get('username'),
                'baseurl':self.request.host_url,
            }
    branch=[]
    _count=0
    _typelist=["series","volume","part","chapter","node","paragraph"]
    
    while (_leafkey!=""):
        _leaf=db.get(_leafkey)
        branch.insert(0,(_leaf.name,_leafkey,""))
        _count+=1
        try:
            _leafkey=_leaf.parentKey
        except:
            _leafkey=""
    for i in range(_count):
        branch[i]=(branch[i][0],branch[i][1],_typelist[i])
    template_values['path']=branch

        

    template = jinja_environment.get_template('navigator.html')
    return (template.render(template_values))

def addBook(_name,_owner,_author):
    userkey=db.GqlQuery("SELECT __key__ FROM CS_User WHERE username='"+_owner+"' LIMIT 1").get()
    if (userkey):
        newbook=CS_Book(name=_name,author=_author)
        newbook.put()
        newrelation=CS_BookUser(bookKey=str(newbook.key()),userKey=str(userkey))
        newrelation.put()
        return "success!"
    else:
        return "no such user!"

def addCell(_handlerinstance,argv):
    _userkey=_handlerinstance.session.get("key")
    _name=_handlerinstance.request.get("elementname")
    _bookkey=Utility.getSafeKey(_handlerinstance.request.get("bookkey"))
    _parentkey=Utility.getSafeKey(_handlerinstance.request.get("parentkey"))
    _insertafter=Utility.getSafeInt(_handlerinstance.request.get("insertafter"))
    _user=db.get(_userkey)
    _book=db.get(_bookkey)
    _relation=db.GqlQuery("SELECT * FROM CS_BookUser WHERE userKey='"+_userkey+"' AND bookKey='"+_bookkey+"'").get()
    if (_relation):
        _purview=_relation.purview
    else:
        _purview=""

    if (_purview=="owner"):
        _handlerinstance.response.write('purview valid!')
        _counts=db.GqlQuery("SELECT __key__ FROM "+argv["cellname"]+" WHERE bookKey='"+_bookkey+"'").count()
        _handlerinstance.response.write("counts:"+str(_counts))
        if ((_insertafter==-1) or (_counts==0) or (_insertafter>=_counts)):#no insertafter assigned or originally no series or overflow insertafter position
            _previouskey=db.GqlQuery("SELECT __key__ FROM "+argv["cellname"]+" WHERE order="+str(_counts)).get()
            if (_previouskey):
                _new=argv["celltype"](order=(_counts+1),bookKey=_bookkey,name=_name,previous=str(_previouskey),parentKey=_parentkey)
                _new.put()
                _previous=db.get(_previouskey)
                _previous.next=str(_new.key())
                _previous.put()
            else:
                _newseries=argv["celltype"](order=(_counts+1),bookKey=_bookkey,name=_name,previous="",parentKey=_parentkey)
                _newseries.put()
        elif (_insertafter<_counts):#originally at least one series AND legal insertafter position ,NEVER insert at the end
            _nextkey=db.GqlQuery("SELECT __key__ FROM "+argv["cellname"]+" WHERE order="+str(_insertafter+1)).get()
            _next=db.get(_nextkey)
            _new=argv["celltype"](order=(_insertafter+1),bookKey=_bookkey,name=_name,previous=(_next.previous),next=str(_nextkey),parentKey=_parentkey)
            _new.put()
            _next.previous=str(_new.key())
            _next.put()
            if (_insertafter!=0):
                _previous=db.get(_new.previous)
                _previous.next=str(_new.key())
                _previous.put()
            _affected=db.GqlQuery("SELECT * FROM "+argv["cellname"]+" WHERE order > "+str(_insertafter+1)+"AND parentKey ='"+_parentkey+"'").fetch(1000000)
            for _instance in _affected:
                _instance.order=_instance.order+1
                _instance.put()
            _next.order+=1
            _next.put()
        else:
            _handlerinstance.response.write('wrong insert-after position!')
            

def listCell(self,_parentkey,_page,argv={}):
        query=db.GqlQuery("SELECT * FROM "+argv['tablename']+" WHERE parentKey='"+_parentkey+"' ORDER BY order ASC")
        result=query.fetch(20,20*(_page-1))
        #self.session['currentSeriesKey']=str(_parentkey) 
        #self.session['currentSeriesName']=str(db.get(_parentkey).name) 
        self.response.write(topNavigator(self,_parentkey))
        _count=db.GqlQuery("SELECT * FROM "+argv['tablename']+" WHERE parentKey='"+_parentkey+"' ORDER BY order DESC").get()
        if (_count):
            _count=_count.order
        else:
            _count=0

        _bookkey=_parentkey
        if (argv['celltype']!='series'):
            _bookkey=db.get(_parentkey).bookKey

        template_values={
                         'list':result,
                         'listtype':argv['celltype'],
                         'childtype':argv['childcelltype'],
                         'fatherkey':_parentkey,
                         'bookkey':_bookkey,
                         'namedescription':argv["celltypeinchinese"],
                         'TotalListLength':_count,
                         
                         }
        template=jinja_environment.get_template('list.html')
        self.response.write(template.render(template_values))

def addParagraph(self,_parentKey,_content,_insertafter,argv={}):
    _parentNode=db.get(_parentKey)
    _count=db.GqlQuery("SELECT __key__ FROM CS_Paragraph WHERE parentKey='"+_parentKey+"'").count()
    if (_insertafter<0 or _insertafter>=_count):
        _new=CS_Paragraph(parentKey=_parentKey,order=_count+1,content=_content,comments=[])
        if (_count>0 and _insertafter!=0):
            _previous=db.GqlQuery("SELECT * FROM CS_Paragraph WHERE parentKey='"+_parentKey+"' AND order="+str(_count)).get()
            _new.previous=str(_previous.key())
        _new.put()
        if (_previous):
            _previous.next=str(_new.key())
            _previous.put()
    else:
        _new=CS_Paragraph(parentKey=_parentKey,order=_insertafter+1,content=_content,comments=[])
        if (_insertafter!=0):
            _previous=db.GqlQuery("SELECT * FROM CS_Paragraph WHERE parentKey='"+_parentKey+"' AND order="+str(_insertafter)).get()
            _new.previous=str(_previous.key())
        _next=db.GqlQuery("SELECT * FROM CS_Paragraph WHERE parentKey='"+_parentKey+"' AND order="+str(_insertafter+1)).get()
        _new.next=str(_next.key())
        _new.put()
        if (_insertafter!=0):
            _previous.next=str(_new.key())
            _previous.put()
        _affected=db.GqlQuery("SELECT * FROM CS_Paragraph WHERE parentKey='"+_parentKey+"' AND order > "+str(_insertafter+1)).fetch(1000000)
        for _instance in _affected:
            _instance.order+=1
            _instance.put()
        _next.order+=1
        _next.put() 

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

class AddBookHandler(BaseHandler):
    def get(self):
        if (self.session.get("loggedin")!=""):
            result=addBook(self.request.get('elementname'),self.session.get('username'),self.request.get('author'))
            self.response.write(result)
        else:
            self.response.write('please <a href="../../static/login.html">log in</a> to add a new book')

class AddSeriesHandler(BaseHandler):
    def get(self):
        argv={
              'cellname':"CS_Series",
              "celltype":CS_Series,
              }
        addCell(self,argv)

class AddVolumeHandler(BaseHandler):
    def get(self):
        argv={
              'cellname':"CS_Volume",
              "celltype":CS_Volume,
              }
        addCell(self,argv)

class AddPartHandler(BaseHandler):
    def get(self):
        argv={
              'cellname':"CS_Part",
              "celltype":CS_Part,
              }
        addCell(self,argv)

class AddChapterHandler(BaseHandler):
    def get(self):
        argv={
              'cellname':"CS_Chapter",
              "celltype":CS_Chapter,
              }
        addCell(self,argv) 

class AddNodeHandler(BaseHandler):
    def get(self):
        argv={
              'cellname':"CS_Node",
              "celltype":CS_Node,
              }
        addCell(self,argv)       

class ListBookHandler(BaseHandler):
    def get(self):
        q=db.GqlQuery("SELECT * FROM CS_Book")
        result=q.fetch(20)
        _counts=q.count()
        self.response.write(topNavigator(self))
        
        template_values={
                          'list':result,
                          'listtype':'book',
                          'childtype':'series',
                          'fatherkey':'',
                          'bookkey':'',
                          'namedescription':u'书籍',
                          'TotalListLength':_counts
                          }
        template=jinja_environment.get_template('list.html')
        self.response.write(template.render(template_values))
        #for r in result:
        #    self.response.write(r.name+r.author+str(r.key())+"<br/>")



class ListCellHandler(BaseHandler):
    def get(self,_type,_parentkey,_page="1"):
        _page=Utility.getSafeInt(_page)
        if (_page<=0) :
            _page=1
        argv={
              'childcelltype':Utility._Utility__celllist['english'][Utility._Utility__celllist['english'].index(_type)+1],
              'celltype':_type,
              'tablename':Utility._Utility__celllist['tablename'][Utility._Utility__celllist['english'].index(_type)],
              'celltypeinchinese':Utility._Utility__celllist['chinese'][Utility._Utility__celllist['english'].index(_type)],
              }
        listCell(self,_parentkey,_page,argv)
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
            user=db.get(assumecorrect)
            self.session["loggedin"]="yes"
            self.session["username"]=user.username
            self.session["key"]=str(assumecorrect)
            self.response.write("succeeded in login!"+user.username)
        else:
            self.response.write("failed on login,please recheck your password or username!")

class LoginTestHandler(BaseHandler):
    def get(self):
        if (self.session.get("loggedin")=="yes"):
            self.response.write("you have logged in!")
        else:
            self.response.write("you haven't logged in,if not,something wrong must have happened somewhere...")

class LogoutHandler(BaseHandler):
    def get(self):
        self.session["loggedin"]=""
        self.session["username"]=""
        self.session["key"]=""
        self.response.write("you have logged out!")

class AddParagraphHandler(BaseHandler):
    def post(self):
        _content=self.request.get('content')
        _parentKey=Utility.getSafeKey(self.request.get('parentkey'))
        _insertafter=self.request.get('insertafter')
        _bookKey=self.request.get("bookkey")
        if (_insertafter!=""):
            _insertafter=Utility.getSafeInt(_insertafter)
        else:
            _insertafter=-1
        try:
            _purview=db.GqlQuery("SELECT * FROM CS_BookUser WHERE userKey='"+self.session.get("key")+"' AND bookKey='"+_bookKey+"'").get().purview
            if (_purview=="owner"):
                addParagraph(self,_parentKey,_content,_insertafter)
        except:
            pass

        
class ListParagraphHandler(BaseHandler):
    def get(self,_parentKey,_page):
        result=db.GqlQuery("SELECT * FROM CS_Paragraph WHERE parentKey='"+_parentKey+"' ORDER BY order ASC").fetch(100000)
        self.response.write(topNavigator(self,_parentKey))
        template_values={
                          'result':result,
                          }
        template=jinja_environment.get_template('content.html')
        self.response.write(template.render(template_values))

class AddCommentHandler(BaseHandler):
    def post(self):
        _content=self.request.get('content')
        _userKey=Utility.getSafeKey(self.session.get('key'))
        _startNode=Utility.getSafeKey(self.request.get('startNode'))
        _endNode=Utility.getSafeKey(self.request.get('endNode'))
        _startOffset=Utility.getSafeInt(self.request.get('startOffset'))
        _endOffset=Utility.getSafeInt(self.request.get('endOffset'))
        _relatedNodes=re.split("#_#",self.request.get('relatedNodes'))
        
        _new=CS_Comment(content=_content,userKey=_userKey,\
            firstNode=_startNode,lastNode=_endNode,\
            startOffset=_startOffset,endOffset=_endOffset,\
            relatedNodes=_relatedNodes)
        _new.put()
        _newkey=str(_new.key())
        for _key in _relatedNodes:
            _paragraph=db.get(_key)
            _paragraph.comments.append(_newkey)
            _paragraph.put()

class ListCommentHandler(BaseHandler):
    def get(self,_parentKey,_page=1):
        _paragraph=db.get(_parentKey)
        
        for _commentKey in _paragraph.comments:
            _comment=CS_Comment.get(_commentKey)
            _result.insert(0,to_dict(_comment))
        self.response.write(json.encode(_result))

class AddMultiplyChapterAndNodeAndParagraphHandler(BaseHandler):
    def post(self):
        _str=self.request.get("data")
        _parentKey=Utility.getSafeKey(self.request.get("parentKey"))
        _bookKey=Utility.getSafeKey(self.request.get("bookKey"))
        _userKey=self.session.get("key")
        if(1):
            _purview=db.GqlQuery("SELECT * FROM CS_BookUser WHERE userKey='"+self.session.get("key")+"' AND bookKey='"+_bookKey+"'").get().purview
            if (_purview=="owner"):
                _s={}
                _currentChapterO=0
                _q=db.GqlQuery("SELECT * FROM CS_Chapter WHERE parentKey='"+_parentKey+"' ORDER BY order DESC LIMIT 1")
                if (_q.count()>0):
                    _s['currentC']=_q.get()
                    _currentChapterO=_s.get('currentC').order
                _currentNodeO=0
                _currentParagraphO=0
                result=re.search(r"<(?P<pattern>.*?)>(.*?)</(?P=pattern)>",\
                    _str,re.U and re.L and re.S)
                while (result):
                    if (result.group(1)=="chapter"):
                        if (_currentChapterO==0):
                            _new=CS_Chapter(order=_currentChapterO+1,\
                            parentKey=_parentKey,name=result.group(2),\
                            previous="",\
                            bookKey=_bookKey)
                            _new.put()
                        else:
                            _new=CS_Chapter(order=_currentChapterO+1,\
                            parentKey=_parentKey,name=result.group(2),\
                            previous=str(_s.get('currentC').key()),\
                            bookKey=_bookKey)
                            _new.put()
                            _s.get('currentC').next=str(_new.key())
                            _s.get('currentC').put()
                        _currentChapterO+=1
                        _currentNodeO=0
                        _currentParagraphO=0
                        
                        _s['currentC']=_new
                    elif (result.group(1)=="node"):
                        if (_currentNodeO==0):
                            _new=CS_Node(order=_currentNodeO+1,\
                                parentKey=str(_s.get('currentC').key()),\
                                name=result.group(2),\
                                previous="",\
                                bookKey=_bookKey)
                            _new.put()
                            
                        else:
                            _new=CS_Node(order=_currentNodeO+1,\
                                parentKey=str(_s.get('currentC').key()),\
                                name=result.group(2),\
                                previous=str(_s.get('currentN').key()),\
                                bookKey=_bookKey)
                            _new.put()
                            _s.get('currentN').next=str(_new.key())
                            _s.get('currentN').put()
                        _s['currentN']=_new
                        _currentNodeO+=1
                        _currentParagraphO=0
                    elif(result.group(1)=="p"):
                        if (_currentParagraphO==0):
                            _new=CS_Paragraph(order=_currentParagraphO+1,\
                                parentKey=str(_s.get('currentN').key()),\
                                content=result.group(2),\
                                previous="",\
                                bookKey=_bookKey)
                            _new.put()
                            
                        else:
                            _new=CS_Paragraph(order=_currentParagraphO+1,\
                                parentKey=str(_s.get('currentN').key()),\
                                content=result.group(2),\
                                previous=str(_s.get('currentP').key()),\
                                bookKey=_bookKey)
                            _new.put()
                            _s.get('currentP').next=str(_new.key())
                            _s.get('currentP').put()
                        _s['currentP']=_new
                        _currentParagraphO+=1
                    _str=_str[result.end():]
                    result=re.search(r"<(?P<pattern>.*?)>(.*?)</(?P=pattern)>",\
                    _str,re.U and re.L and re.S)

class ApiGetMultiplyCommentHandler(BaseHandler):
    def post(self):
        _plist= self.request.get("paragraphList")
        _paragraphs=re.split("#_#",_plist)
        _comments=[]
        _result=[]
        for _pKey in _paragraphs:
            _p=CS_Paragraph.get(_pKey)
            _comments+=_p.comments
        _comments=set(_comments)
        for _cKey in _comments:
            _comment=CS_Comment.get(_cKey)
            _result.insert(0,to_dict(_comment))
        self.response.write(json.encode(_result))



                 
config = {}
config['webapp2_extras.sessions'] = {
    'secret_key': 'CounterTop',  
}

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)+"/template"))# jinja2 config,set dir

app = webapp2.WSGIApplication([
    ('/reset',ResetDataStoreHandler),
    (r'/add/book/*',AddBookHandler),
    (r'/list/((?:series)|(?:volume)|(?:part)|(?:chapter)|(?:node))/(\w*-*[\w\-]*)/?([0-9]*)',ListCellHandler),
    (r'/list/book/*',ListBookHandler),
    (r'/list/paragraph/(\w*-*[\w\-]*)/?([0-9]*)',ListParagraphHandler),
    (r'/list/comment/(\w+-*\w+)/?',ListCommentHandler),
    (r'/add/series/*',AddSeriesHandler),
    (r'/add/volume/*',AddVolumeHandler),
    (r'/add/part/*',AddPartHandler),
    (r'/add/chapter/*',AddChapterHandler),
    (r'/add/node/*',AddNodeHandler),
    (r'/add/paragraph/*',AddParagraphHandler),
    (r'/add/comment/*',AddCommentHandler),
    (r'/manage/add/*',AddMultiplyChapterAndNodeAndParagraphHandler),
    (r'/get/multiply/comment/*',ApiGetMultiplyCommentHandler),
    (r'/register/user/*',RegisterUserHandler),
    (r'/logout/user/*',LogoutHandler),
    (r'/login/user/*',LoginHandler),
    (r'/check/login/*',LoginTestHandler),
    ('/create/tao',NewUserHandler),
    ('/check/1',CheckUsersHandler),
    ('/test/',TestHandler),
    ('/', MainHandler)
], debug=True,config=config)


#(r'/list/series/(\w*-\w*)/*',ListSeriesHandler),
#    (r'/list/series/(\w*-\w*)/([0-9]+)',ListSeriesHandler),
 #   (r'/list/volume/(\w*-\w*)/*',ListVolumeHandler),
  #  (r'/list/part/(\w*-\w*)/*',ListPartHandler),
   # (r'/list/chapter/(\w*-\w*)/*',ListChapterHandler),
    #(r'/list/node/(\w*-\w*)/*',ListNodeHandler),