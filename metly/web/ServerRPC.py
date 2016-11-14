import os
import sys
import json
import urllib3
from urllib3.connectionpool import HTTPSConnectionPool

from metly.util.CertUtil import CertUtil
from metly.util.JSONRPCClient import JSONRPCClient
from metly.exception.NotAuthorizedException import NotAuthorizedException

class JSONCallable(object):
    def __init__(self, json_rpc, command):
        self.json_rpc = json_rpc
        self.command = command

    def __call__(self, *args, **kwargs):
        return self.json_rpc(self.command, *args, **kwargs)


class ServerRPC(JSONRPCClient):

    HTTP_POOL_TIMEOUT = 600
    MAX_DAEMON_CONNECTIONS = 200

    #TODO: make this a decorator instead
    #TODO: why is this needed???
    JSON_FUNCTIONS = set(["get_server_info", "new_search", "new_quick_search", \
            "register", "open_search_pager", "close_search_pager", \
            "get_events", "set_page_info"])

    DEFAULT_SUBJECT = ("/C=AU/ST=New South Wales/L=Sydney/O=Metly/"
            "OU=Metly Default Webserver/CN=%s/"
            "emailAddress=support@metly.com.au")

    def __init__(self, server_host, server_port, working_dir):
        self.server_host = server_host
        self.server_port = server_port
        self.working_dir = working_dir
        self.cookie = None

        #TODO: add file permissions
        if os.path.exists(self.working_dir) == False:
            os.makedirs(self.working_dir)

    
    def connect(self):
        self.ca_cert_path = os.path.join(self.working_dir, "ca.crt")
        self.cert_path = os.path.join(self.working_dir, "web.crt")
        self.key_path = os.path.join(self.working_dir, "web.key")

        uuid = None

        # do we have a ca certificate, key and cert?
        if os.path.exists(self.ca_cert_path) == False or \
                os.path.exists(self.cert_path) == False or \
                os.path.exists(self.key_path) == False:

            # request it from the server
            # don't validate the server certificate as we don't have the ca yet
            # this is obviously opportunistic encryption
            urllib3.disable_warnings()

            self.pool = HTTPSConnectionPool(self.server_host, \
                    port=self.server_port, cert_reqs="CERT_NONE", \
                    assert_hostname=False, timeout=self.HTTP_POOL_TIMEOUT, \
                    maxsize=self.MAX_DAEMON_CONNECTIONS)

            self.request_cert()
            self.start_pool()
            json_result = self.register()
            uuid = json_result["uuid"]

        else:
            self.start_pool()

        self.get_server_info()

    def start_pool(self):
        self.pool = HTTPSConnectionPool(self.server_host, \
                port=self.server_port, cert_reqs="CERT_REQUIRED", \
                key_file=self.key_path, cert_file=self.cert_path, \
                ca_certs=self.ca_cert_path, assert_hostname=False)



    def request_cert(self):

        json_result = self.json_rpc("get_cn")
        cn = json_result["cn"]

        cert_util = CertUtil()
        csr = CertUtil.create_csr(self.DEFAULT_SUBJECT % (cn), self.key_path)

        json_result = self.json_rpc("sign_csr", csr=csr)
        cert_fh = open(self.cert_path, "w")
        cert_fh.write(json_result["certificate"])
        cert_fh.close()

        json_result = self.json_rpc("get_ca_cert")
        ca_cert_fh = open(self.ca_cert_path, "w")
        ca_cert_fh.write(json_result["ca_certificate"])
        ca_cert_fh.close()

        # check a proper secure connection
        self.start_pool()


    # dynamically allow JSONRPC calls
    def __getattr__(self, attr_name):
        if attr_name in self.JSON_FUNCTIONS:
            return JSONCallable(self.json_rpc, attr_name)

        return self.__getattribute__(attr_name)

#    def json_rpc(self, fn, *args, **kwargs):
#
#        kwargs["function"] = fn
#
#        json_data = json.dumps(kwargs)
#
#        headers = {'Content-Type':'application/json'}
#        if self.cookie != None:
#            headers["Cookie"] = self.cookie
#
#        response = self.pool.urlopen("POST", "/jsonrpc", \
#                headers=headers, body=json_data)
#
#        if "Set-Cookie" in response.headers:
#            self.cookie = response.headers["Set-Cookie"].split(";")[0]
#            print "Cookie: %s" % self.cookie
#
#        if response.status == 403:
#            uuid = response.headers["UUID"]
#            raise NotAuthorizedException(uuid)
#
#        content = response.data
#        if len(content) == 0:
#            return None
#        if content.lower() == "true":
#            return True
#
#        json_content = json.loads(content)
#
#        if "error" in json_content:
#            error = json_content["error"]
#            error_module = __import__("metly.exception.%s" % error, \
#                    fromlist=[error])
#            error_class = getattr(error_module, error)
#
#            raise error_class()
#
#        return json_content

