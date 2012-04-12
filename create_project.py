#!/usr/bin/env python
import subprocess, sys

def save(filename, content):
    f = open(filename, 'w')
    f.write(content)
    f.close()

def virtualenv():
    print '--- install virtualenv ---'
    subprocess.call(['virtualenv', '.env'])
    subprocess.call(['chown', '-R', 'web:web', './.env'])

def nginx(domain, folder):
    print '--- configure nginx ---'
    nginx_config = """
server {
    server_name .%(domain)s;

    error_log /var/log/nginx/%(domain)s-error.log warn;
    access_log /var/log/nginx/%(domain)s-access.log;

    location /admin_media {
        alias /web/%(folder)s/.env/lib/python2.6/site-packages/django/contrib/admin/media;
    }   

    location /media/ {
        root /web/%(folder)s;
    }   

    location / { 
        include uwsgi_params;
        uwsgi_pass unix:/web/run/%(folder)s.sock;
    }   
}

server {
    server_name www.%(domain)s;
    location / { 
        rewrite (.*) http://%(domain)s$1 permanent;
    }   
}
    """ % {'domain': domain, 'folder': folder}

    #save
    filename = '/etc/nginx/sites-available/%s' % domain
    save(filename, nginx_config)
    
    #link
    filename2 = '/etc/nginx/sites-enabled/%s' % domain
    subprocess.call(['ln', '-s', filename, filename2])

def uwsgi(domain, folder):
    print '--- config uwsgi ---'
    uwsgi_config = """
[uwsgi]
processes = 2
socket = /web/run/%(folder)s.sock
home = /web/%(folder)s/.env
module = app 
chmod-socket = 666 
master = true
touch-reload = /web/%(folder)s/app.py
chdir = /web/%(folder)s
uid = web 
gid = web 
reload-on-rss = 200 
limit-as = 256     
    """ % {'folder': folder}
    
    filename = '/web/etc/projects/%s.ini' % domain
    save(filename, uwsgi_config)

def app(folder):
    print '--- add app.py to project ---'
    app_config = """
# -*- coding: iso-8859-1 -*-

import sys, os
import django.core.handlers.wsgi

sys.path.insert(0, '/web/%(folder)s/')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

application = django.core.handlers.wsgi.WSGIHandler()
    """ % {'folder': folder}
     
    filename = '/web/%s/app.py' % folder
    save(filename, app_config)

instructions = """
    use inside project folder!
    syntax: create_project domain.ru
"""

if __name__ == '__main__':
    if len(sys.argv) >= 3:
        domain = sys.argv[1]
        folder = os.getcwd().split('/')[-1]

        virtualenv()
        nginx(domain, folder)
        uwsgi(domain, folder)
        app(folder)
    else:
        print instructions
