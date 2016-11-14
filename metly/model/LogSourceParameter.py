from sqlalchemy.orm import relation, backref
from sqlalchemy import ForeignKey, Boolean, Text, DateTime
from sqlalchemy import Table, Column, Integer, String, MetaData, Date, Time

from Base import Base

class LogSourceParameter(Base):
    __tablename__ = 'log_source_parameter'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    value = Column(Text, nullable=False)
    log_source_id = Column(Integer, ForeignKey("log_source.id"))
    log_source = relation("LogSource")

    def __init__(self, name, value):
        self.name = name
        self.value = value
