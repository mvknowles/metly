import os
import re
import json
import datetime

class LogWriter(object):

    def __init__(self, daemon_uuid):
        self.daemon_uuid = daemon_uuid

    def insert_row(self, customer_shortname, host, log_source_name, \
            event_dict, dt=None):
        if dt == None:
            dt = datetime.datetime.now()

        self.impl_insert_row(customer_shortname, host, log_source_name, \
                event_dict, dt)
