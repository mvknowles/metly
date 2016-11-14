from sqlalchemy import ForeignKey, Boolean, Text, DateTime
from sqlalchemy.orm import relation, backref, reconstructor
from sqlalchemy import Table, Column, Integer, String, MetaData, Date, Time

from Base import Base

class WebServer(Base):
    __tablename__ = 'web_server'

    id = Column(Integer, primary_key=True)
    uuid = Column(String(255))
    authorized = Column(Boolean())

#    def __init__(self):
#        self.authorized = False
