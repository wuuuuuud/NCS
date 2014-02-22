#!/usr/bin/env python
# -*- encoding: utf-8 -*-
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
import logging
import cgi
import datetime
import jinja2
import os
import re
import hashlib
import xml.dom.minidom

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api import background_thread
from google.appengine.api import taskqueue

import datamodel
import baseLib
from baseLib import *
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
                'model':[CS_Book,CS_Series,CS_Volume,CS_Part,CS_Chapter,CS_Node,CS_Paragraph],
                }
    @staticmethod
    def getModel(_cellName):
        _index=Utility.__celllist["english"].index(_cellName)
        return Utility.__celllist["model"][_index]
    @staticmethod
    def getElement(_cellName,_type):
        _index=Utility.__celllist['english'].index(_cellName)
        return Utility.__celllist[_type][_index]
        
    @staticmethod
    def getKey(_instance,_name):
        return Utility.getSafeKey(_instance.request.get(_name))
    @staticmethod
    def getPurview(_bookKey,_userKey,_dbName="CS_BookUser"):
        _q=db.GqlQuery("SELECT * FROM "+_dbName+" WHERE bookKey='"+_bookKey+"' AND userKey='"+_userKey+"'")
        #logging.info(str(_q))
        _purview=''
        try :
            _purview=_q.get().purview
        except :
            logging.info("fail to get purview string")
            pass
        logging.info("!"+_purview)
        return _purview

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

def navigateStringGenerator(_key):
    return


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
    #purview check
    _relation=db.GqlQuery("SELECT * FROM CS_BookUser WHERE userKey='"+_userkey+"' AND bookKey='"+_bookkey+"'").get()
    if (_relation):
        _purview=_relation.purview
    else:
        _purview=""

    if (_purview=="owner"):#purview check
        _handlerinstance.response.write('purview valid!')
        _counts=db.GqlQuery("SELECT __key__ FROM "+argv["cellname"]+" WHERE parentKey='"+_parentkey+"'").count()
        _handlerinstance.response.write("counts:"+str(_counts))
        if ((_insertafter==-1) or (_counts==0) or (_insertafter>=_counts)):#no insertafter assigned or originally no series or overflow insertafter position
            _previouskey=db.GqlQuery("SELECT __key__ FROM "+argv["cellname"]+" WHERE parentKey='"+_parentkey+"' AND order="+str(_counts)).get()
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
            _nextkey=db.GqlQuery("SELECT __key__ FROM "+argv["cellname"]+" WHERE parentKey='"+_parentkey+"' AND order="+str(_insertafter+1)).get()
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
        returnObject={
            'affair':'register new user',
            'success':False,
            'username':_username,
            'email':_email
        }
        assumeexist=db.GqlQuery("SELECT __key__ FROM CS_User WHERE username='"+_username+"'").get()
        if (not assumeexist):
            newuser=CS_User(username=_username,password=hashlib.md5(_password+config['PWMD5Salt']).hexdigest(),email=_email)
            newuser.put()
            newuser.secret=hashlib.md5(config['PWMD5Salt']+str(newuser.key())).hexdigest()
            newuser.put()
            returnObject.update(to_dict(newuser))
            returnObject['success']=True
            return self.response.write(json.encode(returnObject))
        else:
            returnObject['description']='username already exists!'
            return self.response.write(json.encode(returnObject))


class LoginHandler(BaseHandler):
    def post(self):
        _username = str(self.request.POST['username'])
        _password = self.request.POST['password']
        assumecorrect = db.GqlQuery("SELECT __key__ FROM CS_User WHERE username='"+_username+"'").get()
        
        returnObject = {}
        returnObject['success'] = False
        returnObject['affair'] = "Log in"
        if (assumecorrect):
            user=db.get(assumecorrect)
            if user.password==hashlib.md5(_password+config['PWMD5Salt']).hexdigest():#check password
                self.session["loggedin"]="yes"
                self.session["username"]=user.username
                self.session["key"]=str(assumecorrect)
                returnObject['success'] = True
                returnObject['username'] = user.username
                returnObject['secret'] = user.secret
                return self.response.write(json.encode(returnObject))
            else:#wrong password
                returnObject['description']="wrong password!"
                return self.response.write(json.encode(returnObject))
        else:
            returnObject['description']='wrong username!'
            return self.response.write(json.encode(returnObject))

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
        returnObject = {}
        returnObject["affair"]="Log out"
        returnObject["success"] = True
        self.response.write(json.encode(returnObject))


