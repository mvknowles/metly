import os
import cherrypy
import sqlalchemy
from formencode import Schema
from formencode import Invalid
from formencode import validators
from genshi.filters import HTMLFormFiller
from sqlalchemy.orm.exc import NoResultFound

import template
from Controller import Controller
from metly.model.User import User
from metly.util import hash

SESSION_KEY = "_cp_username"

class AuthFailedException(Exception):
    pass

class UserDisabledException(Exception):
    pass

def noauth(*args):
    """Decorator that tells cherrypy not to authenticate"""

    def decorate(fn):
        if not hasattr(fn, "_cp_config"):
            fn._cp_config = dict()
        
        if "noauth" not in fn._cp_config:
            fn._cp_config["noauth"] = True


        return fn

    return decorate


def check_auth(*args, **kwargs):
    """This is called by the before_handler before every page request"""

    path_info = cherrypy.request.path_info

    if path_info.startswith("/static/"):
        return

    # authenticate them unless the function is decorated with noauth

    if cherrypy.request.config.get("noauth", None) != True:

        if not cherrypy.session.get(SESSION_KEY):
            raise cherrypy.HTTPRedirect("/auth/login")


cherrypy.tools.authenticate = cherrypy.Tool("before_handler", check_auth)

class AuthController(Controller):

#    @cherrypy.expose
#    @noauth()
#    def prompt(self):
#
#        tmpl = self.loader.load("auth.html")
#        return tmpl.generate(url=cherrypy.url, errors={}).render("html", \
#                doctype="html", encoding="us-ascii")

    @cherrypy.expose
    @noauth()
    @template.output("auth.html")
    def login(self, **data):
        errors = {}

        if cherrypy.request.method == "POST":
            errors = self.submit_login(data)

        # if we're here, it means something has gone wrong.  Render the prompt
        # page
        return template.render(url=cherrypy.url, errors=errors) | \
                HTMLFormFiller(data=data)

    def submit_login(self, data):

        # throw away any existing session and start fresh
        cherrypy.session.regenerate()

        session = self.Session()

        try:
            form_data = LoginValidator().to_python(data)
            username = form_data["username"]
            password = form_data["password"]

            user = session.query(User)\
                   .filter(User.username==username).one()

            hashed_password = hash.hash_password(password, user.salt)
            if hashed_password != user.password:
                raise AuthFailedException()

            if user.enabled == False:
                raise UserDisabledException()

            # if we get all the way here, it means we've succeeded
            # establish a session and redirect to home page
            cherrypy.session["user"] = user
            cherrypy.session[SESSION_KEY] = username
            raise cherrypy.HTTPRedirect("/")

        except (NoResultFound, AuthFailedException):
            errors = {"auth": "Username not found or password incorrect"}

        except UserDisabledException:
            errors = {"auth": \
                    "Username disabled.  Please contact an administrator."}

        except Invalid, ex:
            errors = ex.error_dict

        finally:
            session.close()

        return errors

                


    @cherrypy.expose
    def logout(self):
        username = cherrypy.session.get(SESSION_KEY, None)
        cherrypy.session[SESSION_KEY] = None

        if username:
            cherrypy.request.login = None

        cherrypy.lib.sessions.expire()

        raise cherrypy.HTTPRedirect("/auth/login")


class LoginValidator(Schema):
    username = validators.UnicodeString(not_empty=True)
    password = validators.UnicodeString(not_empty=True)
