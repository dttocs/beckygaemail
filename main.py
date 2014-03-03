#!/usr/bin/env python
#
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
from google.appengine.ext import ndb
from google.appengine.api import users
from google.appengine.ext.webapp import template
from google.appengine.api import mail
from google.appengine.api import namespace_manager


import logging
import json
import datetime
import os
import pprint


class CompletionStatus(ndb.Model):
  first_name = ndb.StringProperty()
  last_name  = ndb.StringProperty()
  email      = ndb.StringProperty()
  completion = ndb.BooleanProperty()
  date       = ndb.DateTimeProperty(auto_now_add=True)
  content    = ndb.StringProperty(indexed=False)

class TestResult(ndb.Model):
  date    = ndb.DateTimeProperty(auto_now_add=True)
  content = ndb.StringProperty(indexed=False)
  
# ConfigDB
class ConfigDB(ndb.Model):
  admin_email = ndb.StringProperty()
  alert_email = ndb.StringProperty()
  send_mail   = ndb.BooleanProperty()
 
# list of valid courses
class CourseDB(ndb.Model):
  course = ndb.StringProperty()
  
  
# send mail
def sendmail(completion):
  query = ConfigDB.query()
  if query.get() != None:
    if query.get().send_mail:
      if completion.completion:
        complete = "completed"
        state = "Complete"
      else:
        complete = "FAILED TO COMPLETE"
        state = "Incomplete"
        
      mail_sub = "Training %s for %s %s" % (state, completion.first_name,completion.last_name)
      mail_body = \
"""
As of %s, %s %s (%s) has %s training.

%s
""" % (datetime.datetime.strftime(datetime.datetime.now(),"%+"),
       completion.first_name,completion.last_name, completion.email, complete, completion.content)

      logging.info('Sending email: subject %s body %s', mail_sub, mail_body)
      mail.send_mail(sender = query.get().admin_email,
              to = query.get().alert_email,
              subject = 'Server status change notification: %s' % mail_sub,
              body = mail_body)