class AddParagraphHandler(BaseHandler):
    def post(self):
        _content=self.request.get('content')
        _parentKey=Utility.getSafeKey(self.request.get('parentkey'))
        _insertafter=self.request.get('insertafter')
        _bookKey=getBookKey(_parentKey)
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
        _bookKey=getBookKey(_parentKey)
        self.response.write(topNavigator(self,_parentKey))
        template_values={
                          'result':result,
                          'bookKey':_bookKey,
                          }
        template=jinja_environment.get_template('content.html')
        self.response.write(template.render(template_values))

class AddCommentHandler(BaseHandler):
    def post(self):
        _content=self.request.get('content')
        _userKey=getUser(self)
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
        returnObject=to_dict(_new)
        returnObject['username']=db.get(_userKey).username
        self.response.write(json.encode(returnObject))

class ListCommentHandler(BaseHandler):
    def post(self,_parentKey,_page=1):
        _paragraph=db.get(_parentKey)
        
        for _commentKey in _paragraph.comments:
            _comment=CS_Comment.get(_commentKey)
            _user=CS_User.get(_comment.userKey)
            _result.insert(0,to_dict(_comment))
            logging.WARNING("alive")
            logging.info(_user.username)
            logging.info(_result[0]['userKey'])
            _result[-1]['username']=_user.username;
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
        #store user info to reduce datebase reads
        _userDict={}
        for _pKey in _paragraphs:
            _p=CS_Paragraph.get(_pKey)
            _comments+=_p.comments
        _comments=set(_comments)
        for _cKey in _comments:
            _comment=CS_Comment.get(_cKey)
            _userKey = _comment.userKey
            if (_userDict.get(_userKey) == None):
                _user=CS_User.get(_comment.userKey)
                _username = _user.username
                _userDict[_userKey]=to_dict(_user)
            else:
                _username = _userDict[_userKey]['username']

            _result.insert(0,to_dict(_comment))
            _result[0]["username"]=_username
        self.response.write(json.encode(_result))

class UpdateParagraphHandler(BaseHandler):
    def post(self):
        _key=Utility.getSafeKey(self.request.get("key"))
        _bookKey=Utility.getSafeKey(self.request.get("bookKey"))
        _content=self.request.get("content")
        _userKey=getUser(self)
        _purview=Utility.getPurview(_bookKey, _userKey)
        #_purview=db.GqlQuery("SELECT * FROM CS_BookUser WHERE bookKey='"+_bookKey+"' AND userKey='"+_userKey+"'").get().purview
        #_purview=db.GqlQuery("SELECT * FROM CS_BookUser WHERE userKey='"+self.session.get("key")+"' AND bookKey='"+_bookKey+"'").get().purview
        logging.info(_content)
        logging.info(_userKey)
        logging.info(_bookKey)
        logging.info(self.request.body)
        if (checkPurview(_purview)):
            _paragraph=CS_Paragraph.get(_key)
            _paragraph.content=_content
            _paragraph.put()
            self.response.write(_content);

