from sqlalchemy.sql import func
from sqlalchemy.orm import relation, backref
from sqlalchemy import ForeignKey, Boolean, Text, DateTime
from sqlalchemy import Table, Column, Integer, String, MetaData, Date, Time

from Base import Base

class ServiceRequest(Base):
    __tablename__ = 'service_request'

    id = Column(Integer, primary_key=True)
    title = Column(String(255))
    user_id = Column(Integer, ForeignKey("user.id"))
    user = relation("User")
    customer_id = Column(Integer, ForeignKey("customer.id"))
    customer = relation("Customer")
    due_date = Column(Date())
    external_id = Column(String(255))
    description = Column(Text())
    create_dt = Column(DateTime(), default=func.now())


#    def set_from_dict(self, data):
#        for key, value in data.items():
#            setattr(self, key, value)
