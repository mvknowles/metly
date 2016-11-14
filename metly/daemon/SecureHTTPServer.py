import os
import cgi
import sys

import socket, os
from SocketServer import BaseServer
from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
from OpenSSL import SSL


class VerifyCNSuffixCallback(object):
    def __init__(self, cn_suffix):
        #TODO: I don't have any idea what this is for
        self.__name__ = "wtf is this"
        self.cn_suffix= cn_suffix
        print self.cn_suffix

    def __call__(self, connection, cert, error_num, depth, ok):

        if error_num != 0 or ok != 1:
            return False

        subject = cert.get_subject()

        if depth == 2 and subject.commonName == "ca.metly.local":
            return True

        if depth == 1 and subject.commonName.endswith(".issuing.metly.local"):
            return True

        if depth == 0 and subject.commonName.endswith(self.cn_suffix):
            return True

        return False


class SecureHTTPServer(HTTPServer):
    def __init__(self, host, port, key_path, cert_path, chained_ca_path, \
            handler_class):
        callback = VerifyCNSuffixCallback(handler_class.rpc.CN_SUFFIX)

        handler_class.sessions = {}
        BaseServer.__init__(self, (host, port), handler_class)
        context = SSL.Context(SSL.SSLv23_METHOD)
        context.use_privatekey_file(key_path)
        context.use_certificate_file(cert_path)
        context.set_verify(SSL.VERIFY_PEER, callback)
        context.load_verify_locations(chained_ca_path)
        self.socket = SSL.Connection(context, \
                socket.socket(self.address_family, self.socket_type))
        self.server_bind()
        self.server_activate()

    def shutdown_request(self, request):
        """Patch for SocketServer shutting down sockets with args"""
        try:
            request.shutdown()
        except socket.error:
            pass 
        self.close_request(request)