class DeleteCellHandler(BaseHandler):
    def post(self):
        _bookKey=Utility.getSafeKey(self.request.get("bookKey"))
        _key=Utility.getSafeKey(self.request.get("key"))
        _parentKey=Utility.getSafeKey(self.request.get("parentKey"))
        _userKey=self.session.get("key")
        _purview=Utility.getPurview(_bookKey,_userKey)
        _cellType=self.request.get("cellType")
        logging.info(_cellType)
        logging.info(_purview)
        if (_purview=="owner"):
            logging.info("purview valid!")
            _current=db.get(_key)
            if (_current.previous and _current.previous!=""):
                _previous=db.get(_current.previous)
                if(_current.next and _current.next!=""):
                    _previous.next=_current.next
                    _next=db.get(_current.next)
                    _next.previous=_current.previous
                    _next.put()
                    _previous.put()
                    _affected=db.GqlQuery("SELECT * FROM "+Utility.getElement(_cellType,u"tablename")+" WHERE parentKey='"+_current.parentKey+"' AND order > "+str(_current.order)).fetch(100000)
                    for _element in _affected:
                        _element.order-=1
                        _element.put()
                else:
                    _previous.next=""
                    _previous.put()
            else:
                if(_current.next and _current.next!=""):
                    _next=db.get(_current.next)
                    _next.previous=""
                    _next.put()
                    _affected=db.GqlQuery("SELECT * FROM "+Utility.getElement(_cellType,u"tablename")+" WHERE parentKey='"+_current.parentKey+"' AND order > "+str(_current.order)).fetch(100000)
                    for _element in _affected:
                        _element.order-=1
                        _element.put()
                else:
                    pass
            #cleanning child elements
            #too lazy to implement it
            _current.delete()


class UpdateCellHandler(BaseHandler):
    def post(self):
        _bookKey=Utility.getSafeKey(self.request.get("bookKey"))
        _key=Utility.getSafeKey(self.request.get("key"))
        _parentKey=Utility.getSafeKey(self.request.get("parentKey"))
        _userKey=self.session.get("key")
        _purview=Utility.getPurview(_bookKey,_userKey)
        _cellType=self.request.get("cellType")
        _newName=self.request.get("newName")
        logging.info(_cellType)
        logging.info(_purview)
        if (_purview=="owner"):
            logging.info("purivew valid!")
            _current=db.get(_key)
            _current.name=_newName
            _current.put()
            logging.info("update succeeded!")
            return self.response.write(_newName)
        else:
            logging.info("purview validation failed")

class ApiAddClassHandler(BaseHandler):
    """docstring for ApiAddClassHandler"""
    def post(self):
        #_bookKey=Utility.getSafeKey(self.request.get("bookKey"))
        _parentKey=Utility.getSafeKey(self.request.get("parentKey"))
        _userKey=getUser(self)
        logging.info(_userKey)
        
        _className=self.request.get("className").lower()
        _name=self.request.get("name")
        returnObject={
            'affair':'Add Class Content',
            'success':False,
            'className':_className,
            'description':''
        }

        _bookKey=getBookKey(_parentKey)
        _purview=Utility.getPurview(_bookKey,_userKey).lower()
        _newClass=None
        if (not checkPurview(_purview)) and _className!='book':
            returnObject['description']='invalid purview string!'
            return self.response.write(json.encode(returnObject))
        if _className=='book':
            if _userKey=='' or db.get(_userKey)==None:
                returnObject['description']='no user with provided info!'
                return self.response.write(json.encode(returnObject))
            _author=self.request.get("author")
            metaInfo={
                'author':_author,
                'addTime':str(datetime.datetime.now()),
                'modifyTime':str(datetime.datetime.now())
            }
            _newClass=CS_Book(name=_name,metaInfo=json.encode(metaInfo))
            _newClass.put()
            _newRelation=CS_BookUser(bookKey=str(_newClass.key()),userKey=str(_userKey),purview='owner')
            _newRelation.put()
            returnObject['success']=True
            
        else:
            _order=Utility.getSafeInt(self.request.get("order")) #A.K.A. insert before
            returnObject['description']+='classname not book\\r\\npurview valid\\r\\n'
            _count=db.Query(CS_Class).filter('parentKey =',_parentKey).count(65535)#number of existed element under the same parent key
            if _order<1:#must larger than 1, of course
                _order=_count+1
            metaInfo={
                'addTime':str(datetime.datetime.now()),
                'modifyTime':str(datetime.datetime.now())
            }
            _level=str(DataScheme['Class'][_className.title()]['level'])
            if _order>_count:
                _newClass=CS_Class(name=_name,
                    order=_count+1,
                    parentKey=_parentKey,
                    bookKey=_bookKey,
                    level=_level,
                    metaInfo=json.encode(metaInfo),
                    className=_className
                    )
                _newClass.put()
                if _count>0:
                    _prevClass=db.Query(CS_Class).filter('parentKey =',_parentKey).filter('order =',_count).get()
                    _prevClass.next=str(_newClass.key())
                    _prevClass.put()
                    _newClass.previous=str(_prevClass.key())
                    _newClass.put()
                returnObject['success']=True
            else:
                _newClass=CS_Class(name=_name,
                    order=0,
                    parentKey=_parentKey,
                    bookKey=_bookKey,
                    level=_level,
                    metaInfo=json.encode(metaInfo),
                    className=_className
                    )
                _newClass.put()
                _affected=db.Query(CS_Class).filter('parentKey =',_parentKey).filter('order >=',_order).fetch(10000000)
                for _instance in _affected:
                    _instance.order=_instance.order+1
                    if (_instance.order==_order+1):
                        _instance.previous=str(_newClass.key())
                        _newClass.next=str(_instance.key())
                    _instance.put()
                _newClass.order=_order

                if (_count>0 and _order>1):
                    _prevClass=db.Query(CS_Class).filter('parentKey =',_parentKey).filter('order =',_order-1).get()
                    _prevClass.next=str(_newClass.key())
                    _prevClass.put()
                    _newClass.previous=str(_prevClass.key())
                _newClass.put()
                returnObject['success']=True
        returnObject['self']=(to_dict(_newClass))
        returnObject['self']['key']=str(_newClass.key())
        return self.response.write(json.encode(returnObject))
                

