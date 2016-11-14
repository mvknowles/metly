import os
import tarfile
from io import BytesIO
from threading import Thread


class CommandAndControlThread(Thread):

    def __init__(self, mc):
        Thread.__init__(self)

        self.mc = mc
        self.json_rpc = self.mc.json_rpc

        self.running = False

    def run(self):
#        self.running = True

        #TODO: this is blocking log events, perhaps we need two threads or
        # multiple connection pools?
        while self.mc.stop_event.is_set() == False:
            json_result = self.json_rpc.cc_loop()
            command = "rpc_%s" % json_result["command"]

            args = {}
            if "args" in json_result:
                args = json_result["args"]
            print command

            # call the relevant command and pass json result as kwargs
            getattr(self, command)(**args)

#            print "Running: ",
#            print self.running

        print "Exited cc_loop"

    def rpc_ping(self):
        print "ping"

    def rpc_shutdown(self):
        print "Shutdown command recieved"
#        self.running = False
        self.mc.stop_event.set()

    def rpc_install_version(self, archive=None, version=None):
        bio = BytesIO(archive)
        tf = tarfile.TarFile(fileobj=bio)

        new_path = os.path.join("/usr/local/metly", "metly_%s" % (version))
        if os.path.exists(new_path) == True:
            raise Exception("Path already exists")

        tf.extractall(path=new_path)

    def rpc_stop_collectors(self):
        # stop all the collectors from listening
        self.mc.stop_collectors()

    def rpc_start_version(self, version):
        new_path = os.path.join("/usr/local/metly", "metly_%s" % (version))
        cmd = os.path.join(new_path, "bin", "metlyclient")

        os.spawnl(os.P_DETACH, cmd)

    def rpc_update_sources(self):
        self.mc.stop_log_sources()
        self.mc.start_log_sources()


    def rpc_add_collector(self, *args, **kwargs):
        # initiate the collector and pass the kwargs to it
        pass

#    def stop(self):
#        print "Stopping"
#        self.running = False
        
