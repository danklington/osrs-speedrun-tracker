from db import Base
from db import engine
from sqlalchemy import Table


class TobRoomTime(Base):
    __table__ = Table(
        'tob_room_time', Base.metadata, autoload_with=engine
    )