class ApiGetClassHandler(BaseHandler):
    def get(self):
        return self.post()
    def post(self):
        return self.response.write(json.encode(getClass(self)))

def getClass(_handler):
    _key=Utility.getSafeKey(_handler.request.get("key"))
    returnObject={
        'affair':'get class',
        'className':'root',
        'data':[],
        'success':True
    }
    if _key == '':
        _result=db.Query(CS_Book).order('name').fetch(100)
        _count=_result.count(-1)
        for _instance in _result:
            returnObject['data'].insert(0,to_dict(_instance))
            returnObject['data'][0]['key']=str(_instance.key())
        return returnObject
    else:
        _result=None
        try:
            _result=CS_Class.get(_key)
            returnObject['className']=_result.className
        except:
            _result=CS_Book.get(_key)
            if _result==None:
                returnObject['success']=False
                returnObject['description']='no such key!'
                return returnObject
            else:
                returnObject['className']='book'
        returnObject['self']=to_dict(_result)
        returnObject['self']['key']=str(_result.key())
        _result=db.Query(CS_Class).filter('parentKey =',str(_result.key())).order('-order').fetch(100)
        for _instance in _result:
            returnObject['data'].insert(0,to_dict(_instance))
            returnObject['data'][0]['key']=str(_instance.key())
        return returnObject

class SitePageHandler(BaseHandler):
    def get(self):
        return self.post()
    def post(self):
        returnObject=getClass(self)
        _templateValue={
            'data':json.encode(returnObject),
        }
        _user=getUser(self)
        if _user!='':
            _templateValue['user']=json.encode(to_dict(CS_User.get(_user)))
            _templateValue['username']=CS_User.get(_user).username
        else:
            pass
        _page=jinja_environment.get_template('header.html').render()
        _page+=jinja_environment.get_template('title.html').render()
        _page+=jinja_environment.get_template('banner.html').render(_templateValue)
        _page+=jinja_environment.get_template('newList.html').render(_templateValue)
        _page+=jinja_environment.get_template('fullScreenWrapper.html').render(_templateValue)
        _page+=jinja_environment.get_template('toolButtonWrapper.html').render(_templateValue)
        return self.response.write(_page)


