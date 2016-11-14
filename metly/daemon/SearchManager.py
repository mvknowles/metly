import os
import sys
import zmq
import time
import json
import datetime
from threading import Thread

from metly.util.log import log
from metly.model.Search import Search

from db import db
from LogReader import LogReader
from SQLParser import SQLParser

class SearchThread(Thread):

#    def __init__(self, log_path, socket, search_id):
    def __init__(self, log_path, search_id):
        Thread.__init__(self)

        self.running = None
        self.log_path = log_path
#        self.socket = socket

        self.session = db.Session()
        self.search = self.session.query(Search).get(search_id)
        self.customer = self.search.customer

        # we open the result file first to prevent race conditions

        result_path = os.path.join(self.log_path, \
                self.search.customer.get_safe_short_name(), "search", \
                "%d.txt" % self.search.id)

        print "Opened result file %s" % result_path
        result_dir = os.path.dirname(result_path)
        if os.path.exists(result_dir) == False:
            os.makedirs(result_dir)

        self.fh = open(result_path, "w")

        # parse the expression before we begin so we can return an
        # exception if need be
        sql_parser = SQLParser()
        self.sql_expression = sql_parser.parse(self.search.expression)
        field_list = self.sql_expression.select.field_list.to_list()
        self.search.field_list = json.dumps(field_list)
        self.update_search()

        self.session.close()

    def stop(self):
        self.running = False

    def run(self):
        self.running = True

        self.session = db.Session()
        self.session.add(self.search)
        self.session.add(self.customer)
        lr = LogReader(self.log_path, self.customer.get_safe_short_name(), \
                self.search.start_dt, self.search.finish_dt)
        self.search.status = Search.Status.RUNNING
        self.search.count = 0
        self.update_search()

        while self.running == True:
            event = lr.next()
            if event == None:
                break

            row = self.sql_expression.evaluate(event) 
            if row != None:
                #TODO: do we restrict the rows here?
                self.fh.write(json.dumps(event))
                self.fh.write("\n")
                self.search.count += 1
                self.update_search()

        self.fh.close()
        self.search.status = Search.Status.DONE
        self.update_search()
        self.session.close()

        print "Done"


    def update_search(self):
        self.session.merge(self.search)
        self.session.commit()
#        self.socket.send("%d %d" % (self.search.id, self.search.count))

class SearchManager(object):

    def __init__(self, log_path):
        self.log_path = log_path
        self.search_threads = []
        context = zmq.Context()
#        self.socket = context.socket(zmq.PUB)
#        self.socket.bind("tcp://*:3333")

    def submit_search(self, search_id):
#        search_thread = SearchThread(self.log_path, self.socket, search_id)
        search_thread = SearchThread(self.log_path, search_id)
        search_thread.start()
        self.search_threads.append(search_thread)

    def stop(self):
        for search_thread in self.search_threads:
            search_thread.stop()

#    def next_page(self, search_id):
#
#        session = db.Session()
#        search = db.query(Search).get(search_id)
#        session.close()
#
#        if search_id in self.sub_sockets:
#            socket = self.sub_sockets[search_id]
#        else:
#            context = zmq.Context()
#            socket = context.socket(zmq.SUB)
#            socket.connect("tcp://localhost:3333")
#            socket.setsockopt(zmq.SUBSCRIBE, str(search_id))
#            self.sub_sockets[search_id] = socket

#        data = socket.recv()
#        topic, message = data.split()
#        count = int(message)
#
#        return count

    def stop_monitor(self, search_id):
        pass
#        self.sub_sockets[search_id].close()
#        del self.sub_sockets[search_id]
