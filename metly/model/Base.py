import inspect
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

def set_from_dict(self, data):
    for key, value in data.items():
        setattr(self, key, value)

def to_json(self):
    raise Exception("Deprecated")

def to_dict(self):
    d = {}
    for item in dir(self):
        value = getattr(self, item)
        if inspect.ismethod(value) == False and item != None and \
                item.startswith("_") == False and item != "metadata" and \
                type(value).__module__.startswith("metly") == False:
            d[item] = str(value)

    return d

Base.set_from_dict = set_from_dict
Base.to_dict = to_dict
Base.to_json = to_json
