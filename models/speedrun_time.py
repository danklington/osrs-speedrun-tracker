from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, TEXT

Base = declarative_base()

class SpeedrunTime(Base):
    __tablename__ = 'speedrun_time'

    id = Column(Integer, primary_key=True)
    raid_type_id = Column(Integer, nullable=False)
    scale_id = Column(Integer, nullable=True)
    time = Column(Integer, nullable=True)
    players = Column(TEXT, nullable=True)
    screenshot = Column(String(2083), nullable=True)