class ApiUpdateClassHandler(BaseHandler):
    def post(self):
        _key=Utility.getSafeKey(self.request.get("key"))
        _author=self.request.get('author')
        _userKey=getUser(self)
        logging.info('the user key is '+_userKey)
        _name=self.request.get("name")
        returnObject={
            'affair':'Update Class Content',
            'success':False,
            'className':'',
            'description':''
        }
        #necessary parameters checking
        if _key=='':
            returnObject['description']='missing parameter:key'
            return self.response.write(json.encode(returnObject))
        
        #determine class name and book key
        _updatee=db.get(_key)
        _className=''
        _bookKey=''
        if not _updatee.get(className):
            _className='book'
            _bookKey=str(_updatee.key())
        else:
            _className=_updatee.className
            _bookKey=_updatee.bookKey
        returnObject['className']=_className

        #get purview string
        _purview=Utility.getPurview(_bookKey,_userKey).lower()

        #purview checking
        if not checkPurview(_purview):
            returnObject['description']='invalid purview, please make sure you are the owner or the co-editor of the book'
            return self.response.write(json.encode(returnObject))
        
        ##main code

        #extract meta info
        _metaInfo=json.decode(_updatee.metaInfo)

        #modify object
        if _className.lower()=='book':
            if _name:
                _updatee.name=_name
                _metaInfo.modifyTime=str(datetime.datetime.now())
            if _author:
                _metaInfo.author=_author
                _metaInfo.modifyTime=str(datetime.datetime.now())
            updatee.metaInfo=json.encode(_metaInfo)
            _updatee.put()
        else:
            if _name:
                _updatee.name=_name
                _metaInfo.modifyTime=str(datetime.datetime.now())
            updatee.metaInfo=json.encode(_metaInfo)
            _updatee.put()
        returnObject['success']=True
        returnObject.update(to_dict(_updatee))
        returnObject['key']=_key
        return self.response.write(json.encode(returnObject))

class ApiDeleteClassHandler(BaseHandler):
    def post(self):
        _key=Utility.getSafeKey(self.request.get("key"))
        _isRecursively=self.request.get("isRecursively")
        _userKey=getUser(self)
        logging.info('the user key is '+_userKey)
        returnObject={
            'affair':'Delete Class',
            'success':False,
            'className':'',
            'description':''
        }
        _deleteList=[]
        _deleteList.append(_key)
        #necessary parameters checking
        if _key=='':
            returnObject['description']='missing parameter:key'
            return self.response.write(json.encode(returnObject))
        
        #determine class name and book key
        _deletee=db.get(_key)

        #checking if the key provided is valid
        if not _deletee:
            returnObject['description']='incorrect key!'
            return self.response.write(json.encode(returnObject))
        _className=''
        _bookKey=''
        if not to_dict(_deletee).get("className"):
            _className='book'
            _bookKey=str(_deletee.key())
        else:
            _className=_deletee.className.lower()
            _bookKey=_deletee.bookKey
        returnObject['className']=_className

        #get purview string
        _purview=Utility.getPurview(_bookKey,_userKey).lower()

        #purview checking
        if not checkPurview(_purview):
            returnObject['description']='invalid purview, please make sure you are the owner or the co-editor of the book'
            return self.response.write(json.encode(returnObject))
        
        ##main code
        if _isRecursively and str(_isRecursively).lower()=='true':
            returnObject['isRecursively']=True
            _i=0
            _paragraphList=[]
            while _i < len(_deleteList):
                _directChildren=db.Query(CS_Class).filter('parentKey =',_deleteList[_i]).fetch(65535)
                for _child in _directChildren:
                    _deleteList.append(str(_child.key()))
                __directParagraph=db.Query(CS_Class).filter('parentKey =',_deleteList[_i]).fetch(65535)
                for _child in __directParagraph:
                    _paragraphList.append(str(_child.key()))
                _i+=1
            _deleteList.extend(_paragraphList)
            for _each in _deleteList[1:]:
                _child=db.get(_each)
                if _child:
                    _child.delete()


        if _className=='book':
            #delete related entries in the bookuser diagram
            _purviews=db.Query(CS_BookUser).filter('bookKey =',_key).fetch(65535)
            for _each in _purviews:
                _each.delete()
            #delete the entry
            _deletee.delete()
        else:
            #repair linkage
            if hasattr(_deletee,'previous') and _deletee.previous!='' and db.get(_deletee.previous):
                logging.info("deleting.book-.previous+.")
                _previous=db.get(_deletee.previous)
                if hasattr(_deletee,'next') and _deletee.next!='' and db.get(_deletee.next):
                    logging.info('next+')
                    _next=db.get(_deletee.next)
                    _previous.next=_deletee.next
                    _previous.put()
                    _next.previous=''
                    _next.previous=str(_deletee.previous)
                    logging.info(str(_next.put()))
                    _next.put()
                    logging.info(_next.previous)
                else:
                    logging.info('next-')
                    _previous.next=''
                    _previous.put()
            elif hasattr(_deletee,'next') and _deletee.next!='' and db.get(_deletee.next):
                logging.info('deleting,previous-,next+')
                _next=db.get(_deletee.next)
                _next.previous=''
                _next.put()
                _next.put()
            #update affected entries
            _affected=db.Query(CS_Class).filter('parentKey =',_deletee.parentKey).filter('order >', _deletee.order).fetch(65535)
            for _each in _affected:
                _each.order-=1
                _each.put()
            #delete the entry
            _deletee.delete()
        returnObject['success']=True
        return self.response.write(json.encode(returnObject))

