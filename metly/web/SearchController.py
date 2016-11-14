import json
import time
import cherrypy
import sqlalchemy
import formencode
from formencode import Schema
from formencode import Invalid
from formencode import validators
from genshi.filters import HTMLFormFiller

import template
from metly.util import hash
from Controller import Controller
from metly.model.User import User
from metly.model.Device import Device
from metly.model.Search import Search
from metly.model.Collector import Collector
from metly.util.cef_fields import cef_fields

class QueryType(object):

    def __init__(self, query_type_id, name):
        self.query_type_id = query_type_id
        self.name = name

class SearchController(Controller):

#    QUERY_TYPES = [ \
#            ("Auto-detect", -1), \
#            ("Text", Search.QueryType.TEXT), \
#            ("SQL", Search.QueryType.SQL), \
#            ("Regular Expression", Search.QueryType.REGEX), \
#            ("HBase Expression", Search.QueryType.HBASE) \
#    ]


    QUERY_TYPES = { 
            -1: "Auto-detect", \
            Search.QueryType.TEXT: "Text", \
            Search.QueryType.SQL: "SQL", \
            Search.QueryType.REGEX: "Regular Expression", \
            Search.QueryType.HBASE: "HBase Expression"
    }

    QUERY_TYPE_ORDER = [
            -1,
            Search.QueryType.REGEX, \
            Search.QueryType.SQL, \
            Search.QueryType.TEXT, \
            Search.QueryType.HBASE, \
    ]

    def __init__(self, server_rpc):
        Controller.__init__(self, server_rpc)

        self.s_query_types = []

        for query_type_id in self.QUERY_TYPE_ORDER:
            t = (query_type_id, self.QUERY_TYPES[query_type_id])
            self.s_query_types.append(t)


    @cherrypy.expose
    def index(self):
        raise cherrypy.HTTPRedirect("/search/list")


    @cherrypy.expose
    def new_quick(self, **data):
        data["title"] = data["expression"]
        data["description"] = ""
        data["external_id"] = ""
        data["query_type"] = Search.QueryType.SQL
        search = self.submit_new(data)

        return self.results(search.id)


    @cherrypy.expose
    @template.output("new_search.html")
    def new(self, **data):
        if cherrypy.request.method == "POST":
            return self.submit_new(data)

        session = self.Session()

        try:

            user = cherrypy.session["user"]
            search = Search()
            cherrypy.session["search"] = search
            data = search.__dict__

            return template.render(errors={}, query_types=self.s_query_types, \
                    search_type=-1) | HTMLFormFiller(data=data)

        finally:
            session.close()


    def submit_new(self, data):
        session = self.Session()

        try:
            user = cherrypy.session["user"]
            session.add(user)

            validator = NewFormValidator()
            data = validator.to_python(data)
            search = Search() # cherrypy.session["search"]
            search.customer_id = user.customer_id
            search.user_id = user.id
            print "User ID = %d" % search.user_id
            search.status = search.Status.QUEUED
            search.query_type = data["query_type"]
            search.title = data["title"]
            search.external_id = data["external_id"]
            search.description = data["description"]
            search.expression = data["expression"]

            session.add(search)
            session.commit()

            print "Starting RPC call"
            self.server_rpc.new_search(search_id=search.id)
            print "Finished RPC call"
            return search

        except Invalid, ex:
            print "Exception"
            print ex

        finally:
            session.close()

    @cherrypy.expose
    def set_page_info(self, **data):
#        cherrypy.response.headers["Content-Type"] = "application/json"
        pager_uuid = data["pager_uuid"]
        page_number = int(data["page_number"])
        page_size = 20
        print "Set_page_info"
        json_data = self.server_rpc.set_page_info(pager_uuid=pager_uuid, \
                page_number=page_number, page_size=page_size)
        print "Start field list"
        print json_data["field_list"]
        print "stop field list"
        return json_data["field_list"]


    @cherrypy.expose
    def get_events(self, **data):
        pager_uuid = data["pager_uuid"]
        page_number = int(data["page_number"])
