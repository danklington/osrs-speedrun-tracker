from db import Base
from db import engine
from sqlalchemy import Table


class RaidType(Base):
    __table__ = Table(
        'raid_type', Base.metadata, autoload_with=engine
    )
