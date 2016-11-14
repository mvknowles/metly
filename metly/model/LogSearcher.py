from sqlalchemy import ForeignKey, Boolean, Text, DateTime
from sqlalchemy.orm import relation, backref, reconstructor
from sqlalchemy import Table, Column, Integer, String, MetaData, Date, Time

from Base import Base
from metly.util import constants

class LogSearcher(Base):
    __tablename__ = 'logsearcher'

    id = Column(Integer, primary_key=True)
    uuid = Column(String(255))

