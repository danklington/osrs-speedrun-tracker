from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

Base = declarative_base()

class Scale(Base):
    __tablename__ = 'scale'

    id = Column(Integer, primary_key=True)
    identifier = Column(String(32), nullable=False)
    value = Column(Integer, nullable=False)
