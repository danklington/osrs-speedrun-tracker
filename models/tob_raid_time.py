from db import Base
from db import engine
from sqlalchemy import Table


class TobRaidTime(Base):
    __table__ = Table(
        'tob_raid_pb', Base.metadata, autoload_with=engine
    )
