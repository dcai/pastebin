#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cgi
import datetime
import logging
import md5
import math
import os
import sys
import wsgiref.handlers
import webapp2

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api import datastore
from google.appengine.api import datastore_types
from google.appengine.ext.webapp import template

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.lexers import get_all_lexers
from pygments.formatters import HtmlFormatter
import chardet

VERIFY_CODE = '1984'

def sort_language(a,b):
    if a.has_key('score') and b.has_key('score'):
        if a['score'] == b['score']:
            return cmp(a['name'],b['name'])
        else:
            return -cmp(a['score'], b['score'])
    elif a.has_key('score') and not b.has_key('score'):
        return -1
    elif not a.has_key('score') and b.has_key('score'):
        return 1
    else:
        return cmp(a['name'].lower(),b['name'].lower())

def get_syntax():
    w = {'text':30,'java':20,'php':20,'html':20,'javascript':30}
    lexers = get_all_lexers()
    result = []
    for i in lexers:
        d={}
        d['name']=i[0]
        name = d['name'].lower()
        if w.has_key(name):
            d['score'] = w[name]
        d['syn']=i[1][0]
        result.append(d)
    result.sort(sort_language)
    return result

class Snippet(db.Model):
    author  = db.StringProperty()
    content = db.TextProperty()
    code    = db.TextProperty()
    date    = db.DateTimeProperty(auto_now_add=True)
    lang    = db.StringProperty()
    title   = db.StringProperty()

class MainPage(webapp2.RequestHandler):
    def get(self):
        lexers = get_syntax()
        tpl = {'lexers':lexers, 'candycode':VERIFY_CODE }
        path = os.path.join(os.path.dirname(__file__), 'views/home.html')
        self.response.out.write(template.render(path, tpl))
    def post(self):
        code = Snippet()
        candycode = self.request.get('candycode')
        if candycode == VERIFY_CODE:
            code.author  = self.request.get('author')
            code.title   = self.request.get('title')
            code.lang    = self.request.get('lang')
            code.content = self.request.get('content')
            code.code    = self.request.get('code')
            code.put()
            self.redirect('/'+str(code.key().id()))
        else:
            logging.error('Spamer attacked')
            self.redirect('/')

class ListSnippet(webapp2.RequestHandler):
    def get(self, page = 1):
        query = db.GqlQuery("SELECT * FROM Snippet order by date DESC")
        limit = 5
        total = query.count()
        pages = int(math.ceil(float(total)/float(limit)))
        list = query.fetch(limit, (int(page)-1)*limit)
        count = 2;
        for i in list:
            if count % 2:
                i.row = True
            count = count + 1
            i.ID = i.key().id()
        tpl = {"list":list, "pages": range(1, pages+1), "page":int(page)}
        path = os.path.join(os.path.dirname(__file__), 'views/list.html')
        self.response.out.write(template.render(path, tpl))

class ViewSnippet(webapp2.RequestHandler):
    def get(self, ID = ""):
        code = Snippet.get_by_id(int(ID))
        css   = HtmlFormatter().get_style_defs('.highlight')
        lexer = get_lexer_by_name(code.lang, stripall=True)
        formatter = HtmlFormatter(encoding='utf-8',nobackground=True)
        formatted = highlight(code.code, lexer, formatter)
        params = {
            'title'  : code.title,
            'author' : code.author,
            'content': code.content,
            'code'   : formatted,
            'plain'  : code.code,
            'date'   : code.date,
            'ID'     : ID,
            'css'    : css
        }
        logging.info(params)
        path = os.path.join(os.path.dirname(__file__), 'views/code.html')
        self.response.out.write(template.render(path, params))

class HandleSnippet(webapp2.RequestHandler):
    def get(self, ID, action):
        code = Snippet.get_by_id(int(ID))
        if action == 'raw':
            self.response.headers['Content-Type'] = 'text/plain; charset=utf-8'
            self.response.out.write(code.code)
        elif action == 'del':
            pass

    def post(self, ID, action):
        isnew   = False
        isvalid = True
        errors  = ''
        code = Snippet.get_by_id(int(ID))
        self.response.headers['Content-Type'] = 'text/plain; charset=utf-8'
        if not code:
            isnew = True
            code = Snippet()

        if self.request.get('file'):
            sourcecode = self.request.POST.get('file').file.read()
            encoding  = chardet.detect(sourcecode)
            code.code = unicode(sourcecode, encoding['encoding'])
        else:
            if isnew:
                isvalid = False
                errors += " => Where is your source code?\n"
        if self.request.get('author'):
            code.author = self.request.get('author')
        if self.request.get('title'):
            code.title  = self.request.get('title')
        if self.request.get('lang'):
            code.lang  = self.request.get('lang')
            lexers = get_syntax()
            verified = False
            for i in lexers:
                if code.lang == i['syn']:
                    verified = True
                    break
            if not verified :
                errors += " => Syntax type is invalid.\n"
                isvalid = False
        else:
            if isnew:
                errors += " => Syntax type must be specified.\n"
                isvalid = False
        if self.request.get('content'):
            code.content  = self.request.get('content')
        if isvalid:
            code.put()
            if isnew:
                self.response.out.write('New entry created.\n')
                self.response.out.write('Code ID: #'+str(code.key().id())+'\n')
            else:
                self.response.out.write('Code #'+str(ID)+' update succeed!\n')
        else:
            self.response.out.write('Invalid submitted data:\n')
            self.response.out.write(errors)

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/latest/', ListSnippet),
    ('/latest/(\d+)', ListSnippet),
    ('/(\d+)/(.+)', HandleSnippet),
    ('/(\d+)', ViewSnippet),
], debug=True)
