import json
import time
import Queue

class Command(object):
    def __init__(self, command, args, retries=3):
        self.command = command
        self.args = args
        self.retries = retries

class CommandAndControl(object):
    def __init__(self):
        self.command_queues = {}

    def get_queue(self, collector_uuid):
        if collector_uuid not in self.command_queues:
            self.command_queues[collector_uuid] = Queue.Queue()

        return self.command_queues[collector_uuid]

    def queue_command(self, collector_uuid, command, **kwargs):
        self.get_queue(collector_uuid).put(Command(command, kwargs))

    def get_next_command(self, request, collector_uuid):
        # TODO: what do we do if it fails... we've removed it from the
        # queue already...
        try:
            command = self.get_queue(collector_uuid).get(True, 10)
            response = {"command": command.command,
                "args": command.args}
            return json.dumps(response)
    
        except Queue.Empty:
            response = {"command": "ping"}
            return json.dumps(response)
            
