from sqlalchemy import ForeignKey, Boolean, Text, DateTime
from sqlalchemy.orm import relation, backref, reconstructor
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy import Table, Column, Integer, String, MetaData, Date, Time

from Base import Base

class LogSource(Base):
    __tablename__ = 'log_source'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    collector_id = Column(Integer, ForeignKey("collector.id"))
    collector = relation("Collector")
    customer_id = Column(Integer, ForeignKey("customer.id"))
    customer = relation("Customer")
    log_source_type_id = Column(Integer, ForeignKey("log_source_type.id"))
    log_source_type = relation("LogSourceType")

    parameters = relation("LogSourceParameter", \
            collection_class=attribute_mapped_collection("name"),
            cascade="all, delete-orphan")

    def __repr__(self):
        return self.log_source_type.get_log_source_repr(self)
