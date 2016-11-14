import json
import sqlalchemy
from twisted.web.resource import Resource

from db import db
from metly.util.log import log
from metly.util import constants
from SearchPager import SearchPager
from metly.model.Search import Search
from JSONRPCServer import JSONRPCServer, stream
from metly.model.WebServer import WebServer

class WebRPC(JSONRPCServer):

    ISSUED_EXTENSIONS = "client"
    CN_SUFFIX = constants.WEB_CERT_CN_SUFFIX

    def __init__(self, ca, root_ca_cert_path, search_manager, log_manager):
        JSONRPCServer.__init__(self, ca, root_ca_cert_path)

        self.search_manager = search_manager
        self.log_manager = log_manager
        self.authorized_web_servers = {}

    def json_register(self, request):
        # create a database object for the web frontend
        session = db.Session()

        try:
            uuid = self.cn_to_uuid(self.peer_cert.get_subject().commonName)

            # see if the webserver exists already
            try:
                web_server = session.query(WebServer)\
                        .filter(WebServer.uuid==uuid).one() 
                print "Webserver reporting, UUID: %s" % uuid

            except sqlalchemy.orm.exc.NoResultFound:
                # create a new webserver
                web_server = WebServer()
                web_server.uuid = uuid
                print "Webserver register.  UUID: %s" % (web_server.uuid)
                session.add(web_server)
                session.commit()

            return json.dumps({"uuid": web_server.uuid})
        finally:
            session.close()

    def json_new_search(self, request):
        search_id = int(request.json["search_id"])
        print "Notified of new search, search_id: %d" % search_id
        self.search_manager.submit_search(search_id)
        return ""

    def json_update_log_source(self, request):
        self.log_manager.update_log_source(int(request.json["id"]), \
                request.json["collector_uuid"])

    def json_open_search_pager(self, request):
        search_id = request.json["search_id"]
        search_pager = SearchPager(search_id)

        http_session = request.get_session()
        if hasattr(http_session, "search_pagers") == False:
            http_session.search_pagers = {}
        http_session.search_pagers[search_pager.uuid] = search_pager

        return json.dumps({"pager_uuid": search_pager.uuid})


    def get_pager(self, request, pager_uuid):
        http_session = request.get_session()
        if hasattr(http_session, "search_pagers") == False or \
                pager_uuid not in http_session.search_pagers:
            raise Exception("No pager with that UUID found")
        return http_session.search_pagers[pager_uuid]


    def json_set_page_info(self, request):
        """Set the pager page info and return a list of fields in the
           query to the client"""
        pager_uuid = request.json["pager_uuid"]
        page_number = int(request.json["page_number"])
        page_size = int(request.json["page_size"])

        print "Set page info"
        pager = self.get_pager(request, pager_uuid)
        pager.set_page_info(page_number, page_size=page_size)

        session = db.Session()
        try:
            search = session.query(Search).get(pager.search_id)
        finally:
            session.close()

        data = {"field_list": search.field_list}

        return json.dumps(data)



#    @stream
    def json_get_events(self, request):
        pager_uuid = request.json["pager_uuid"]

        pager = self.get_pager(request, pager_uuid)
        db_session = db.Session()
        search = db_session.query(Search).get(pager.search_id)
        db_session.close()

        for event in pager.yield_events():
            data = {"count": search.count, "row": event}
            print "Status: %d" % search.status
            request.wfile.write("%s\n" % (json.dumps(data)))
            request.wfile.flush()

        data = {"count": search.count, "status": search.status}
        request.wfile.write("%s\n" % (json.dumps(data)))
        request.wfile.flush()

        return ""


    def json_close_search_pager(self, request):
        pager_uuid = request.json["pager_uuid"]
        pager = self.get_pager(request, pager_uuid)
        pager.close()

        http_session = self.request.get_session()
        del http_session.search_pagers[pager_uuid]

    def is_authorized(self, web_server_uuid):
        web_server = None

        if web_server_uuid in self.authorized_web_servers.keys():
            web_server = self.authorized_web_servers[web_server_uuid]
        else:
            self.refresh_authorized_web_servers()
            if web_server_uuid in self.authorized_web_servers.keys():
                web_server = self.authorized_web_servers[web_server_uuid]

        if web_server == None:
            return False

        return web_server.authorized

    def refresh_authorized_web_servers(self):
        log("Populating authorized web_server uuids, uuids follow", 5)
        try:
            session = db.Session()
            web_servers = session.query(WebServer)\
                    .filter(WebServer.authorized==True).all()

            for web_server in web_servers:
                self.authorized_web_servers[web_server.uuid] = web_server
                log(web_server.uuid, 5)
            log("EOL", 5)
        finally:
            session.close()