# CompletionHandler
class CompletionHandler(webapp2.RequestHandler):
  def post(self):
    logging.debug('received POST to /complete')

    completion = CompletionStatus()

    data = self.request.body
    try:
      post = json.loads(data)
    except ValueError, e:
      logging.error("ValueError %s decoding %s",e,data)

    completion.first_name = post["first_name"]
    completion.last_name = post["last_name"]
    completion.email = post["email"]
    if post["completion"] == "Y":
      completion.completion = True
    else:
      completion.completion = False
    if "content" in post.keys():
      completion.content = post["content"]
    else:
      completion.content = None

    try:
      completion.put()
    except e:
      logging.error('There was an error saving completion %s: %s', data, e)

    sendmail(completion)
    logging.debug('Finish POST to /complete')
    self.redirect('/')

  def options(self):      
      self.response.headers['Access-Control-Allow-Origin'] = '*'
      self.response.headers['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept'
      self.response.headers['Access-Control-Allow-Methods'] = 'POST, GET, PUT, DELETE'

class ResultsHandler(webapp2.RequestHandler):
  def post(self):
    logging.debug('received POST to /testresults')

    results = TestResult()

    logging.error("params '%s'", self.request.arguments())
    r = self.request.body
    logging.error("results '%s'",r)
    results.content = r

    try:
      results.put()
    except e:
      logging.error('There was an error saving results %s: %s', data, e)

    logging.debug('Finish POST to /testresults')
    self.redirect('/')

  def options(self):      
      self.response.headers['Access-Control-Allow-Origin'] = '*'
      self.response.headers['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept'
      self.response.headers['Access-Control-Allow-Methods'] = 'POST, GET, PUT, DELETE'
    
class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.response.headers.add_header('Access-Control-Allow-Origin', '*')
        self.response.write('Hello world!')

    def options(self):      
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        self.response.headers['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept'
        self.response.headers['Access-Control-Allow-Methods'] = 'POST, GET, PUT, DELETE'
        
class ExportHandler(webapp2.RequestHandler):
  def get(self):
    self.response.out.write(self.export())
  
  def export(self):
    self.response.headers['Content-Type'] = 'text/csv'
    type = self.request.get('type')
    if type == 'complete':
      text = type
    elif type == 'test':
      results_query = TestResult.query()
      results = results_query.fetch()
      text = ''
      for r in results_query.iter():
        try:
          content = json.loads(r.content)
#          text += str(r.content) + '\n' + str(pprint.pformat(json.loads(r.content))) + '\n'
          text += content['email']+ ',' + \
                 ','.join(map(str,content['Pre'])) + ',' + \
                 ','.join(map(str,content['Post'])) + '\n'
        except Exception, e:
          text += str(e) + '\n'
    else: 
      text = "Unknown export type %s" % type
    return text
    
#AdminHandler
class AdminHandler(webapp2.RequestHandler):
  def post(self):
    action = self.request.get('action')
    result = None
    if action == 'addurl2':
      if self.request.get('url').startswith('http://'):
        urlDB = UrlDB()
        urlDB.url = self.request.get('url').strip()
        urlDB.put()
        result = 'url added'
      else:
        result = 'url must start with http://'
    if action == 'addcronurl2':
      if self.request.get('url').startswith('http://'):
        cronUrlDB = CronUrlDB3()
        cronUrlDB.url = self.request.get('url').strip()
        cronUrlDB.alias = self.request.get('alias').strip()
        if len(cronUrlDB.alias) == 0: 
          cronUrlDB.alias = cronUrlDB.url
        cronUrlDB.checkvalue = self.request.get('checkvalue').strip()
        cronUrlDB.counter = 0 # just defined!
        cronUrlDB.n_errors = 0
        cronUrlDB.n_retrys = 0
        cronUrlDB.status = 0 # undef
        cronUrlDB.put()
        result = 'cron url added'
      else:
        result = 'url must start with http://'
    if action == 'edit.email':
      if self.request.get('admin.email').find('@') != -1:
        if self.request.get('alert.email').find('@') != -1:
          query = ConfigDB.query()
          if query.get() == None: # singleton
            configDB = ConfigDB()
          else:
            configDB = query.get()
          configDB.admin_email = self.request.get('admin.email')
          configDB.alert_email = self.request.get('alert.email')
          configDB.send_mail = (self.request.get('send.email') == 'True')
          configDB.put()
          result = 'email values saved in configuration'
        else:
          result = 'alert email must contain @'
      else:
        result = 'admin email must contain @'
    self.render_admin(action, result, None)

  def get(self):
    action = self.request.get('action')
    result = None
    if action == 'delete':
      mykey = self.request.get('key')
    else:
      mykey = None
    if action == 'delete2':
      mykey = self.request.get('key')
      entity = db.get(mykey)
      if entity:
        entity.delete()
        result = 'entity deleted'
      else:
        result = 'nothing to delete'
    self.render_admin(action, result, mykey)

  # render_admin
  def render_admin(self, action, result, mykey):
      query = ConfigDB.query()
      if query.get() != None:
        admin_email = query.get().admin_email
        alert_email = query.get().alert_email
        send_mail = query.get().send_mail
      else:
        admin_email = ''
        alert_email = ''
        send_mail = ''
      template_values = {
        'style': style,
        'header': header(self),
        'footer': footer(self),
        'action': action,
        'result': result,
        'mykey': mykey,
#        'urlDBs': UrlDB.all(),
        'admin_email': admin_email,
        'alert_email': alert_email,
        'send_mail': send_mail,
      }
      printHtml(self, 'admin.html', template_values)        

# style used in html templates
style = u'''
<style type="text/css">
<!--
body       { background-color: #FFFFEE; color: #000000; font-family: Arial }
td.header  { background-color: #F0F000;}
.small       { font-size: 8pt; font-style: normal; font-family: Arial, Helvetica; }
table { background-color:#FFFFFF; border-width:3px; border-style:solid; border-color:#006699; }
td    { background-color: #DEE3E7; }
th    { background-color: #C8D1D7; }
table.menu { background-color:#FFFFFF; border-width:0px; }
-->
</style>
'''

# header
def header(self):
    return "".join(('''<table class="menu" width="100%" cellpadding="0" cellspacing="0"><tr><td align="left">
      <a href="view">View statistics</a> | <a href="checkurl">Dashboard</a> | <a href="admin">Admin</a></td>''',
      '<td align="right">%s [%s]</td>' % (users.get_current_user(), datetime.datetime.now().strftime("%d %b %y, %H:%M:%S")),
      '</tr></table>'
    ))

# footer
def footer(self):
    return '<div align="center" style="font-size: smaller">Powered by <a title="cron-tab@googlecode" href="http://code.google.com/p/cron-tab/">cron-tab</a></div>'

#printHtml
def printHtml(self, template_name, template_values={}):
  path = os.path.join(os.path.dirname(__file__), os.path.join('templates', template_name))
  self.response.out.write(template.render(path, template_values))


logging.getLogger().setLevel(logging.DEBUG)

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/complete', CompletionHandler),
    ('/testresults', ResultsHandler),
    ('/admin', AdminHandler),
    ('/export', ExportHandler)
    
], debug=True)
