from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Enum, JSON, ForeignKey
from .raid_type import RaidType  # noqa

Base = declarative_base()

class SpeedrunTimes(Base):
    __tablename__ = 'speedrun_times'

    id = Column(Integer, primary_key=True)
    raid_type_id = Column(Integer, ForeignKey('raid_type.id'), nullable=False)
    scale = Column(Integer, Enum('1', '2', '3', '4', '5'), nullable=True)
    time = Column(Integer, nullable=True)
    players = Column(JSON, nullable=True)
    screenshot = Column(String(2083), nullable=True)
