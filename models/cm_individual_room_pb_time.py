from db import Base
from db import engine
from sqlalchemy import Table


class CmIndividualRoomPbTime(Base):
    __table__ = Table(
        'cm_individual_room_pb_time', Base.metadata, autoload_with=engine
    )
