import os
import sys
import json

from metly.exception.NotAuthorizedException import NotAuthorizedException

class JSONRPCClient(object):

    def __init__(self):
        self.cookie = None
        self.pool = None

    def json_rpc_request(self, fn, *args, **kwargs):
        kwargs["function"] = fn

        json_data = json.dumps(kwargs)

        headers = {'Content-Type':'application/json'}
        if self.cookie != None:
            headers["Cookie"] = self.cookie

        response = self.pool.urlopen("POST", "/jsonrpc", \
                headers=headers, body=json_data, preload_content=False)

        return response


    def post_binary_part(self, upload_id, part_number, data):
        """Upload part of a binary file.  JSON call needs to be made to
           fn=upload_start which will return an upload_id
           then this is called repeatedly to upload contents
           then to finish, JSON call fn=upload_finish.
           
           If there's an error, call fn=upload_status"""

        #TODO: how do we tail/append a file?

        # randomly corrupt data for testing purposes
        if random.randint(0,1) == True:
            print "Returning"
            sys.exit(0)

        headers = {}
        if self.cookie != None:
            headers["Cookie"] = self.cookie

        json_data = json.dumps({"part": part_number, \
                "upload_id": str(upload_id), \
                "part_number": str(part_number)})

        fields = {"json_data": json_data, "file": ("data", data)}

        response = self.pool.request_encode_body("POST", "/upload", \
                headers=headers, fields=fields)

        return self.parse_json(response)
        

    def json_rpc(self, fn, *args, **kwargs):

        parse = True
        if "parse" in kwargs and kwargs["parse"] == False:
            del kwargs["parse"]
            parse = False

        response = self.json_rpc_request(fn, *args, **kwargs)

        if "Set-Cookie" in response.headers:
            self.cookie = response.headers["Set-Cookie"].split(";")[0]
            print "Cookie: %s" % self.cookie

        print response.status
        if response.status == 403:
            uuid = response.headers["UUID"]
            raise NotAuthorizedException(uuid)


        if parse == False:
            return response.data

        return self.parse_json(response)


    # this allows json_rpc calls to be called as a function
    def __getattr__(self, attr): #, *args, **kwargs):
        #if hasattr(self, attr):
        #    return attr

        print attr

        # TODO: we should get a list of valid rpc calls so
        # we can raise AttributeError if the FN doesn't exist
        # We could either make it part of the protocol or script
        # something to write a dynamic "header", kind of like WDSL
        def json_rpc_with_arg(*args, **kwargs):
            return self.json_rpc(attr, *args, **kwargs)

        return json_rpc_with_arg


    def parse_json(self, response):
        if len(response.data) == 0:
            return None

        if response.data.lower() == "true":
            return True

        if response.data.lower() == "false":
            return False

        json_data = json.loads(response.data)

        if "error" in json_data:
            error = json_data["error"]
            error_module = __import__("metly.exception.%s" % error, \
                    fromlist=[error])
            error_class = getattr(error_module, error)

            raise error_class()

        return json_data
