from sqlalchemy import ForeignKey, Boolean, Text, DateTime
from sqlalchemy.orm import relation, backref, reconstructor
from sqlalchemy import Table, Column, Integer, String, MetaData, Date, Time

from Base import Base
from metly.util import constants

class Collector(Base):
    __tablename__ = 'collector'

    id = Column(Integer, primary_key=True)
    uuid = Column(String(255))
    name = Column(String(255))
    location = Column(String(255))
    customer_id = Column(Integer, ForeignKey("customer.id"))
    customer = relation("Customer")

    #TODO: fix all the other cascades that need to be done
    log_sources = relation("LogSource", cascade="delete")

    network_id = Column(Integer, ForeignKey("network.id"))
    network = relation("Network")
