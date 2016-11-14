from sqlalchemy.sql import func
from sqlalchemy.orm import relation, backref
from sqlalchemy import ForeignKey, Boolean, Text, DateTime
from sqlalchemy import Table, Column, Integer, String, MetaData, Date, Time

from Base import Base

class RootCAFile(Base):
    __tablename__ = 'rootcafile'

    filename = Column(String(255), primary_key=True)
    contents = Column(String(10000))

    def __init__(self, filename, contents):
        self.filename = filename
        self.contents = contents
