from sqlalchemy.sql import func
from sqlalchemy.orm import relation, backref
from sqlalchemy import Table, Column, Integer, String, MetaData, Date, Time
from sqlalchemy import ForeignKey, Boolean, Text, DateTime, UniqueConstraint

from Base import Base

class Device(Base):
    __tablename__ = "device"

    id = Column(Integer, primary_key=True)
    ip_address = Column(String(15), index=True)
    fqdn = Column(String(255), index=True)
    create_dt = Column(DateTime(), default=func.now())
    customer_id = Column(Integer, ForeignKey("customer.id"))
    customer = relation("Customer")
    update_dt = Column(DateTime())

    network_id = Column(Integer, ForeignKey("network.id"))
    network = relation("Network")

    UniqueConstraint("network_id", "ip_address")
    UniqueConstraint("network_id", "fqdn")
