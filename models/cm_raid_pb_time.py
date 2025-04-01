from db import Base
from db import engine
from sqlalchemy import Table


class CmRaidPbTime(Base):
    __table__ = Table(
        'cm_raid_pb_time', Base.metadata, autoload_with=engine
    )
