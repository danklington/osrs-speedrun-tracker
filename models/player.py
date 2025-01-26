from db import Base
from db import engine
from sqlalchemy import Table


class Player(Base):
    __table__ = Table(
        'player', Base.metadata, autoload_with=engine
    )
