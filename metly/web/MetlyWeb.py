#!/usr/bin/env python

import os
import sys
import time
import urllib3
import cherrypy
import argparse
import ConfigParser
from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(".")
from metly.util.log import log
from metly.util.CertUtil import CertUtil
from metly.exception.NotAuthorizedException import NotAuthorizedException

# import all model classes here so relationships are established
from metly.model.Base import Base
from metly.model.User import User
from metly.model.Device import Device
#from metly.model.Search import Search
from metly.model.Customer import Customer
from metly.model.Requestor import Requestor
from metly.model.ServiceRequest import ServiceRequest

from ServerRPC import ServerRPC
from Controller import Controller
from UIRootController import UIRootController

#search_event_table = Table('search_event', Base.metadata,
#        Column('search_id', Integer, ForeignKey('search.id')),
#        Column('event_id', Integer, ForeignKey('event.id'))
#)

class Args(object):
    pass

class MetlyWeb(object):

    DEFAULT_CONFIG_PATH = "/etc/metly/web.conf"

    DEFAULT_WEB_SUBJECT = ("/C=AU/ST=New South Wales/L=Sydney/O=Metly/"
            "OU=MetlyWeb Self Signed/CN=localhost/"
            "emailAddress=support@metly.com.au")

    def __init__(self):
        self.cert_path = None
        self.key_path = None
        self.listen_address = None
        self.listen_port = None
        self.auto_cert = True

 
    def main(self):

        self.args = Args()
        self.parse_arguments()

        if os.path.exists(self.args.config_path) == False:
            log(0, "Couldn't find config file:", self.args.config_path)
            sys.exit(1)

        self.config = ConfigParser.RawConfigParser()
        self.config.read(self.args.config_path)

        self.cert_path = self.config.get("main", "cert_path")
        self.key_path = self.config.get("main", "key_path")
        server_pki_path = self.config.get("server", "pki_path")
        server_rpc_host = self.config.get("server", "host")
        server_rpc_port = self.config.get("server", "port")

        self.listen_address = self.config.get("listen", "address")
        self.listen_port = int(self.config.get("listen", "port"))

        db_uri = self.config.get("database", "uri")

        self.open_db(db_uri)
        self.server_rpc = ServerRPC(server_rpc_host, server_rpc_port, \
                server_pki_path)

        try:
            while True:
                try:
                    self.server_rpc.connect()
                    break
                except urllib3.exceptions.MaxRetryError:
                    log(0, "Couldn't connect to Metly Daemon, retrying")
                    time.sleep(10)

        except NotAuthorizedException, ex:
            self.server_rpc.register()
            sys.stderr.write(("This webserver isn't authorized with Metly" \
                    "Daemon.  UUID: %s\n") % ex.uuid)
            sys.exit(1)

        try:
            self.auto_cert = self.config.get("main", "auto_cert")
            self.auto_cert = self.auto_cert.upper() == "TRUE"
        except ConfigParser.NoOptionError:
            pass

        # check to see if our server certificate exists
        if os.path.exists(self.cert_path) == False or \
                os.path.exists(self.key_path) == False:

            if self.auto_cert == True:
                # create the keypair automatically
                CertUtil.create_self_signed_cert(self.DEFAULT_WEB_SUBJECT, \
                        self.key_path, self.cert_path)

            else:
                log(0, "Server cert or key cert doesn't exist:", \
                        self.cert_path, self.key_path)
                sys.exit(1)

        self.start_ui()

    def open_db(self, db_uri):
        engine = create_engine(db_uri, echo=True)
        Controller.Session = sessionmaker(bind=engine)
        Base.metadata.create_all(engine)


    def start_ui(self):

        server_config= {
            'server.socket_host': self.listen_address,
            'server.socket_port': self.listen_port,

            'server.ssl_module': 'builtin',
            'server.ssl_certificate': self.cert_path,
            'server.ssl_private_key': self.key_path,
        }


        cwd = os.path.dirname(os.path.abspath(__file__))
        static_path = os.path.join(cwd, "html/static")

        global_config = {
                "tools.authenticate.on": True,
                "tools.sessions.on": True
        }

        static_config = {
                'tools.staticdir.on': True,
                'tools.staticdir.dir': static_path
        }

        root_config = {"global": global_config, "/static": static_config}


        cherrypy.config.update(server_config)
        root_controller = UIRootController(self.server_rpc)
        cherrypy.quickstart(root_controller, "/", config=root_config)


    def parse_arguments(self):
        parser = argparse.ArgumentParser(description="Metly Web")

        parser.add_argument("-c", "--conf", dest="config_path",
                required=False, default=self.DEFAULT_CONFIG_PATH, \
                help="The configuration file to use")

        parser.parse_args(namespace=self.args)
