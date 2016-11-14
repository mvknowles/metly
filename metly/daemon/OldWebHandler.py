import zmq
import json

from threading import Thread

class WebHandler(Thread):

    def __init__(self, md):
        Thread.__init__(self)
        self.md = md

    def run(self):
        self.running = True

        context = zmq.Context()
        socket = context.socket(zmq.REP)
        socket.bind("tcp://127.0.0.1:5555")
        poller = zmq.Poller()
        poller.register(socket, zmq.POLLIN)

        while self.running == True:
            if len(poller.poll(1000)) == 0:
                continue
            msg = socket.recv()
            json_request= json.loads(msg)
            fn = json_request["command"]
            result = getattr(self, "json_%s" % (fn))(json_request)
            socket.send(result)

    def stop(self):
        self.running = False

    def json_start_search(self, search_id):
        self.md.search_handler.start_search(search_id)
