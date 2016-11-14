import socket

from LogSource import LogSource

class SyslogLogSource(LogSource):

    NAME = "syslog"

    def __init__(self, mc):
        LogSource.__init__(self, mc)
        self.listen = "0.0.0.0"

    def start(self):
        if self.protocol != "udp":
            raise Exception("TCP not done yet")

        self.port = 5514

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self.listen, int(self.port)))
    
        while self.is_running() == True:
            data, addr = sock.recvfrom(4096)

            event = {"raw": data}
            self.mc.json_rpc.log(log_source_id=self.log_source_id, event=event)
