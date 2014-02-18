#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re

from google.appengine.ext import db

import datamodel
from datamodel import *
from toDict import to_dict



__keypattern=re.compile(r'(\w*-*[\w\-]*)')

def getSafeKey(_in):
        _re=__keypattern.match(_in).group()
        return _re


def checkPurview(pStr):
    if pStr.lower()=='owner' or pStr.lower()=='co-editor':
        return True
    return True

def getUser(handler):
    _userKey=handler.session.get("key")
    if _userKey and str(_userKey)!='':
        return str(_userKey)
    else:
        _secret=handler.request.get("secret")
        if _secret!='' and _secret:
            _user=db.Query(CS_User).filter('secret =',_secret).get()
            if _user:
                return str(_user.key())
    return ''


def getBookKey(_parentKey):
    try:
        _parent=db.get(_parentKey)
    except:
        return ''
    if to_dict(_parent).get('bookKey'):
        return _parent.bookKey
    else:
        return str(_parent.key())
