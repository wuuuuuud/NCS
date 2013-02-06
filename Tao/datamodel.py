#!/use/bin/env python
#-*- coding:utf-8 -*-

import cgi
import datetime
import webapp2

from google.appengine.ext import db
from google.appengine.api import users

class CS_User(db.Model):
    username=db.StringProperty(verbose_name=u"用户名",required=True)
    password=db.StringProperty(verbose_name=u"密码",required=True)
    email=db.EmailProperty(verbose_name=u"邮箱地址",required=True)
    socialNetwork=db.StringProperty();

class CS_Book(db.Model):
    name=db.StringProperty(required=True)
    author=db.StringProperty(required=True)

    

class CS_BookUser(db.Model):
    bookKey=db.StringProperty(required=True)
    userKey=db.StringProperty(required=True)
    purview=db.StringProperty(default="owner")

class CS_Series(db.Model):
    parentKey=db.StringProperty(required=True)
    name=db.StringProperty(required=True)
    order=db.IntegerProperty(required=True)
    next=db.StringProperty(default='')
    previous=db.StringProperty(default='')
    other=db.StringProperty()
    bookKey=db.StringProperty(required=True)
    

class CS_Volume(db.Model):
    parentKey=db.StringProperty(required=True)
    name=db.StringProperty(required=True)
    order=db.IntegerProperty(required=True)
    next=db.StringProperty(default='')
    previous=db.StringProperty(default='')
    other=db.StringProperty()
    bookKey=db.StringProperty(required=True)

class CS_Part(db.Model):
    parentKey=db.StringProperty(required=True)
    name=db.StringProperty(required=True)
    order=db.IntegerProperty(required=True)
    next=db.StringProperty(default='')
    previous=db.StringProperty(default='')
    other=db.StringProperty()
    bookKey=db.StringProperty(required=True)


class CS_Chapter(db.Model):
    parentKey=db.StringProperty(required=True)
    name=db.StringProperty(required=True)
    order=db.IntegerProperty(required=True)
    next=db.StringProperty(default='')
    previous=db.StringProperty(default='')
    other=db.StringProperty()
    bookKey=db.StringProperty(required=True)

class CS_Node(db.Model):
    parentKey=db.StringProperty(required=True)
    name=db.StringProperty(required=True)
    order=db.IntegerProperty(required=True)
    next=db.StringProperty(default='')
    previous=db.StringProperty(default='')
    other=db.StringProperty()
    bookKey=db.StringProperty(required=True)

class CS_Paragraph(db.Model):
    parentKey=db.StringProperty(required=True)
    order=db.IntegerProperty(required=True)
    next=db.StringProperty(default='')
    previous=db.StringProperty(default='')
    other=db.StringProperty()
    content=db.TextProperty()
    comments=db.ListProperty(str,default=[])
    
class CS_Comment(db.Model):
    userKey=db.StringProperty(required=True)
    relatedNodes=db.ListProperty(str)
    firstNode=db.StringProperty()
    lastNode=db.StringProperty()
    content=db.TextProperty()
    time=db.DateTimeProperty(auto_now_add=True)
    startOffset=db.IntegerProperty(required=True)
    endOffset=db.IntegerProperty(required=True)
    other=db.TextProperty()