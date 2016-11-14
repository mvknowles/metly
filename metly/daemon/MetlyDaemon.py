import os
import re
import sys
import time
import uuid
import shutil
import twisted
import argparse
import sqlalchemy
import ConfigParser
from threading import Thread
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from M2Crypto import X509 

sys.path.append(".")
from metly.util.log import log
from metly.daemon.db import db
from metly.util import constants
from metly.daemon.config import config
from metly.daemon.WebRPC import WebRPC
from metly.util.CertUtil import CertUtil
from metly.model.RootCAFile import RootCAFile
from metly.daemon.LogManager import LogManager
from metly.daemon.CollectorRPC import CollectorRPC
from metly.daemon.SearchManager import SearchManager
from metly.daemon.JSONRequestHandler import JSONRequestHandler
from metly.daemon.SecureHTTPServer import SecureHTTPServer
from metly.daemon.CommandAndControl import CommandAndControl
from metly.util.CertificateAuthority import CertificateAuthority


class ConfigException(Exception):
    pass

class Args(object):
    pass

class WebHandler(JSONRequestHandler):
    pass

class CollectorHandler(JSONRequestHandler):
    pass

class SecureHTTPServerThread(Thread):

    def __init__(self, server):
        Thread.__init__(self)
        self.server = server

    def run(self):
        self.server.serve_forever()

    def stop(self):
        self.server.shutdown()


class MetlyDaemon(object):

    DEFAULT_SUBJECT_PREFIX=(
            "/C=AU/ST=New South Wales/L=Sydney/O=Metly/")

    DEFAULT_CA_SUBJECT = (
            "%sOU=Metly Default CA/"
            "CN=ca.metly.local/"
            "emailAddress=support@metly.com.au") % DEFAULT_SUBJECT_PREFIX

    DEFAULT_SERVER_SUBJECT = (
            "%sOU=Metly Self Signed/CN=localhost/"
            "emailAddress=support@metly.com.au") % DEFAULT_SUBJECT_PREFIX

    ERR_CONFIG_NOT_FOUND = "The config file %s is not found"
    DEFAULT_CA_SKEL_PATH = "/usr/share/metly/ca_skel"


    def main(self):

        #TODO: figure out where the hell this was meant to go
        log_path = "/tmp/metly"

        self.args = Args()
        self.parse_arguments()

#        if self.args.devel == True:
#            import colored_traceback
#            colored_traceback.add_hook(always=True)

        if os.path.exists(self.args.config_path) == False:
            log(self.ERR_CONFIG_NOT_FOUND % (self.args.config_path))
            sys.exit(1)
            

        self.config = ConfigParser.RawConfigParser()
        self.config.read(self.args.config_path)
#        self.init_java_classpath()

        try:
            ca_skel_path = self.config.get("devel", "ca_skel_path")
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            ca_skel_path = self.DEFAULT_CA_SKEL_PATH

        # TODO: move all config items into the singleton called "config".
        # it's defined above and meant to be a global config

        # check to see if the ca key exists
        self.ca_path = self.config.get("main", "ca_path")
        self.auto_cert = self.config.get("main", "auto_cert").upper() == "TRUE"
        self.ca = CertificateAuthority(self.ca_path, ca_skel_path=ca_skel_path)
        self.key_path = self.config.get("main", "key_path")
        self.chained_ca_path = os.path.join(self.ca_path, "chained.ca.crt")
        self.root_ca_path = os.path.join(self.ca_path, "root_ca")
        root_ca_cert_path = os.path.join(self.root_ca_path, "certs", "ca.crt")

        self.key_path = self.config.get("main", "key_path")
        self.cert_path = self.config.get("main", "cert_path")


        db_uri = self.config.get("database", "uri")
        self.open_db(db_uri)
        print "enter db.init"
        try:
            db.init(drop=self.args.drop_db, drop_phoenix=self.args.drop_phoenix)
        except sqlalchemy.exc.OperationalError, ex:
            if str(ex.orig) == "unable to open database file":
                print "Can't open database URI: %s" % db_uri
                sys.exit(0)
            else:
                raise
        print "exit db.init"


        if os.path.exists(self.ca_path) == False:
            # CA not established.  Create it if specified.
            if self.config.get("main", "auto_ca").upper() == "TRUE":
                if os.path.exists(ca_skel_path) == False:
                    log(0, "CA skeleton path cannot be found:", ca_skel_path)
                    sys.exit(1)

                self.create_ca(ca_skel_path)

        # check to see if our server certificate exists
        if os.path.exists(self.key_path) == False:
            if self.auto_cert == True:
                log(5, "creating server cert from ca")
                csr = CertUtil.create_csr(self.DEFAULT_SERVER_SUBJECT, \
                        self.key_path)
                cert = self.ca.sign_csr(csr, extensions="server")

                cert_fh = open(self.cert_path, "w")
                cert_fh.write(cert)
                cert_fh.close()
                
            else:
                sys.stderr.write("Key file not found %s" % self.key_path)


        self.daemon_uuid = self.get_daemon_uuid()

        print "Launching command and control"
        command_and_control = CommandAndControl()


        print "Launching log manager"
        log_manager = LogManager(self.daemon_uuid, command_and_control, \
                log_path)

        print "Launching search manager"
        search_manager = SearchManager(log_path)
