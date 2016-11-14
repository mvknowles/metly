log_level = 10

import sys

def log(*args, **kwargs):
    message = None
    level = 0

    # see if we've got a log level
    if len(args) >= 2:

        if type(args[0]) == int:
            level = args[0]
            message = " ".join(args[1:])
        elif type(args[-1]) == int:
            level = args[-1]
            message = " ".join(args[:-1])

    if message == None:
        message = " ".join(args)

    if level <= log_level:
        sys.stderr.write("%s\n" % (message))
