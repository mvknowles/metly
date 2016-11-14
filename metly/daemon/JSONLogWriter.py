import os
import re
import json
import datetime

from LogWriter import LogWriter

class JSONLogWriter(LogWriter):

    def __init__(self, daemon_uuid, log_path):
        LogWriter.__init__(self, daemon_uuid)
        self.log_path = log_path

    def impl_insert_row(self, customer_shortname, host, log_source_name, \
            event_dict, dt):

        json_event = json.dumps(event_dict, default=self.json_serial)

        log_file_path = self.get_file_path(customer_shortname, host, dt, \
                log_source_name)
        print log_file_path
        print json_event

        log_file_dir = os.path.dirname(log_file_path)
        if os.path.exists(log_file_dir) == False:
            os.makedirs(log_file_dir)
        fh = open(log_file_path, "a")
        fh.write(json_event)
        fh.write("\n")
        fh.close()

    def get_file_path(self, customer_shortname, host, dt, log_source_name):
        # customer/logs/2015-07-01/host/23-uuid.txt
        date_part = datetime.datetime.strftime(dt, "%Y-%m-%d")
        hour_part = datetime.datetime.strftime(dt, "%H")

        filename = "%s.%s.%s.txt" % (hour_part, self.daemon_uuid, \
                log_source_name)
        path = os.path.join(self.log_path, customer_shortname, "logs", \
                date_part, host, filename)

        return path

    def json_serial(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()

        raise TypeError("Type not serializable")
