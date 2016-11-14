import json
import uuid

from db import db
from metly.util.log import log
from metly.util import constants
from metly.exception.NotAuthorizedException import NotAuthorizedException

def stream(func):
    def func_wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    func_wrapper.__stream__ = True
    return func_wrapper

class JSONRPCServer(object):

    UNAUTHED_FUNCTIONS = ["get_cn", "get_ca_cert", "sign_csr", "register"]
    OK = "True"

    def __init__(self, ca, root_ca_cert_path):
        self.ca = ca
        self.root_ca_cert_path = root_ca_cert_path

        self.modules = {}

    def render_json(self, post_data, request):
        # make sure sessions are enabled

        self.peer_cert = request.get_cert()
        json_request = json.loads(post_data)

        fn = json_request["function"]
        request.json = json_request

        print fn
        if fn not in self.UNAUTHED_FUNCTIONS:
            cn = self.peer_cert.get_subject().commonName
            uuid = self.cn_to_uuid(cn)

            if self.is_authorized(uuid) != True:
                raise NotAuthorizedException(uuid)

        # enable "modules" by adding a dot character.
        #TODO: check the security of this
        fn_parts = fn.split(".")
        if len(fn_parts) == 2:
            json_module = self.json_modules[fn_parts[0]]
            fn = fn_parts[1]
        else:
            json_module = self
            fn = fn_parts[0]

        # if the function has a @stream decorator, they will open the
        # response file handle and write directly to the client
        fn = getattr(self, "json_%s" % (fn))
        if hasattr(fn, "__stream__") == True:
            fn(request)
        else:
            return fn(request)


    def json_sign_csr(self, request):
        csr = request.json["csr"]

        cert = self.ca.sign_csr(csr, extensions=self.ISSUED_EXTENSIONS)

        response = {"certificate": cert}
        json_response = json.dumps(response)

        return json_response

    def json_get_cn(self, request):
        cn = str(uuid.uuid1())
        return json.dumps({"cn": "%s%s" % (cn, \
                self.CN_SUFFIX)})


    def json_get_ca_cert(self, request):
        ca_cert_fh = open(self.root_ca_cert_path, "r")
        ca_cert = ca_cert_fh.read()
        ca_cert_fh.close()

        return json.dumps({"ca_certificate": ca_cert})

    def cn_to_uuid(self, cn):
        return cn.replace(self.CN_SUFFIX, "")

    def json_get_server_info(self, request):
        return json.dumps({"server_version": "0.1"})

    def is_authorized(self, common_name):
        raise NotImplemented()
