import os
import time
import json
import uuid

from db import db
from config import config
from metly.model.Search import Search

class SearchPager(object):
    
    def __init__(self, search_id):
        self.search_id = search_id
        self.uuid = str(uuid.uuid4())
        self.line_no = 0

        session = db.Session()
        try:
            search = session.query(Search).get(search_id)

            # open up the results file
            print config.log_path
            print search.customer.get_safe_short_name()
            result_path = os.path.join(config.log_path, \
                    search.customer.get_safe_short_name(), "search", \
                    "%d.txt" % search.id)

            print "SearchPager opening %s" % result_path

            self.fh = open(result_path, "r")

        finally:
            session.close()


    def set_page_info(self, page_number, page_size=20):
        self.page_number = page_number
        self.page_size = page_size
        self.start_x = page_size * (page_number - 1)
        self.finish_x = self.start_x + 20 - 1

        if self.line_no > self.start_x:
            print "Gone backwards, seek-0ing"
            # we've gone backwards, seek to beginning
            self.fh.seek(0)
            self.line_no = 0

    def yield_events(self, timeout=2):
        # the client keeps calling this until they get page_size events

        for line in self.fh:
            if self.line_no >= self.start_x and \
                    self.line_no <= self.finish_x:
                try:
                    data = json.loads(line)
                    print "Yielding %s" % line
                    yield json.loads(line)
                except ValueError:
                    # this catches incomplete lines that haven't been flushed
                    pass

            self.line_no += 1

            # TODO: make sure this is ok
            if self.line_no == self.finish_x:
                return

