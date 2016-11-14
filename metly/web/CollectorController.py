import cherrypy
import sqlalchemy
from formencode import Schema
from formencode import Invalid
from formencode import validators
from genshi.filters import HTMLFormFiller

import template
from Controller import Controller
from metly.model.Network import Network
from metly.model.Collector import Collector

class CollectorController(Controller):

    @cherrypy.expose
    def index(self):
        raise cherrypy.HTTPRedirect("/col/list")


    @cherrypy.expose
    @template.output("find_collector.html")
    def find(self, **data):
        if cherrypy.request.method == "POST":
            return self.submit_find(data) 

        return template.render(errors={})


    @template.output("find_collector.html")
    def submit_find(self, form_data):

        errors = {}
        session = self.Session()
        try:
            validator = FindFormValidator()
            form_data = validator.to_python(form_data)
            cherrypy.session["collector"] = session.query(Collector)\
                   .filter(Collector.uuid==form_data["collector_uuid"]).one()
            raise cherrypy.HTTPRedirect("/col/new")

        except sqlalchemy.orm.exc.NoResultFound:
            errors = {"collector_uuid":
                    "Could not find a collector with that ID"}
        except Invalid, ex:
            errors = ex.error_dict
        finally:
            session.close()

        return template.render(errors=errors) | HTMLFormFiller(data=form_data)


    @cherrypy.expose
    @template.output("new_collector.html")
    def new(self, **data):
        if cherrypy.request.method == "POST":
            return self.submit_new(data)

        collector = cherrypy.session["collector"]

        return template.render(errors={}, \
                collector_uuid=collector.uuid) | \
                HTMLFormFiller(data=collector.__dict__)


    def submit_new(self, form_data):

        session = self.Session()

        try:
            validator = NewFormValidator()
            form_data = validator.to_python(form_data)
        
            user = cherrypy.session["user"]
            collector = cherrypy.session["collector"]
            session.add(user)
            session.add(collector)

            # TODO: enable multiple network support once we need it
            network = session.query(Network)\
                    .filter(Network.customer_id==user.customer_id)\
                    .filter(Network.name=="Default").one()

            collector.customer_id = user.customer_id
            collector.name = form_data["name"]
            collector.location = form_data["location"]
            collector.network_id = network.id

            session.commit()

            raise cherrypy.HTTPRedirect("/col/list")

        except Invalid, ex:
            errors = ex.error_dict
        finally:
            session.close()

#        collector_uuid = cherrypy.session["collector"].get_uuid()

#        return template.render(collector_uuid=collector_uuid, errors=errors) | \
#                 HTMLFormFiller(data=form_data)


    @cherrypy.expose
    def edit(self, collector_id):
        collector_id = int(collector_id)

        # look up the collector
        session = self.Session()

        try:
            user = cherrypy.session["user"]
            session.add(user)
            collector = session.query(Collector)\
                    .filter(Collector.id==collector_id).one()

            # ensure that the user "owns" the collector
            if collector.customer_id != user.customer_id:
                raise Exception("Attack detected")

            cherrypy.session["collector"] = collector
        
        finally:
            session.close()

        raise cherrypy.HTTPRedirect("/col/new")


    @cherrypy.expose
    @template.output("collectors.html")
    def list(self):
        session = self.Session()

        try:
            user = cherrypy.session["user"]
            session.add(user)
            collectors = session.query(Collector)\
                    .filter(Collector.customer_id==user.customer_id)

            return template.render(collectors=collectors, url=cherrypy.url)

        finally:
            session.close()


class FindFormValidator(Schema):
    collector_uuid = validators.UnicodeString(not_empty=True)


class NewFormValidator(Schema):
    name = validators.UnicodeString(not_empty=True)
    location = validators.UnicodeString(not_empty=False)
