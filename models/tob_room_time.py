from db import Base
from db import engine
from db import get_session
from models.raid_type import RaidType
from models.room_time import RoomTime
from sqlalchemy import Table


class TobRoomTime(Base, RoomTime):
    __table__ = Table(
        'tob_room_time', Base.metadata, autoload_with=engine
    )

    def get_raid_type(self) -> RaidType:
        with get_session() as session:
            return session.query(RaidType).filter(
                RaidType.identifier == 'Theatre of Blood'
            ).first()
