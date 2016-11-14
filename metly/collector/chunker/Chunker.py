class Chunker(object):

    def __init__(self, mc):
        self.mc = mc

    def chunk(self):
        raise NotImplemented()

    def send(self, chunk):
        log_source = self.get_calling_object()
        log_source_class_name = log_source.__class__.__name__

        params = {"chunk":chunk, "log_source_class": log_source_class_name, \
                "log_source_name": log_source.name, \
                "log_source_id": log_source.id}

        try:
            self.json_rpc.process_chunk(**params)
        except NotAuthorizedException:
            print "COLLECTOR NOT REGISTERED!"
            self.json_rpc.register()
            self.json_rpc.process_chunk(**params)
