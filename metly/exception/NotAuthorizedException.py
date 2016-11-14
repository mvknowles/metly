class NotAuthorizedException(Exception):
    def __init__(self, uuid):
        self.uuid = uuid
