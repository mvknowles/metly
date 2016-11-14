import os
import sys
import ssl
import json
import time
import uuid
import urllib
import inspect
import urllib2
import urllib3
import argparse
import threading
import ConfigParser
#from twisted.internet import reactor
from urllib3.connectionpool import HTTPSConnectionPool

sys.path.append(".")
import logsource
from metly.util.log import log
from FileUploader import FileUploader
from metly.util.CertUtil import CertUtil
from metly.util.JSONRPCClient import JSONRPCClient
from CommandAndControlThread import CommandAndControlThread
from metly.exception.CollectorNotRegisteredException \
         import CollectorNotRegisteredException
from metly.exception.NotAuthorizedException import NotAuthorizedException

from logsource.SyslogLogSource import SyslogLogSource
from logsource.FilesystemLogSource import FilesystemLogSource

class Args(object):
    pass

class MetlyClient(object): #JSONRPCClient):

    DEFAULT_CONFIG_DIR = "/etc/metly"
    DEFAULT_CONFIG_FILE = "collector.conf"
    DEFAULT_SOURCES_CONFIG_FILE = "sources.conf"

    DEFAULT_SUBJECT = ("/C=AU/ST=New South Wales/L=Sydney/O=Metly/"
            "OU=Metly Default Client/CN=%s/"
            "emailAddress=support@metly.com.au")

    ERR_FILES_MISSING = "The following files do not exist: %s"
    ERR_CORR_FILE_MSSING = "Could not find the corresponding %s file for %s"

    HTTP_POOL_TIMEOUT = 600
    MAX_DAEMON_CONNECTIONS = 20

    LOG_SOURCE_CLASSES = {
            "syslog": SyslogLogSource,
            "filesystem": FilesystemLogSource
    }

    def __init__(self):
        self.ssl_context = None
        self.log_sources = {}
        self.cookie = None
        self.log_source_classes = {}
        self.stop_event = threading.Event()


    def main(self):

        self.args = Args()
        self.parse_arguments()

        # use local user dotfiles if they exist


        local_config_dir = os.path.join(os.environ["HOME"], ".metly")
        if os.path.exists(local_config_dir):
            self.args.config_path = os.path.join(local_config_dir, \
                    "collector.conf")
            self.args.sources_config_path = os.path.join(local_config_dir, \
                    "sources.conf")

        if os.path.exists(self.args.config_path) == False:
            log(0, "Couldn't find config file:", self.args.config_path)
            sys.exit(1)

        if os.path.exists(self.args.sources_config_path) == False:
            log(0, "Couldn't find sources config file:", \
                    self.args.sources_config_path)
            sys.exit(1)

        self.config = ConfigParser.RawConfigParser()
        self.config.read(self.args.config_path)

        self.working_dir = self.config.get("main", "working_dir")
        self.server_host = self.config.get("server", "host")
        self.server_port = self.config.get("server", "port")
        self.ca_cert_path = os.path.join(self.working_dir, "ca.crt")
        self.cert_path = os.path.join(self.working_dir, "collector.crt")
        self.key_path = os.path.join(self.working_dir, "collector.key")

        self.json_rpc = JSONRPCClient()
        print type(self.json_rpc)

        #TODO: all this pool logic should go in JSONRPCClient, as we repeat
        #all this in the webserver
#        self.json_rpc.pool = self.pool

        # do we have a ca certificate, key and cert?
        if os.path.exists(self.ca_cert_path) == False or \
                os.path.exists(self.cert_path) == False or \
                os.path.exists(self.key_path) == False:

            # request it from the server
            # don't validate the server certificate as we don't have the ca yet
            # this is obviously opportunistic encryption
            urllib3.disable_warnings()

            # temporary pool without client cert
            self.pool = HTTPSConnectionPool(self.server_host, \
                    port=self.server_port, cert_reqs="CERT_NONE", \
                    assert_hostname=False, timeout=self.HTTP_POOL_TIMEOUT, \
                    maxsize=self.MAX_DAEMON_CONNECTIONS)
       
            #TODO this is bonkers
            self.json_rpc.pool = self.pool
            self.request_cert()
            self.start_pool()
            json_result = self.json_rpc.register()
            uuid = json_result["uuid"]
            print "Collector UUID: %s" % (uuid)

        else:
            self.start_pool()


        try:
            json_result = self.json_rpc.get_server_info()
            server_version = json_result["server_version"]
            print "Server version: %s" % (server_version)
        except NotAuthorizedException, ex:
            self.json_rpc.register()
            sys.stderr.write("Collector not authorized. UUID: %s\n" % \
                    ex.uuid)
            sys.exit(1)

        self.file_uploader = FileUploader(self)
        self.update_config()