#        search_manager.search("select create_dt, raw from iinet_events")

        print "Launching web handler"
        print self.chained_ca_path
        print root_ca_cert_path
        web_rpc = WebRPC(self.ca, root_ca_cert_path, search_manager, \
                log_manager)
        WebHandler.rpc = web_rpc
        web_httpd = SecureHTTPServer("0.0.0.0", 6443, self.key_path, \
                self.cert_path, self.chained_ca_path, WebHandler)
        web_httpd_thread = SecureHTTPServerThread(web_httpd)
        web_httpd_thread.start()


        print "Launcing client handler"

        collector_rpc = CollectorRPC(self.ca, root_ca_cert_path, \
                log_manager, command_and_control)
        CollectorHandler.rpc = collector_rpc
        collector_httpd = SecureHTTPServer("0.0.0.0", 5443, self.key_path, \
                self.cert_path, self.chained_ca_path, CollectorHandler)
        collector_httpd_thread = SecureHTTPServerThread(collector_httpd)
        collector_httpd_thread.start()

        running = True
        while running == True:
            try:
                time.sleep(0.5)
            except KeyboardInterrupt:
                running = False

        log("Stopping web httpd", 3)
        web_httpd_thread.stop()
        log("Stopping collector httpd", 3)
        collector_httpd_thread.stop()
        log("Stopping search manager", 3)
        search_manager.stop()

    def get_daemon_uuid(self):
        # get subject name from server cert
        fh = open(self.ca.ca_cert_path, "r")
        cert_data = fh.read()
        fh.close()

        cert = X509.load_cert_string(cert_data, X509.FORMAT_PEM) 
        uuid = re.search("CN=(.*)\.issuing", str(cert.get_subject())).group(1)

        return uuid




    def open_db(self, db_uri):
        db.engine = create_engine(db_uri, echo=False)
        db.Session = sessionmaker(bind=db.engine)


    def parse_arguments(self):
        parser = argparse.ArgumentParser(description="Metly Daemon")

        parser.add_argument("-c", "--conf", dest="config_path",
                required=False, default=constants.DEFAULT_DAEMON_CONFIG_PATH, \
                help="The configuration file to use")

        parser.add_argument("-d", "--drop-db", dest="drop_db",
                required=False, default=False, action="store_true", \
                help="Drop the database prior to starting")

        parser.add_argument("-dp", "--drop-phoenix", dest="drop_phoenix",
                required=False, default=False, action="store_true", \
                help="Drop the phoenix database prior to starting")

        parser.add_argument("--devel", dest="devel",
                required=False, default=False, action="store_true", \
                help="Development mode")

        parser.parse_args(namespace=self.args)


    def create_ca(self, ca_skel_path):
        # see if the parent CA exists first of all
        session = db.Session()

        shutil.copytree(ca_skel_path, self.ca_path)
        self.root_ca = CertificateAuthority(self.root_ca_path, \
                ca_skel_path=ca_skel_path)

        root_ca_files = session.query(RootCAFile).all()
        if len(root_ca_files) > 0:
            print "Found Root CA, copying to %s" % self.root_ca_path
            os.mkdir(self.root_ca_path)
            for root_ca_file in root_ca_files:
                print "    %s" % root_ca_file.filename
                dirname = os.path.dirname(root_ca_file.filename)
                if os.path.exists(dirname) == False:
                    os.makedirs(dirname)
                fh = open(os.path.join(self.root_ca_path, \
                            root_ca_file.filename),"w")
                fh.write(root_ca_file.contents)
                fh.close()
            print "end file list"

        else:
            print "Didn't find root CA.  Creating"
            print self.DEFAULT_CA_SUBJECT
            self.root_ca.create_ca(self.DEFAULT_CA_SUBJECT)

            for root, dirs, files in os.walk(self.root_ca_path):
                for ca_filename in files:
                    full_ca_filename = os.path.join(root, ca_filename)
                
                    if not os.path.isfile(full_ca_filename):
                        continue
                    fh = open(os.path.join(self.root_ca_path, \
                                full_ca_filename), "r")
                    ca_file = RootCAFile(full_ca_filename, fh.read())
                    fh.close()
                    print "Added %s" % full_ca_filename
                    session.add(ca_file)

        session.commit()

        print "Creating issuing CA"

        # create issuing CA
        ic_uuid = str(uuid.uuid1())
        ic_subject = "%s/OU=Issuing CAs/CN=%s%s" % \
                (self.DEFAULT_SUBJECT_PREFIX, ic_uuid, \
                constants.ISSUING_CERT_CN_SUFFIX)

        issuing_csr = CertUtil.create_csr(ic_subject, self.ca.ca_key_path)
        fh = open(self.ca.ca_cert_path, "w")
        fh.write(self.root_ca.sign_csr(issuing_csr, extensions="v3_ca"))
        fh.close()

        # write a chained cert
        fh = open(self.chained_ca_path, "w")
        fh.write(self.get_chained_issuing_cert())
        fh.close()


    def get_chained_issuing_cert(self):
        begin = "-----BEGIN CERTIFICATE-----"
        end = "-----END CERTIFICATE-----"
        ss = "(%s.*%s)" % (begin, end)

        # intermediate ca cert
        fh = open(self.ca.ca_cert_path, "r")
        issuing_ca_cert = re.search(ss, fh.read(), flags=re.MULTILINE | re.DOTALL).group(1)
        fh.close()

        # root cert
        fh = open(os.path.join(self.ca_path, "root_ca", "certs", "ca.crt"), "r")
        ca_cert = re.search(ss, fh.read(), flags=re.MULTILINE | re.DOTALL).group(1)
        fh.close()

        chained_issuing_cert = "\n".join([ca_cert, issuing_ca_cert])

        return chained_issuing_cert

#if __name__ == "__main__":
#    MetlyDaemon().main()
