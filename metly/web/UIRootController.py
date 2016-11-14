import cherrypy

from metly.model.Customer import Customer

from auth import AuthController
from Controller import Controller
from UserController import UserController
from DeviceController import DeviceController
from SearchController import SearchController
from SourceController import SourceController
from CollectorController import CollectorController
from ServiceRequestController import ServiceRequestController

class UIRootController(Controller):

    def __init__(self, server_rpc):
        Controller.__init__(self, server_rpc)

        self.auth = AuthController(server_rpc)
        self.sr = ServiceRequestController(server_rpc)
        self.col = CollectorController(server_rpc)
        self.dev = DeviceController(server_rpc)
        self.user = UserController(server_rpc)
        self.search = SearchController(server_rpc)
        self.src = SourceController(server_rpc)

    @cherrypy.expose
    def index(self):
        tmpl = self.loader.load('index.html')
        user = cherrypy.session["user"]

        stream = tmpl.generate(errors=None, url=cherrypy.url, user=user)
        return stream.render('html', doctype='html')

    @cherrypy.expose
    def c(self, customer_name):
        cherrypy.session.regenerate()

        session = self.Session()
        # see if customer exists
        try:
            customer = session.query(Customer)\
                   .filter(Customer.name==customer_name).one()

            cherrypy.session["customer"] = customer_name
            raise cherrypy.HTTPRedirect("/auth/prompt")

        except NoResultFound:
            return "Please contact support"

        finally:
            session.close()



    @cherrypy.expose
    def cdebug(self):
        return "Customer = %s" % cherrypy.session.get("customer")
