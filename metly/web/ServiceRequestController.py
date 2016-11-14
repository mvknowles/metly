import cherrypy
import datetime
import sqlalchemy
from formencode import Schema
from formencode import Invalid
from formencode import validators
from genshi.filters import HTMLFormFiller

import template
from Controller import Controller
from metly.model.ServiceRequest import ServiceRequest

class ServiceRequestController(Controller):

    @cherrypy.expose
    def index(self):
        raise cherrypy.HTTPRedirect("/sr/list")

    @cherrypy.expose
    @template.output("new_service_request.html")
    def new(self, **data):
        if cherrypy.request.method == "POST":
            return self.submit_new(data)

        cherrypy.session["sr"] = ServiceRequest()

        return template.render(errors={})


    def submit_new(self, form_data):
        # TODO: come up with a better way to do this
        form_data["due_date"] = datetime.datetime.strptime(\
                form_data["due_date"], "%Y-%m-%d")
        validator = NewFormValidator()
        form_data = validator.to_python(form_data)

        user = cherrypy.session["user"]
        sr = cherrypy.session["sr"]

        session = self.Session()

        try:

            session.add(user)
            session.add(sr)
            sr.customer_id = user.customer_id
            sr.user_id = user.id
            sr.set_from_dict(form_data)
    #        sr.title = form_data["title"]
    #        sr.due_date = form_data["due_date"]
    #        sr.external_id = form_data["external_id"]
    #        sr.description = form_data["description"]

            session.add(sr)
            session.commit()

            raise cherrypy.HTTPRedirect("/sr/list")
        finally:
            session.close()



    @cherrypy.expose
    @template.output("new_service_request.html")
    def edit(self, sr_id):
        sr_id = int(sr_id)

        session = self.Session()

        try:
            user = cherrypy.session["user"]
            session.add(user)
            # note that we add in the customer id to verify the user is allowed
            # to edit the object
            sr = session.query(ServiceRequest)\
                    .filter(ServiceRequest.id==sr_id)\
                    .filter(ServiceRequest.customer_id==user.customer_id).one()

            cherrypy.session["sr"] = sr

            return template.render(errors={}) | HTMLFormFiller(data=sr.__dict__)

        finally:
            session.close()


    @cherrypy.expose
    @template.output("service_requests.html")
    def list(self):
        session = self.Session()

        try:
            user = cherrypy.session["user"]
            session.add(user)
            service_requests = session.query(ServiceRequest)\
                    .filter(ServiceRequest.customer_id==user.customer_id)

            return template.render(srs=service_requests, url=cherrypy.url)

        finally:
            session.close()




class NewFormValidator(Schema):
    title = validators.UnicodeString(not_empty=True)
    #requestor = validators.Int()
    due_date = validators.DateValidator(after_now=True, date_format="%Y-%m-%d")
    external_id = validators.UnicodeString(not_empty=False)
    description = validators.UnicodeString(not_empty=True)

