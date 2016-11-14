import sys
from backports import lzma

fh = open("test.xz", "w")

compressor = lzma.LZMACompressor()

fh.write(compressor.compress("Hello this is a test\n"))
#fh.write(compressor.flush())
fh.close()


sys.exit(0)


import zmq
import json

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://127.0.0.1:5555")
request = json.dumps({"command": "start_search", "search_id": 1})
socket.send(request)
msg = socket.recv()
print msg
