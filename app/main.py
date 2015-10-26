import newrelic.agent
newrelic.agent.initialize()


from os import path
from raven.contrib.tornado import AsyncSentryClient

import torndb
import tornado.ioloop
import tornado.locale
import tornado.web
import tornado.httpserver
import tornado.options

import os
import yaml
import logging
import string
import datetime, time


from main.helper import *
from main.db import *


# global variables (and list of all used environment variables)
APP_VERSION        = os.getenv('VERSION', tornado.version)
APP_DEBUG          = os.getenv('DEBUG', 'false')
APP_PORT           = os.getenv('PORT', 3000)
APP_AUTH_URL       = os.getenv('AUTH_URL', 'https://auth.entu.ee')
APP_MONGODB        = os.getenv('MONGODB', 'mongodb://localhost:27017/')
APP_MYSQL_HOST     = os.getenv('MYSQL_HOST', 'localhost')
APP_MYSQL_DATABASE = os.getenv('MYSQL_DATABASE')
APP_MYSQL_USER     = os.getenv('MYSQL_USER')
APP_MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
APP_CUSTOMERGROUP  = os.getenv('CUSTOMERGROUP')
APP_SECRET         = os.getenv('SECRET', 'ABC123')
APP_SENTRY         = os.getenv('SENTRY_DSN')


# List of controllers to load.
app_controllers = [
    'api.api',
    'api.api2',
    'api.erply',
    'api.websocket',
    'entity.csv_import',
    'entity.entity',
    'importers.cmdi',
    'library.ester',
    'library.photo',
    'main.config',
    'main.status',
    'public.public',
    'update.update',
    'user.auth',
    'user.user',
]


class MainPage(myRequestHandler):
    """
    Redirects / to site's default path.

    """
    def get(self):
        self.redirect(self.app_settings('path'))


class PageNotFound(myRequestHandler):
    """
    """
    def get(self, page=None):
        self.missing()


class myApplication(tornado.web.Application):
    """
    Main Application handler. Imports controllers, settings, translations.

    """
    def __init__(self):
        # load settings
        settings = {
            'port':                 APP_PORT,
            'debug':                str(APP_DEBUG).lower() == 'true',
            'template_path':        path.join(path.dirname(__file__), '..', 'app'),
            'static_path':          path.join(path.dirname(__file__), '..', 'static'),
            'xsrf_coocies':         True,
            'login_url':            '/auth',
            'auth_url':             APP_AUTH_URL,
            'start_time':           time.time(),
            'request_count':        0,
            'request_time':         0,
            'slow_request_count':   0,
            'slow_request_time':    0,
            'slow_request_ms':      1000,
            'mongodb':              APP_MONGODB,
            'database-host':        APP_MYSQL_HOST,
            'database-database':    APP_MYSQL_DATABASE,
            'database-user':        APP_MYSQL_USER,
            'database-password':    APP_MYSQL_PASSWORD,
            'customergroup':        APP_CUSTOMERGROUP,
            'secret':               APP_SECRET,
            'mongodbs':             {},
            'databases':            {},
        }

        # load handlers
        handlers = [(r'/', MainPage)]
        for controller in app_controllers:
            c = __import__ (controller, globals(), locals(), ['*'], -1)
            handlers.extend(c.handlers)
            for h in c.handlers:
                settings.setdefault('paths', {}).setdefault('%s.py' % controller, []).append(h[0])
        handlers.append((r'(.*)', PageNotFound))

        logging.warning('Tornado %s started to listen %s' % (APP_VERSION, APP_PORT))

        # init application
        # logging.debug('App settings:\n%s' % yaml.safe_dump(settings, default_flow_style=False, allow_unicode=True))
        tornado.web.Application.__init__(self, handlers, **settings)


if __name__ == '__main__':
    tornado.options.parse_command_line()
    tornado.locale.load_translations(path.join(path.dirname(__file__), 'main', 'translation'))

    application = myApplication()
    application.sentry_client = AsyncSentryClient(dsn=APP_SENTRY, release=APP_VERSION)

    server = tornado.httpserver.HTTPServer(application, xheaders=True, max_body_size=1024*1024*1024*5)
    # server.bind(APP_PORT)
    # server.start(0)
    server.listen(APP_PORT)

    tornado.ioloop.IOLoop.current().start()
