from db import Base
from db import Session as session
from db import engine
from sqlalchemy import Table


class CmRaidPbTime(Base):
    __table__ = Table(
        'cm_raid_pb_time', Base.metadata, autoload_with=engine
    )

    def __init__(self, scale_id: int, speedrun_time_id: int):
        self.raid = session.query(CmRaidPbTime).filter(
            CmRaidPbTime.scale_id == scale_id,
            CmRaidPbTime.speedrun_time_id == speedrun_time_id
        ).first()
