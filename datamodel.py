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
    bookname=db.StringProperty(required=True)
    author=db.StringProperty(required=True)
    

class CS_BookUser(db.Model):
    bookKey=db.StringProperty(required=True)
    userKey=db.StringProperty(required=True)
    purview=db.StringProperty(default="owner")

class CS_Series(db.Model):
    bookKey=db.StringProperty(required=True)
    seriesName=db.StringProperty(required=True)
    order=db.IntegerProperty(required=True)
    next=db.StringProperty(default='')
    previous=db.StringProperty(default='')
    other=db.StringProperty()

class CS_Volume(db.Model):
    SeriesKey=db.StringProperty(required=True)
    volumeName=db.StringProperty(required=True)
    order=db.IntegerProperty(required=True)
    next=db.StringProperty(default='')
    previous=db.StringProperty(default='')
    other=db.StringProperty()

class CS_Part(db.Model):
    volumeKey=db.StringProperty(required=True)
    partName=db.StringProperty(required=True)
    order=db.IntegerProperty(required=True)
    next=db.StringProperty(default='')
    previous=db.StringProperty(default='')
    other=db.StringProperty()

class CS_Chapter(db.Model):
    partKey=db.StringProperty(required=True)
    chapterName=db.StringProperty(required=True)
    order=db.IntegerProperty(required=True)
    next=db.StringProperty(default='')
    previous=db.StringProperty(default='')
    other=db.StringProperty()

class CS_Node(db.Model):
    chapterKey=db.StringProperty(required=True)
    nodeName=db.StringProperty(required=True)
    order=db.IntegerProperty(required=True)
    next=db.StringProperty(default='')
    previous=db.StringProperty(default='')
    other=db.StringProperty()

class CS_Paragraph(db.Model):
    nodeKey=db.StringProperty(required=True)
    order=db.IntegerProperty(required=True)
    next=db.StringProperty(default='')
    previous=db.StringProperty(default='')
    other=db.StringProperty()
    content=db.TextProperty()