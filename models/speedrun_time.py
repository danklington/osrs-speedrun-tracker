from db import Base
from db import engine
from sqlalchemy import Table


class SpeedrunTime(Base):
    __table__ = Table(
        'speedrun_time', Base.metadata, autoload_with=engine
    )
