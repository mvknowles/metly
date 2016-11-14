from threading import Thread

class LogSource(Thread):
    def __init__(self, mc):
        Thread.__init__(self)
        self.mc = mc
        self.json_rpc = mc.json_rpc
        self.name = None
        self.log_source_id = None

    def is_running(self):
        return self.mc.stop_event.is_set() == False

    def sleep(self, sec):
        self.mc.stop_event.wait(sec)

