from sqlalchemy.orm import relation, backref
from sqlalchemy import ForeignKey, Boolean, Text, DateTime
from sqlalchemy import Table, Column, Integer, String, MetaData, Date, Time

from Base import Base

class Upload(Base):
    __tablename__ = 'upload'

    id = Column(Integer, primary_key=True)
    path = Column(Text())
    original_path = Column(Text())
    finished = Column(Boolean, default=False)
    length = Column(Integer)
    crc = Column(Integer)
    parts = Column(Integer, default=0)
    collector_id = Column(Integer, ForeignKey("collector.id"))
    collector = relation("Collector")
