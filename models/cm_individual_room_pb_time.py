from db import Base
from db import Session as session
from db import engine
from sqlalchemy import Table


class CmIndividualRoomPbTime(Base):
    __table__ = Table(
        'cm_individual_room_pb_time', Base.metadata, autoload_with=engine
    )

    def __init__(self, scale_id: int, player_id: int):
        self.raid = session.query(CmIndividualRoomPbTime).filter(
            CmIndividualRoomPbTime.scale_id == scale_id,
            CmIndividualRoomPbTime.player_id == player_id
        ).first()
