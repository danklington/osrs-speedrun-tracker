from db import Base
from db import engine
from sqlalchemy import Table


class TobRoomTime(Base):
    __table__ = Table(
        'tob_room_pb', Base.metadata, autoload_with=engine
    )
