import sys
import inspect
import logsource

for name, obj in inspect.getmembers(sys.modules["logsource"]):
    print obj
    if inspect.isclass(obj):
        print "x"
        print obj
