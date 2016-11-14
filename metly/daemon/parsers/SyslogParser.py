import re
import math
import datetime
import sqlalchemy
import dateutil.parser

from db import db
from metly.util.log import log
from metly.util import syslogpri
from LineParser import LineParser
from metly.model.Event import Event
from metly.model.Device import Device
from metly.exception.ParseException import ParseException

class SyslogParser(LineParser):

    SUPPORTED_FORMATS = []


    def parse_line(self, data):
        self.event = Event()
        self.line = data["event"]["raw"]
        log_source_name = data["log_source_name"]

        self.parse_syslog_prio()

#        self.add_device_if_new()

        self.log_writer.insert_row(self.customer_short_name, \
                self.event.device_hostname, log_source_name, \
                self.event.to_dict())


    def parse_syslog_prio(self):
        match = self.cmatch("<(\d+)>")

        pri = int(match.group(1))
        facility = math.floor(pri / 8.0)
        severity = pri - (facility * 8)

        facility_name = syslogpri.FACILITY[facility]
        severity_name = syslogpri.SEVERITY[severity]

        self.event.types.append("syslog")
        self.event.severity = int(100.0 * (7.0 - severity) / 7.0)
        self.event.device_severity = "%s.%s" % (severity_name, facility_name)
        self.event.extra_0 = severity
        self.event.extra_0_name = "Severity"
        self.event.extra_1 = facility
        self.event.extra_1_name = "Facility"

        self.parse_syslog()

    def parse_syslog(self):
        process_name = None
        pid = None
        hostname = None

        match = self.cmatch("(.*?): (.*)")
        header = match.group(1)
        message = match.group(2)
        print "parse_syslog:0 header: %s, message: %s" % (header, message)

        # see if we've got the name of the process
        match = re.match("(.*)\s+(\S+)\[(\d+)\]", header)

        if match != None:
            header = match.group(1)
            process_name = match.group(2)
            pid = match.group(3)
            print "parse_syslog:1 header: %s, process_name: %s, pid: %s" % \
                    (header, process_name, pid)
        else:
            match = re.match("(.*)\s+(\S+)", header)
            header = match.group(1)
            process_name = match.group(2)
            print "parse_syslog:2 header: %s, process_name: %s" % \
                    (header, process_name)
            

        match = re.match("(.*)\s+(\S+)", header)
        
        if match != None:
            dt = dateutil.parser.parse(match.group(1))
            self.event.start_time = dt
            self.event.device_hostname = match.group(2)
            self.event.message = message
        else:
            raise ParserException("Can't parse %s" % self.line)
        