#        cherrypy.response.headers["Content-Type"] = "application/json"

        count = None
        status = None
        rows = []
        response = {}
        try:
            request = self.server_rpc.json_rpc_request("get_events", \
                    pager_uuid=pager_uuid)

            for line in request:
                #print line
                try:
                    data = json.loads(line)
                except ValueError, ex:
                    print line

                if "count" in data:
                    count = data["count"]

                if "row" in data:
                    rows.append(data["row"])

                if "status" in data:
                    status = data["status"]
                    #print status

            response["count"] = count
            response["rows"] = rows
            response["status"] = status
            #print rows

        finally:
            pass
#            # this prevents the browser from ddossing us
#            if len(rows) == 0:
#                time.sleep(2)

        return json.dumps(response)

#    get_events._cp_config = {"response.stream": True}

    def get_page_generator(self, request):
        # yield one result at a time
        print "Yield %s" % line
        yield "data: %s\n" % (line)
#
        yield "\n"

    

    @cherrypy.expose
    @template.output("search_results.html")
    def results(self, search_id):
        print "results"
        search_id = int(search_id)
        #TODO: this should be closed with the session timeout
        json_data = self.server_rpc.open_search_pager(search_id=search_id)
        pager_uuid = json_data["pager_uuid"]

        session = self.Session()

        try:
            user = cherrypy.session["user"]
            session.add(user)
            # note that we add in the customer id to verify the user is allowed
            # to edit the object
            search = session.query(Search)\
                    .filter(Search.id==search_id)\
                    .filter(Search.customer_id==user.customer_id).one()

#            collectors = session.query(Collector)\
#                    .filter(Collector.customer_id==user.customer_id)
#            devices = session.query(Device)\
#                    .filter(Device.customer_id==user.customer_id)

            return template.render(errors={}, search=search, \
                    search_type=search.query_type, \
                    query_types=self.QUERY_TYPES, \
                    pager_uuid=pager_uuid)

        finally:
            session.close()



#    @cherrypy.expose
    @template.output("new_search.html")
    def edit(self, search_id):
        search_id = int(search_id)

        session = self.Session()

        try:
            user = cherrypy.session["user"]
            session.add(user)
            # note that we add in the customer id to verify the user is allowed
            # to edit the object
            search = session.query(Search)\
                    .filter(Search.id==search_id)\
                    .filter(Search.customer_id==user.customer_id).one()

#            collectors = session.query(Collector)\
#                    .filter(Collector.customer_id==user.customer_id)

            cherrypy.session["search"] = search

            return template.render(errors={}, query_types=self.QUERY_TYPES) | \
                    HTMLFormFiller(data=search.__dict__)

        finally:
            session.close()



    @cherrypy.expose
    @template.output("searches.html")
    def list(self):
        session = self.Session()

        try:

            print "TOP"
            user = cherrypy.session["user"]
            session.add(user)
            searches = session.query(Search)\
                    .options(sqlalchemy.orm.joinedload('user'))\
                    .filter(Search.customer_id==user.customer_id)\
                    .all()


            for search in searches:
                if search.query_type == None:
                    search.query_type = -1
                search.status_text = self.QUERY_TYPES[search.query_type]

            print "Bottom"

            return template.render(searches=searches, url=cherrypy.url)

        finally:
            session.close()

#    @cherrypy.expose
#    def get_collector_devices(self, **form_data):
#        session = self.Session()
#
#        try:
#            validator = CollectorDevicesFormValidator()
#            form_data = validator.to_python(form_data)
#        
#            user = cherrypy.session["user"]
#            session.add(user)
#
#            devices = session.query(Device)\
#                    .filter(Device.customer_id==user.customer_id)
#                    .filter(Device.id.in())
#
#            return template.render(devices=devices, errors=errors) |\
#                    HTMLFormFiller(data=form_data)
#
#        finally:
#            session.close()





class NewFormValidator(Schema):
#    allow_extra_fields = True
#    filter_extra_fields = True
    title = validators.UnicodeString(not_empty=True)
    query_type = validators.Int(not_empty=True)
    expression = validators.UnicodeString(not_empty=True)
    external_id = validators.UnicodeString(not_empty=False)
    description = validators.UnicodeString(not_empty=False)
#    collectors = formencode.ForEach(formencode.validators.Int())
#    devices = formencode.ForEach(formencode.validators.Int())
