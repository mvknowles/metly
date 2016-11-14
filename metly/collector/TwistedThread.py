from threading import Thread
from twisted.internet import reactor

class TwistedThread(Thread):

    def __init__(self, mc):
        Thread.__init__(self)

        self.mc = mc

    def start(self):
        reactor.run()

    def stop(self):
        reactor.stop()
