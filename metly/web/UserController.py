import cherrypy
import sqlalchemy
from formencode import Schema
from formencode import Invalid
from formencode import validators
from genshi.filters import HTMLFormFiller

import template
from metly.util import hash
from Controller import Controller
from metly.model.User import User

class PasswordException(Exception):
    pass

class UserController(Controller):

    @cherrypy.expose
    def index(self):
        raise cherrypy.HTTPRedirect("/user/list")


    @cherrypy.expose
    @template.output("new_user.html")
    def new(self, **data):
        if cherrypy.request.method == "POST":
            return self.submit_new(data)

        edit_user = User()
        edit_user.enabled = True
        cherrypy.session["edit_user"] = edit_user

        return template.render(errors={}) | \
                HTMLFormFiller(data=edit_user.__dict__)


    def submit_new(self, form_data):

        session = self.Session()

        edit_user = cherrypy.session["edit_user"]
        errors = {}

        try:
            validator = NewFormValidator()
            form_data = validator.to_python(form_data)
        
            user = cherrypy.session["user"]
            session.add(user)
            session.add(edit_user)

            edit_user.customer_id = user.customer_id
            edit_user.username = form_data["username"]
            edit_user.firstname = form_data["firstname"]
            edit_user.lastname = form_data["lastname"]
            edit_user.email = form_data["email"]
            edit_user.enabled = form_data["enabled"]

            print "User added"
            print edit_user.enabled

            #TODO this would probably be better handled with a custom validator
            if form_data["password"] == "":
                if hasattr(edit_user, "orig_password") == True:
                    # we're updating a record, so just keep the old password
                    edit_user.password = edit_user.orig_password
                    print "set original password %s" % (edit_user.password)
                else:
                    # they've entered a blank password. error the fuck out

                    errors["password"] = "Please enter a non-blank password"
                    raise PasswordException()

            else:
                edit_user.salt = hash.new_salt()
                edit_user.password = hash.hash_password(form_data["password"], \
                        edit_user.salt)
                print "created a new password"


            session.commit()

            raise cherrypy.HTTPRedirect("/user/list")

        except Invalid, ex:
            errors = ex.error_dict
        except PasswordException:
            pass
        finally:
            session.close()

#        edit_user.orig_password = edit_user.password
#        edit_user.password = ""

        return template.render(errors=errors) | HTMLFormFiller(data=form_data)


    @cherrypy.expose
    @template.output("new_user.html")
    def edit(self, user_id):
        user_id = int(user_id)

        session = self.Session()

        try:
            user = cherrypy.session["user"]
            session.add(user)
            # note that we add in the customer id to verify the user is allowed
            # to edit the object
            edit_user = session.query(User)\
                    .filter(User.id==user_id)\
                    .filter(User.customer_id==user.customer_id).one()

            edit_user.orig_password = edit_user.password
            edit_user.password = ""
            cherrypy.session["edit_user"] = edit_user

            return template.render(errors={}) | \
                    HTMLFormFiller(data=edit_user.__dict__)

        finally:
            session.close()


    @cherrypy.expose
    @template.output("users.html")
    def list(self):
        session = self.Session()

        try:
            user = cherrypy.session["user"]
            session.add(user)
            users = session.query(User)\
                    .filter(User.customer_id==user.customer_id)

            return template.render(users=users, url=cherrypy.url)

        finally:
            session.close()


class NewFormValidator(Schema):
    username = validators.UnicodeString(not_empty=True)
    firstname = validators.UnicodeString(not_empty=True)
    lastname = validators.UnicodeString(not_empty=True)
    email = validators.UnicodeString(not_empty=True)
    password = validators.UnicodeString(not_empty=False)
    enabled = validators.StringBoolean(if_missing=False)
