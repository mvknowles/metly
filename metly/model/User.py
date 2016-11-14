from sqlalchemy.orm import relation, backref
from sqlalchemy import ForeignKey, Boolean, Text, DateTime
from sqlalchemy import Table, Column, Integer, String, MetaData, Date, Time

from Base import Base

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(String(52))
    firstname = Column(String(255))
    lastname = Column(String(255))
    email = Column(String(255))
    password = Column(String(255))
    salt = Column(String(255))
    enabled = Column(Boolean())
    su = Boolean()

    customer_id = Column(Integer, ForeignKey("customer.id"))
    customer = relation("Customer")

    def __init__(self):
        self.su = False
