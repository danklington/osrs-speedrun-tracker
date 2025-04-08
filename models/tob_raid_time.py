from db import Base
from db import engine
from sqlalchemy import Table


class TobRaidTime(Base):
    __table__ = Table(
        'tob_raid_time', Base.metadata, autoload_with=engine
    )
