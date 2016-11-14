from sqlalchemy.orm import relation, backref
from sqlalchemy import ForeignKey, Boolean, Text, DateTime
from sqlalchemy import Table, Column, Integer, String, MetaData, Date, Time

from Base import Base

class Requestor(Base):
    __tablename__ = 'requestor'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))

    def __init__(self, name):
        self.name = name
