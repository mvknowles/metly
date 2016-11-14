from sqlalchemy.sql import func
from sqlalchemy.orm import relation, backref, relationship
from sqlalchemy import ForeignKey, Boolean, Text, DateTime
from sqlalchemy import Table, Column, Integer, String, MetaData, Date, Time

from Base import Base

class Search(Base):
    __tablename__ = 'search'

    class Status(object):
        QUEUED, RUNNING, DONE = range(3)


    class QueryType(object):
        TEXT, SQL, REGEX, HBASE = range(4)

    id = Column(Integer, primary_key=True)
    title = Column(String(255))
    expression = Column(Text())
    user_id = Column(Integer, ForeignKey("user.id"))
    user = relation("User")
    customer_id = Column(Integer, ForeignKey("customer.id"))
    customer = relation("Customer")
    external_id = Column(String(255))
    description = Column(Text())
    create_dt = Column(DateTime(), default=func.now())
    results_uri = Column(String(2000))
    status = Column(Integer())
    query_type = Column(Integer())
    start_dt = Column(DateTime())
    finish_dt = Column(DateTime())
    count = Column(Integer)
    field_list = Column(Text())