class SiteParagraphHandler(BaseHandler):
    def get(self):
        _parentKey=Utility.getSafeKey(self.request.get('parentKey'))
        _bookKey=getBookKey(_parentKey)
        result=db.GqlQuery("SELECT * FROM CS_Paragraph WHERE parentKey='"+_parentKey+"' ORDER BY order ASC").fetch(100000)
        _node=CS_Class.get(_parentKey)
        _templateValue={
                          'result':result,
                          'bookKey':_bookKey,
                          'node':json.encode(to_dict(_node)),
                          }
        _user=getUser(self)
        if _user!='':
            _templateValue['user']=json.encode(to_dict(CS_User.get(_user)))
            _templateValue['username']=CS_User.get(_user).username
        else:
            pass
        _page=jinja_environment.get_template('header.html').render()
        _page+=jinja_environment.get_template('title.html').render()
        _page+=jinja_environment.get_template('banner.html').render(_templateValue)
        _page+=jinja_environment.get_template('newContent.html').render(_templateValue)
        _page+=jinja_environment.get_template('fullScreenWrapper.html').render(_templateValue)
        _page+=jinja_environment.get_template('toolButtonWrapper.html').render(_templateValue)

        return self.response.write(_page)      

class UploadPartHandler(BaseHandler):
    def post(self):
        _str=self.request.get("data")
        _parentKey=Utility.getSafeKey(self.request.get("parentKey"))
        _bookKey=getBookKey(_parentKey)
        _userKey=getUser(self)
        _temp=CS_Temp(data=_str).put()
        taskqueue.add(url='/background/upload/part/',
            params={
            "dataKey":str(_temp),
            "parentKey":_parentKey,
            "userKey":_userKey
            },
            target='1.DBWorker')
        return self.response.write("1")


