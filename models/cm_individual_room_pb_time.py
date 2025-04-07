from db import Base
from db import engine
from db import get_session
from models.player import Player
from models.raid_type import RaidType
from models.scale import Scale
from models.speedrun_time import SpeedrunTime
from sqlalchemy import Table


class CmIndividualRoomPbTime(Base):
    __table__ = Table(
        'cm_individual_room_pb_time', Base.metadata, autoload_with=engine
    )

    def get_raid_type(self) -> RaidType:
        with get_session() as session:
            return session.query(RaidType).filter(
                RaidType.identifier == 'Chambers of Xeric: Challenge Mode'
            ).first()

    def get_scale(self) -> Scale:
        with get_session() as session:
            return session.query(Scale).filter(
                Scale.id == self.scale_id
            ).first()

    def get_player(self) -> Player:
        with get_session() as session:
            return session.query(Player).filter(
                Player.id == self.player_id
            ).first()

    def get_individual_room_times(self) -> dict[str, str]:
        from util import ticks_to_time_string

        # Strip out unnecessary keys.
        times = {
            attr: getattr(self, attr)
            for attr in vars(self)
            if attr not in [
                '_sa_instance_state', 'id', 'scale_id', 'speedrun_time_id'
            ]
        }

        # Convert the ticks to a string.
        for key, value in times.items():
            times[key] = ticks_to_time_string(value)

        return times

    def get_speedrun_time(self) -> SpeedrunTime:
        with get_session() as session:
            return session.query(SpeedrunTime).filter(
                SpeedrunTime.raid_type_id == self.get_raid_type().id,
                SpeedrunTime.scale_id == self.get_scale().id,
                SpeedrunTime.players.contains(str(self.get_player().id))
            ).order_by(SpeedrunTime.time).first()