#        self.start_log_sources()
        self.start_cc_thread()
        print "Entering run loop"
        while self.stop_event.is_set() == False:
            try:
                time.sleep(0.5)
            except KeyboardInterrupt:
                break

#        print "Shutting down C&C"
#        self.stop_cc_thread()
        print "Shutting down Threads"
        self.stop_event.set()
        self.pool.close()

    def start_cc_thread(self):
        self.cc = CommandAndControlThread(self)
        self.cc.start()

#    def stop_cc_thread(self):
#        print "cc stop"
#        self.cc.stop()
#        print "pool stop"


    def update_config(self):
        json_result = self.json_rpc.get_sources_config(parse=False)
        print "New config:"
        print json_result

        fh = open(self.args.sources_config_path, "w")
        fh.write(json_result)
        fh.close()

        self.stop_log_sources()
        self.start_log_sources()


    def start_log_sources(self):

        print self.args.sources_config_path
        fh = open(self.args.sources_config_path, "r")
        config = json.loads(fh.read())
        fh.close()

        for lsc in config:

            clazz = self.get_class(lsc["log_source_type"])
            log_source = clazz(self)
            log_source.name = lsc["name"]
            log_source.log_source_id = int(lsc["id"])

            for param_name, param_value in lsc["parameters"].items():
                setattr(log_source, param_name, param_value)

            self.log_sources[log_source.log_source_id] = log_source

        for key, log_source in self.log_sources.items():
            print "Starting %s (%s)" % (log_source.name, \
                    log_source.__class__.__name__)
            log_source.start()


    def stop_log_sources(self):
        for key, log_source in self.log_sources.items():
            log_source.stop()
            del log_source[key]



    def start_pool(self):
        self.pool = HTTPSConnectionPool(self.server_host, \
                port=self.server_port, cert_reqs="CERT_REQUIRED", \
                key_file=self.key_path, cert_file=self.cert_path, \
                ca_certs=self.ca_cert_path, assert_hostname=False)

        self.json_rpc.pool = self.pool


    def request_cert(self):

        json_result = self.json_rpc.get_cn()
        cn = json_result["cn"]

        cert_util = CertUtil()
        csr = CertUtil.create_csr(self.DEFAULT_SUBJECT % (cn), self.key_path)

        json_result = self.json_rpc.sign_csr(csr=csr)
        cert_fh = open(self.cert_path, "w")
        cert_fh.write(json_result["certificate"])
        cert_fh.close()

        json_result = self.json_rpc.get_ca_cert()
        ca_cert_fh = open(self.ca_cert_path, "w")
        ca_cert_fh.write(json_result["ca_certificate"])
        ca_cert_fh.close()

        # check a proper secure connection
        self.start_pool()


    def import_log_source_class(self, class_name):
        """Dynamically load log_sources"""

        mod_name = "logsource.%s" % (class_name)

        mod = __import__(mod_name, fromlist=[mod_name])
        clazz = getattr(mod, class_name)

        return clazz


    def get_class(self, log_source_type):
        return self.LOG_SOURCE_CLASSES[log_source_type]
#        if class_name not in self.log_source_classes:
#            clazz = self.import_log_source_class(class_name)
#            self.log_source_classes[clazz.NAME] = clazz
#        else:
#            clazz = self.log_source_classes[]
        

    def parse_arguments(self):
        parser = argparse.ArgumentParser(description="Metly Client")

        parser.add_argument("-c", "--conf", dest="config_path",
                required=False, default=self.DEFAULT_CONFIG_DIR, \
                help="The configuration file to use")

#        parser.add_argument("-sc", "--sources-conf", dest="sources_config_path",
#                required=False, default=self.DEFAULT_SOURCES_CONFIG_PATH, \
#                help="The sources configuration file to use")

        parser.add_argument("-d", "--devel", dest="devel_mode",
                required=False, action="store_true", \
                help="Developer mode")

        parser.parse_args(namespace=self.args)

    def get_calling_object(self):
        stack = inspect.stack()
        return stack[2][0].f_locals["self"] #.__class__.__name__
