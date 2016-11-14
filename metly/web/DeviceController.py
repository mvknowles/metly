import json
import cherrypy
import datetime
import sqlalchemy
from formencode import Schema
from formencode import Invalid
from formencode import validators
from genshi.filters import HTMLFormFiller

import template
from Controller import Controller
from metly.model.Device import Device

class DeviceController(Controller):

    @cherrypy.expose
    def index(self):
        raise cherrypy.HTTPRedirect("/dev/list")


    @cherrypy.expose
    @template.output("devices.html")
    def list(self):
        return template.render(url=cherrypy.url)


    @cherrypy.expose
    def all(self):
        session = self.Session()

        try:
            user = cherrypy.session["user"]
            session.add(user)
            devices = session.query(Device)\
                    .filter(Device.customer_id==user.customer_id)

            nodes = []
            for device in devices:
                node = {"hostname": device.hostname, \
                        "ip_address": device.ip_address, "id": device.id}
                nodes.append(node)

            return json.dumps(nodes)


        finally:
            session.close()


    @cherrypy.expose
    def view(self, device_id):
        device_id = int(device_id)

        # look up the device
        session = self.Session()

        try:
            user = cherrypy.session["user"]
            session.add(user)
            device = session.query(Device)\
                    .filter(Device.id==device_id).one()

            # ensure that the user "owns" the device
            if device.customer_id != user.customer_id:
                raise Exception("Attack detected")

            return json.dumps(device.to_json())

        finally:
            session.close()

