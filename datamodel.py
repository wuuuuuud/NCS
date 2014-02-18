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
    secret=db.StringProperty(verbose_name=u"密钥",default='')
    socialNetwork=db.StringProperty();

class CS_Book(db.Model):
    name=db.StringProperty(required=True)
    metaInfo=db.StringProperty(default='')

    

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
    style=db.TextProperty()

class CS_Class(db.Model):
    parentKey=db.StringProperty(required=True)
    name=db.StringProperty(required=True)
    order=db.IntegerProperty(required=True)
    next=db.StringProperty(default='')
    previous=db.StringProperty(default='')
    other=db.StringProperty()
    bookKey=db.StringProperty(required=True)
    level=db.StringProperty(required=True)
    style=db.StringProperty(default='')
    metaInfo=db.StringProperty(default='')
    className=db.StringProperty(default='')

class CS_Temp(db.Model):
    data=db.TextProperty()

DataScheme = {}
DataScheme['Class'] = {
    'Sequence' : ['Book','Series','Volume','Part','Chapter','Node','Paragraph'],
    'Book' : {
        'level' : 1,
        'Chinese' : u'书籍'
    },
    'Series' : {
        'level' : 2,
        'Chinese' : u'系列'
    },
    'Volume' : {
        'level' : 3,
        'Chinese' : u'卷册'
    },
    'Part' : {
        'level' : 4,
        'Chinese' : u'部'
    },
    'Chapter' : {
        'level' : 5,
        'Chinese' : u'章'
    },
    'Node' : {
        'level' : 6,
        'Chinese' : u'节'
    },
    'Paragraph' : {
        'level' : 99,
        'Chinese' : u'段'
    }
}
