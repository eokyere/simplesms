#!/usr/bin/env python


from __future__ import with_statement

import functools
import os, sys, re, datetime
from fabric.api import *
from fabric.colors import red, green

# requirements: git

#default values
env.app_name = 'pact' 
env.datastore = '%(app_name)s.sqlite3' % env

def test():
    manage('test reminder')

def start():
    s = ''
    if not (env.port or env.host):
        dev()
    
    if env.port:
        if env.host:
            s = '%s:%s' % (env.host, env.port)
        else:
            s = env.port
    else:
        s = env.host
    manage('runserver %s' % s)

def route():
    manage('runrouter')
    
def deploy():
    manage('depoy')
    
def clear_reminders():
    manage('clear_reminders')    

def manage(cmd, capture=False):
    local('python manage.py %s' % cmd, capture=capture)
    

def clean():
    for cmd in ['find . -iname "*.pyc" -exec rm {} \;']:
        try:
            local(cmd)
        except: pass

def cleandb():    
    try:
        local('rm %(datastore)s' % env)
    except:
        pass

def dev(host='0.0.0.0', port='8000'):
    env.version = 'dev'
    env.host = host
    env.port = port

def stage():
    pass

def launch():
    # deploy
    # send necessary announcements and messages
    pass

# remote git repository management
def pull(parent='origin', branch='master'):
    "Updates the repository."
    run("cd ~/git/$(repo)/; git pull %(parent)s %(branch)s")

def reset():
    "Resets the repository to specified version."
    run("cd ~/git/$(repo)/; git reset --hard $(hash)")


