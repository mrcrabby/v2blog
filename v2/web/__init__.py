#!/usr/bin/env python
# -*- coding:utf-8 -*-

import logging
import time
import shlex
import subprocess

from email import encoders
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE
from email.utils import formatdate
import smtplib

import tornado.ioloop
import tornado.web
import tornado.escape

class BaseHandler(tornado.web.RequestHandler):

    @property
    def root_path(self):
        """
        获取项目根目录
        """
        return self.application.settings.get('root_path')

    def get_current_user(self):
        """
        从cookie中获取当前登录用户信息，如果没有登录则返回None
        """
        user = self.get_secure_cookie("user")
        if not user: return None
        return tornado.escape.json_decode(user)

    def get_header(self, name, default=None):
        """
        获取请求头信息
        """
        return self.request.headers[name] or default

################################################################################
#
# AsyncProcessMixin is borrowed from Philip Plante
# http://gist.github.com/489093
#
# Copyright (c) 2010, Philip Plante of EndlessPaths.com
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

class AsyncProcessMixIn(tornado.web.RequestHandler):
    """
    class SampleHandler(AsyncProcessMixIn):
        @tornado.web.asynchronous
        def get(self):
            self.call_subprocess('ls /', self.on_ls)

        def on_ls(self, output, return_code):
            self.write("return code is: %d" % (return_code,))
            self.write("output is:\n%s" % (output.read(),)) # output is a file-like object returned by subprocess.Popen

            self.finish()

    """
    def call_subprocess(self, command, callback=None):
        self.ioloop = tornado.ioloop.IOLoop.instance()
        self.pipe = p = subprocess.Popen(shlex.split(command), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
        self.ioloop.add_handler(p.stdout.fileno(), self.async_callback(self.on_subprocess_result, callback), self.ioloop.READ)

    def on_subprocess_result(self, callback, fd, result):
        try:
            if callback:
                callback(self.pipe.stdout)
        except Exception, e:
            logging.error(e)
        finally:
            self.ioloop.remove_handler(fd)

class MailMixin(object):
    
    def send_mail(self, sender, to, subject, body, html=None, attachments=[]):
        """Send an email.

        If an HTML string is given, a mulitpart message will be generated with
        plain text and HTML parts. Attachments can be added by providing as a
        list of (filename, data) tuples.
        """
        if html:
            # Multipart HTML and plain text
            message = MIMEMultipart("alternative")
            message.attach(MIMEText(body, "plain"))
            message.attach(MIMEText(html, "html"))
        else:
            # Plain text
            message = MIMEText(body)

        if attachments:
            part = message
            message = MIMEMultipart("mixed")
            message.attach(part)
            for filename, data in attachments:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(data)
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", "attachment",
                    filename=filename)
                message.attach(part)
        
        message["Date"] = formatdate(time.time())
        message["From"] = sender
        message["To"] = COMMASPACE.join(to)
        message["Subject"] = subject
        
        server = smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT)
        server.sendmail(sender, to, message.as_string())
        server.quit()