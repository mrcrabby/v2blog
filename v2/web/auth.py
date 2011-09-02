#!/usr/bin/env python
# encoding: utf-8

import tornado.auth
import tornado.web

from v2.web import BaseHandler

class LoginHandler(BaseHandler, tornado.auth.GoogleMixin):
    @tornado.web.asynchronous
    def get(self):
        if self.get_argument("openid.mode", None):
            self.get_authenticated_user(self.async_callback(self._on_auth))
            return
        self.authenticate_redirect()
    
    def _on_auth(self, user):
        if not user:
            raise tornado.web.HTTPError(500, "Google auth failed")

        current_user = {
            'email': user['email'],
            'name': user['name'],
        }

        self.set_secure_cookie("user", tornado.escape.json_encode(user), expires_days=15)
        self.redirect(self.get_argument("next", "/"))

class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user")
        self.redirect(self.get_argument("next", "/"))