from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

Base = declarative_base()

class Players(Base):
    __tablename__ = 'players'

    id = Column(Integer, primary_key=True)
    name = Column(String(32), nullable=False)
