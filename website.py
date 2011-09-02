#!/usr/bin/env python
# encoding: utf-8

import os.path
import re
import datetime
import tornado.auth
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import unicodedata
from mongoengine import *

from tornado.options import define, options

define("port", default=8888, help="run on the given port", type=int)
define("debug", default=False, help="debug mode", type=bool)

from v2.web import blog, auth

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", blog.HomeHandler),
            (r"/archive", blog.ArchiveHandler),
            (r"/feed", blog.FeedHandler),
            (r"/blog/([^/]+)", blog.ArticleHandler),
            
            (r"/auth/login", auth.LoginHandler),
            (r"/auth/logout", auth.LogoutHandler),
            
            (r"/admin/?", blog.OverviewHandler),
            (r"/admin/overview", blog.OverviewHandler),
            (r"/admin/write", blog.ComposeHandler),
            (r"/admin/edit/(.*)", blog.ComposeHandler),
            (r"/admin/remove/(.*)", blog.RemoveHandler),
        ]
        settings = dict(
            blog_title = u"Tornado Blog",
            template_path = os.path.join(os.path.dirname(__file__), "templates"),
            theme = 'default',
            static_path = os.path.join(os.path.dirname(__file__), "static"),
            ui_modules = {},
            xsrf_cookies = True,
            cookie_secret = "11oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
            login_url = "/auth/login",
            autoescape = None,
            debug = options.debug,
        )
        tornado.web.Application.__init__(self, handlers, **settings)

        # Have one global connection to the blog DB across all handlers
        self.db = None
        
        connect('v2blog', port=7680)

def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
