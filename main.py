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
from webapp2_extras import sessions

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
import uuid

def sort_language(a,b):
    if a.has_key('score') and b.has_key('score'):
        if a['score'] == b['score']:
            return cmp(a['name'],b['name'])
        else:
            return -cmp(a['score'], b['score'])
    else:
        return cmp(a['name'].lower(),b['name'].lower())

def get_syntax():
    w = {'text':40,'java':20,'php':20,'html':20,'js':30}
    lexers = get_all_lexers()
    result = []
    for i in lexers:
        d={'name':i[0], 'syn':i[1][0], 'score':0}
        name = d['syn'].lower()
        if name in w:
            d['score'] = w[name]
        result.append(d)
    result.sort(sort_language)
    return result

def get_verify_code():
    return str(uuid.uuid4().get_hex().upper()[0:6]).strip().lower()

class Snippet(db.Model):
    author  = db.StringProperty()
    content = db.TextProperty()
    code    = db.TextProperty()
    date    = db.DateTimeProperty(auto_now_add=True)
    lang    = db.StringProperty()
    title   = db.StringProperty()

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

class MainPage(BaseHandler):
    def get(self):
        code = get_verify_code()
        self.session['verifycode'] = code
        lexers = get_syntax()
        tpl = {'lexers':lexers, 'candycode':code, 'ID': 0 }
        path = os.path.join(os.path.dirname(__file__), 'template/home.html')
        self.response.out.write(template.render(path, tpl))
    def post(self):
        code = Snippet()
        candycode = self.request.get('candycode').strip()
        if candycode == self.session.get('verifycode'):
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

class ListSnippet(BaseHandler):
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
        tpl = {"list":list, "pages": range(1, pages+1), "page":int(page), "ID":0}
        path = os.path.join(os.path.dirname(__file__), 'template/list.html')
        self.response.out.write(template.render(path, tpl))

class ViewSnippet(BaseHandler):
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
        path = os.path.join(os.path.dirname(__file__), 'template/code.html')
        self.response.out.write(template.render(path, params))

class HandleSnippet(BaseHandler):
    def get(self, ID, action):
        code = Snippet.get_by_id(int(ID))
        if action == 'raw':
            self.response.headers['Content-Type'] = 'text/plain; charset=utf-8'
            self.response.out.write(code.code)
        elif action == 'rm':
            code = Snippet.get_by_id(int(ID))
            code.delete()
            self.redirect('/')

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

config = {}
config['webapp2_extras.sessions'] = {'secret_key': ''}

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/latest/', ListSnippet),
    ('/latest/(\d+)', ListSnippet),
    ('/(\d+)/(.+)', HandleSnippet),
    ('/(\d+)', ViewSnippet),
], config=config)
