from sqlalchemy.orm import relation, backref
from sqlalchemy import ForeignKey, Boolean, Text, DateTime
from sqlalchemy import Table, Column, Integer, String, MetaData, Date, Time

from Base import Base

class LogSourceType(Base):
    __tablename__ = 'log_source_type'

    id = Column(Integer, primary_key=True, autoincrement=False)
    short_name = Column(String(20))
    name = Column(String(255))

    def __init__(self, id, short_name, name):
        self.id = id
        self.short_name = short_name
        self.name = name

    def get_log_source_repr(self, log_source):
        return getattr(self, "get_%s_repr" % self.short_name)(log_source)


    def get_syslog_repr(self, log_source):
        return "%s\n(%s)" % (self.name, log_source.parameters["protocol"])

    def get_filesystem_repr(self, log_source):
        return "%s\n(%s)" % (self.name, log_source.parameters["path"].value)

