from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

Base = declarative_base()

class RaidType(Base):
    __tablename__ = 'raid_type'

    id = Column(Integer, primary_key=True)
    identifier = Column(String(50), nullable=False)
