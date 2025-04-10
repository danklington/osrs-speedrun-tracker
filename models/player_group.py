from db import Base
from db import engine
from sqlalchemy import Table


class PlayerGroup(Base):
    __table__ = Table(
        'player_group', Base.metadata, autoload_with=engine
    )
