import re
import math
import datetime
import sqlalchemy
#import dateutil.parser

from db import db
from Parser import Parser
from metly.util.log import log
from metly.util import syslogpri
from metly.model.Event import Event
from metly.model.Device import Device
from metly.exception.ParseException import ParseException

class LineParser(Parser):

    SUPPORTED_FORMATS = []

    def __init__(self, customer, log_writer):
        Parser.__init__(self, customer, log_writer)
        self.line = None
        self.buf = ""

    def parse(self, data, buf, buffered=False):
        if buffered == True:
            self.buf += data["event"]["raw"]
            for line in self.buf.splitlines(True):
                sline = line.strip()
                if len(sline) != len(line):
                    # this means we have a line that was terminated with a cr
                    # or crlf
                    data["event"]["raw"] = sline
                    self.parse_line(data)
                else:
                    # we have an incomplete line
                    return
        else:
            self.parse_line(data)


    def cmatch(self, regex):
        """Consuming match.  If we match the regex, we take that portion away"""

        print "Attempting match to %s" % regex
        match = re.match(regex, self.line)

        if match != None:
            self.line = self.line[match.end():]

        if match == None:
            raise ParseException("Could not parse.  Regex: %s\nLine:%s" % \
                    (regex, self.line))

        return match


