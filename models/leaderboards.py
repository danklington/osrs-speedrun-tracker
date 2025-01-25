from db import Session as session
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
        raid_type = session.query(RaidType).filter(
            RaidType.identifier == self._raid_type
        ).first()
        return raid_type

    @property
    def scale(self) -> Scale:
        scale = session.query(Scale).filter(
            Scale.value == self._scale
        ).first()
        return scale

    def get_leaderboard(self, limit: int = 10) -> list[SpeedrunTime]:
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

    async def display(self):
        from embed import leaderboard_to_embed

        leaderboard = self.get_leaderboard()
        if not leaderboard:
            await self.ctx.send(
                'Placeholder until embed for no leaderboard is made.'
            )
            return

        embed = leaderboard_to_embed(self)
        embed.title = (
            f'{self.raid_type.identifier} '
            f'({self.scale.identifier} scale) leaderboard'
        )

        await self.ctx.send(embed=embed)
