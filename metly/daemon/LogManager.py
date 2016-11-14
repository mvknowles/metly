import datetime
import threading
import sqlalchemy

from metly.util.log import log
from metly.model.Event import Event
from metly.model.Device import Device
from metly.model.Customer import Customer
from metly.model.Collector import Collector
from metly.model.LogSource import LogSource
from metly.daemon.JSONLogWriter import JSONLogWriter
from metly.exception.CollectorNotRegisteredException \
        import CollectorNotRegisteredException

from db import db
#from storage import MySQLStorage

#TODO: this is untidy
from parsers.Parser import Parser
from parsers.SquidParser import SquidParser
from parsers.SyslogParser import SyslogParser

class LogManager(object):
    """This class is responsible for taking a raw log message and turning it
       into a nicely structured event, ready for storage in whatever engine
       we see fit."""

    # TODO: move this shit elsewhere
    FORMATS = {"squid": SquidParser, "syslog": SyslogParser}

    def __init__(self, daemon_uuid, command_and_control, log_path):
        self.command_and_control = command_and_control

        self.log_writer = JSONLogWriter(daemon_uuid, log_path)
        self.session = None
        self.parsers = {}
        # collectors, indexed by UUID
        self.collectors = None

        self.reload_cache()

    def log(self, data, collector_uuid):
        log_source_id = int(data["log_source_id"])
        log_source = self.log_sources[log_source_id]
        data["log_source_name"] = log_source.name

        # load collector into session
        session = db.Session()
        try:
            session.add(log_source)
            collector = log_source.collector
        finally:
            session.close()

        # check that the log source is actually owned by the customer
        if collector.uuid != collector_uuid:
            raise Exception("Security exception")

        parser = self.get_parser(log_source_id)
        parser.parse_line(data)

    def update_log_source(self, log_source_id, collector_uuid):
        session = db.Session()

        try:
            log_source = session.query(LogSource)\
                    .filter(LogSource.id==log_source_id).one()

            self.log_sources[log_source.id] = log_source
            format_name = log_source.parameters["format"].value
            #self.parsers[log_source.id] = Parser.new(format_name)
            self.parsers[log_source.id] = self.new_parser(log_source)
        finally:
            session.close()

        # notify the collector that it's changed
        self.command_and_control.queue_command(collector_uuid, "update_sources")


    def reload_cache(self):
        session = db.Session()
        self.log_sources = {}
        try:
            for log_source in session.query(LogSource).all():
                log(2, "Initialising log source:")
                log(2, "Customer: %s, Source Name: %s, Format: %s" % \
                        (log_source.customer.name, log_source.name, \
                        log_source.parameters["format"].value))
                self.log_sources[log_source.id] = log_source
                self.parsers[log_source.id] = self.new_parser(log_source)
        finally:
            session.close()


    def get_parser(self, log_source_id):

#        if log_source_id not in self.parsers:
#            self.parsers[log_source_id] = LineParser(customer, \
#                    self.log_writer)

        return self.parsers[log_source_id]


    def new_parser(self, log_source):
        return SyslogParser(log_source.customer, self.log_writer)
#        format_name = log_source.parameters["format"].value
#        return self.FORMATS[format_name](log_source.customer, self.log_writer)


#TODO: This doesn't seem to get called from anywhere.....

#    def get_collector(self, collector_uuid):
#        try:
#            # Look up the collector object from the DB based on it's certificate
#            log("Message from collector UUID: %s" % collector_uuid, 3)
#            collector = self.session.query(Collector)\
#                    .filter(Collector.uuid==collector_uuid).one()
#            log("Collector found with id %d" % collector.id, 5)
#
#            return collector
#
#        except sqlalchemy.orm.exc.NoResultFound:
#            log("Event from unregisted collector: %s (%s)" % \
#                    (collector_uuid, host), 1)
#            raise CollectorNotRegisteredException()

#TODO: This doesn't seem to get called from anywhere.....

#    def get_customer(self, customer_id):
#        customer = self.session.query(Customer)\
#                .filter(Customer.id==customer_id)\
#                .one()
#
#        return customer