class BackgroundUploadPartHandler(BaseHandler):
    def post(self):
        _dataKey=self.request.get("dataKey")
        _str=db.get(_dataKey).data
        _parentKey=Utility.getSafeKey(self.request.get("parentKey"))
        _bookKey=getBookKey(_parentKey)
        _userKey=self.request.get("_userKey")
        _purview=Utility.getPurview(_bookKey, _userKey)
        if(checkPurview(_purview)):
            _s={}
            _currentChapterO=0
            _q=db.GqlQuery("SELECT * FROM CS_Class WHERE className='chapter' AND parentKey='"+_parentKey+"' ORDER BY order DESC LIMIT 1")
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
                        _new=CS_Class(order=_currentChapterO+1,
                        parentKey=_parentKey,
                        name=result.group(2),
                        previous="",
                        bookKey=_bookKey,
                        className="chapter",
                        level=str(DataScheme['Class']['Chapter']['level']))
                        _new.put()
                    else:
                        _new=CS_Class(order=_currentChapterO+1,
                            parentKey=_parentKey,
                            name=result.group(2),
                            previous=str(_s.get('currentC').key()),
                            bookKey=_bookKey,
                            className="chapter",
                            level=str(DataScheme['Class']['Chapter']['level']))
                        _new.put()
                        _s.get('currentC').next=str(_new.key())
                        _s.get('currentC').put()
                    _currentChapterO+=1
                    _currentNodeO=0
                    _currentParagraphO=0
                    
                    _s['currentC']=_new
                elif (result.group(1)=="node"):
                    if (_currentNodeO==0):
                        _new=CS_Class(order=_currentNodeO+1,\
                            parentKey=str(_s.get('currentC').key()),\
                            name=result.group(2),\
                            previous="",\
                            bookKey=_bookKey,
                            className="node",
                            level=str(DataScheme['Class']['Node']['level']))
                        _new.put()
                        
                    else:
                        _new=CS_Class(order=_currentNodeO+1,
                            parentKey=str(_s.get('currentC').key()),
                            name=result.group(2),
                            previous=str(_s.get('currentN').key()),
                            bookKey=_bookKey,
                            className="node",
                            level=str(DataScheme['Class']['Node']['level']))
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


                          
config = {}
config['webapp2_extras.sessions'] = {
    'secret_key': 'CounterTop',  
}
config['PWMD5Salt']='StoneforgeSword'

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)+"/template"))# jinja2 config,set dir

app = webapp2.WSGIApplication([
    ('/reset' , ResetDataStoreHandler), 
    (r'/add/book/*',AddBookHandler),
    (r'/list/((?:series)|(?:volume)|(?:part)|(?:chapter)|(?:node))/(\w*-*[\w\-]*)/?([0-9]*)',ListCellHandler),
    (r'/list/book/*',ListBookHandler),
    (r'/list/paragraph/(\w*-*[\w\-]*)/?([0-9]*)',ListParagraphHandler),
    (r'/list/comment/(\w+-*[\w\-]+)/?',ListCommentHandler),
    (r'/add/series/*',AddSeriesHandler),
    (r'/add/volume/*',AddVolumeHandler),
    (r'/add/part/*',AddPartHandler),
    (r'/add/chapter/*',AddChapterHandler),
    (r'/add/node/*',AddNodeHandler),
    (r'/add/paragraph/*',AddParagraphHandler),
    (r'/add/comment/*',AddCommentHandler),
    (r'/manage/add/*',AddMultiplyChapterAndNodeAndParagraphHandler),
    (r'/get/comments/*',ApiGetMultiplyCommentHandler),
    (r'/get/multiply/comment/*',ApiGetMultiplyCommentHandler),
    (r'/update/paragraph/*',UpdateParagraphHandler),
    (r'/delete/cell/*',DeleteCellHandler),
    (r'/update/cell/*',UpdateCellHandler),
    (r'/register/user/*',RegisterUserHandler),
    (r'/logout/user/*',LogoutHandler),
    (r'/login/user/*',LoginHandler),
    (r'/check/login/*',LoginTestHandler),
    (r'/get/class/*',ApiGetClassHandler),#api handler for volumes,chapters,parts,etc
    (r'/add/class/*',ApiAddClassHandler),
    (r'/delete/class/*',ApiDeleteClassHandler),
    (r'/update/class/*',ApiUpdateClassHandler),
    (r'/page/*',SitePageHandler),
    (r'/upload/part/*',UploadPartHandler),
    (r'/background/upload/part/*',BackgroundUploadPartHandler),
    (r'/paragraph/*',SiteParagraphHandler),
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
