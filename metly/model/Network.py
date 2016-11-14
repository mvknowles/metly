from sqlalchemy.sql import func
from sqlalchemy.orm import relation, backref
from sqlalchemy import ForeignKey, Boolean, Text, DateTime
from sqlalchemy import Table, Column, Integer, String, MetaData, Date, Time

from Base import Base

class Network(Base):
    __tablename__ = "network"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    description = Column(Text)
    customer_id = Column(Integer, ForeignKey("customer.id"))
    customer = relation("Customer")
