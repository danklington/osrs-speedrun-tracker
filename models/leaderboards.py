from db import get_session
from models.raid_type import RaidType
from models.scale import Scale
from models.speedrun_time import SpeedrunTime
from sqlalchemy import func
import interactions


class Leaderboards():
    def __init__(
        self,
        ctx: interactions.SlashContext,
        raid_type: str = None,
        scale: int = None
    ):
        self.ctx = ctx
        self._raid_type = raid_type
        self._scale = scale

    @property
    def raid_type(self) -> RaidType:
        with get_session() as session:
            raid_type = session.query(RaidType).filter(
                RaidType.identifier == self._raid_type
            ).first()
            return raid_type

    @property
    def scale(self) -> Scale:
        with get_session() as session:
            scale = session.query(Scale).filter(
                Scale.value == self._scale
            ).first()
            return scale

    def get_leaderboard(self, limit: int = 10) -> list[SpeedrunTime]:
        with get_session() as session:
            # Find the leaderboards.
            subquery = session.query(
                SpeedrunTime.players,
                func.min(SpeedrunTime.time).label('best_time')
            ).filter(
                SpeedrunTime.raid_type_id == self.raid_type.id,
                SpeedrunTime.scale_id == self.scale.id
            ).group_by(SpeedrunTime.players).subquery()

            leaderboards = session.query(SpeedrunTime).join(
                subquery,
                (SpeedrunTime.players == subquery.c.players) &
                (SpeedrunTime.time == subquery.c.best_time)
            ).order_by(SpeedrunTime.time).limit(limit).all()

            return leaderboards
