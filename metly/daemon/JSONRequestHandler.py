import cgi
import sys
import uuid
import socket
import traceback
import BaseHTTPServer

from metly.util.log import log
from metly.exception.NotAuthorizedException import NotAuthorizedException

class Session(object):
    pass

class JSONRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

#    rpc = None
#    sessions = None

    def setup(self):
        self.connection = self.request
        self.rfile = socket._fileobject(self.request, "rb", self.rbufsize)
        self.wfile = socket._fileobject(self.request, "wb", self.wbufsize)

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

    def get_session(self):
        cookie = self.headers.getheader("Cookie").split("sessionid=")[1]
        return self.sessions[cookie]


    def send_headers(self, code):
        self.send_response(code)
        self.send_header("Content-type", "application/json")
        if "Cookie" in self.headers:
            cookie = self.headers.getheader("Cookie").split("sessionid=")[1]
        else:
            cookie = str(uuid.uuid4())
            self.send_header("Set-Cookie", "sessionid=%s" % cookie)

        if cookie not in self.sessions:
            self.sessions[cookie] = Session()

        session = self.sessions[cookie]


    def do_POST(self):

        try:
            content_type_header = self.headers.getheader("content-type")
            content_type, post_dict = cgi.parse_header(content_type_header)
            length = int(self.headers.getheader("content-length"))

            if content_type == "multipart/form-data":
                environ = {"REQUEST_METHOD":"POST", \
                        "CONTENT_TYPE":self.headers["Content-Type"]}

                fs = cgi.FieldStorage(fp=self.rfile, headers=self.headers, \
                        environ=environ)

                self.rpc.post_binary_part(self, fs)
                return

            if content_type != "application/json":
                self.wfile.write("Expected JSON data")

            # TODO: do we need a timeout
            post_body = self.rfile.read(length)

            post_body = "".join(post_body)

            response = self.rpc.render_json(post_body, self)
            self.send_headers(200)
            self.end_headers()
            #TODO: check that this actually writes all the bytes
            if response != None:
                self.wfile.write(response)
        except NotAuthorizedException, ex:
            log("Unauthorized connection from ... %s:%d" % self.client_address, 0)
            self.send_headers(403)
            self.send_header("UUID", ex.uuid)
            self.end_headers()

        except Exception, ex:
            self.send_headers(500)
            self.end_headers()
            tb = "%s\n" % traceback.format_exc()
            json_data = {"error": ex.__class__.__name__, "traceback": tb}
            sys.stderr.write(tb)
            self.wfile.write(json_data)

    def get_cert(self):
        return self.request.get_peer_certificate()

    def shutdown(self, sock_args):
        super(BaseHTTPServer, self).shutdown()
