from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer

Base = declarative_base()

class CmRaidPbTime(Base):
    __tablename__ = 'cm_raid_pb_time'

    id = Column(Integer, primary_key=True)
    scale_id = Column(Integer, nullable=False)
    speedrun_time_id = Column(Integer, nullable=False)
    tekton = Column(Integer, nullable=True)
    crabs = Column(Integer, nullable=True)
    icedemon = Column(Integer, nullable=True)
    shamans = Column(Integer, nullable=True)
    floor1 = Column(Integer, nullable=True)
    vanguards = Column(Integer, nullable=True)
    thieving = Column(Integer, nullable=True)
    vespula = Column(Integer, nullable=True)
    tightrope = Column(Integer, nullable=True)
    floor2 = Column(Integer, nullable=True)
    guardians = Column(Integer, nullable=True)
    vasa = Column(Integer, nullable=True)
    mystics = Column(Integer, nullable=True)
    muttadiles = Column(Integer, nullable=True)
    floor3 = Column(Integer, nullable=True)
    olmmagehandphase1 = Column(Integer, nullable=True)
    olmphase1 = Column(Integer, nullable=True)
    olmmagehandphase2 = Column(Integer, nullable=True)
    olmphase2 = Column(Integer, nullable=True)
    olmphase3 = Column(Integer, nullable=True)
    olmhead = Column(Integer, nullable=True)
    olm = Column(Integer, nullable=True)
    completed = Column(Integer, nullable=True)
