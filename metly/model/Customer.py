import re
import uuid
from sqlalchemy.orm import relation, backref
from sqlalchemy import ForeignKey, Boolean, Text, DateTime
from sqlalchemy import Table, Column, Integer, String, MetaData, Date, Time

from Base import Base

class Customer(Base):
    __tablename__ = 'customer'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    short_name = Column(String(20))
    uuid = Column(String(36))

    collectors = relation("Collector", cascade="delete")
    searches = relation("Search", cascade="delete")
    devices = relation("Device", cascade="delete")
    networks = relation("Network", cascade="delete")

    def __init__(self, name, short_name):
        self.name = name
        self.short_name = short_name
        # the UUID is used for phoenix multi-tenancy (i.e. making it hard to
        # guess)
        self.uuid = str(uuid.uuid1())

    def get_safe_short_name(self):
        return re.sub("\W", "", self.short_name)

