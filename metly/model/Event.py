import datetime

class Event(object):

    def __init__(self):
        self.id = None
        self.raw = None
        self.create_dt = datetime.datetime.now()
        self.device_id = None
        self.collector_id = None
        self.device_hostname = None
        self.device_domain_name = None
        self.device_ip_address = None
        self.types = []

    def to_dict(self):
        d = {}
        for item in self.__dict__:
            val = getattr(self, item)
            if val != None:
                d[item] = val

        return d

