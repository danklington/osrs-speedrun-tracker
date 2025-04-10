from db import get_session
from models.player import Player
from models.player_group import PlayerGroup
from models.raid_type import RaidType
from models.scale import Scale
from models.speedrun_time import SpeedrunTime
from sqlalchemy import func


class Leaderboards():
    def __init__(self, raid_type: str = None, scale: int = None):
        self._raid_type = raid_type
        self._scale = scale

    def get_raid_type(self) -> RaidType:
        with get_session() as session:
            return session.query(RaidType).filter(
                RaidType.identifier == self._raid_type
            ).first()

    def get_scale(self) -> Scale:
        with get_session() as session:
            return session.query(Scale).filter(
                Scale.value == self._scale
            ).first()

    def get_players(self, speedrun_time: SpeedrunTime) -> list[Player]:
        with get_session() as session:
            # Find the players for this speedrun time.
            player_group = session.query(PlayerGroup).filter(
                PlayerGroup.id == speedrun_time.player_group_id
            ).all()
            if not player_group:
                return []

            # Find the players in the player group.
            players = []
            for grouped_player in player_group:
                player = session.query(Player).filter(
                    Player.id == grouped_player.player_id
                ).first()
                if player:
                    players.append(player)

            return players

    def get_leaderboard(self, limit: int = 10) -> list[SpeedrunTime]:
        with get_session() as session:
            subquery = session.query(
                SpeedrunTime.player_group_id,
                func.min(SpeedrunTime.time).label('best_time')
            ).filter(
                SpeedrunTime.raid_type_id == self.get_raid_type().id,
                SpeedrunTime.scale_id == self.get_scale().id
            ).group_by(SpeedrunTime.player_group_id).subquery()

            leaderboards = session.query(SpeedrunTime).join(
                subquery,
                (SpeedrunTime.player_group_id == subquery.c.player_group_id) &
                (SpeedrunTime.time == subquery.c.best_time)
            ).order_by(SpeedrunTime.time).limit(limit).all()

            return leaderboards
