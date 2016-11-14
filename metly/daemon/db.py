import re
import sys
#import jpype
#import jaydebeapi
import traceback
#import phoenixdb
import sqlalchemy

from metly.util import hash
from metly.util.log import log
from metly.model.Base import Base
from metly.model.User import User
from metly.model.Device import Device
from metly.model.Search import Search
from metly.model.Network import Network
from metly.model.Customer import Customer
from metly.model.Collector import Collector
from metly.model.Requestor import Requestor
from metly.model.LogSource import LogSource
from metly.model.WebServer import WebServer
from metly.model.LogSourceType import LogSourceType
from metly.model.ServiceRequest import ServiceRequest
from metly.model.LogSourceParameter import LogSourceParameter

from metly.daemon.LogWriter import LogWriter


class Database(object):

    def init(self, drop=False, drop_phoenix=False):
        log("Starting db.init", 2)
        self.init_defaults(drop)
        log("Finished db.init", 2)

    def init_defaults(self, drop):
        log("Initialising defaults", 3)
        if drop == True:
            log("Dropping database", 3)
            Base.metadata.drop_all(db.engine)

        Base.metadata.create_all(db.engine)

        session = db.Session()
        # make sure all our constants exist etc
        if session.query(Requestor).first() != None:
            log("Defaults already initialised", 3)
            session.close()
            return

        session.add(LogSourceType(0, "syslog", "Syslog"))
        session.add(LogSourceType(1, "filesystem", "Filesystem Path"))

        session.add(Requestor("customer"))
        session.add(Requestor("AFP (Australian Federal Police)"))
        session.add(Requestor("NSW Police"))
        session.add(Requestor("Victorian Police"))
        session.add(Requestor("ACC (Australian Crime Comission)"))
        session.add(Requestor("ASIO"))
        session.add(Requestor("DSD"))

        customer = Customer("test", "test")
        network = Network()
        network.name = "Default"
        network.description = "Default"
        session.add(network)
        customer.networks.append(network)
        network = Network()
        network.name = "Intranet"
        network.description = "Intranet"
        session.add(network)
        customer.networks.append(network)
        session.add(customer)
        session.add(Customer("internode", "internode"))
        session.add(Customer("telstra", "telstra"))

        user = User()
        user.username = "mark"
        user.firstname = "Mark"
        user.lastname = "Knowles"
        user.email = "mark@mknowles.com.au"
        user.su = True
        user.customer = customer
        user.enabled = True
        user.salt = hash.new_salt()
        user.password = hash.hash_password("test", user.salt)

        session.add(user)

        session.commit()
        session.close()

        log("Done initialising defaults", 3)



db = Database()


