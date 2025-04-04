from db import Base
from db import engine
from db import get_session
from models.player import Player
from models.raid_type import RaidType
from models.scale import Scale
from sqlalchemy import Table


class SpeedrunTime(Base):
    __table__ = Table(
        'speedrun_time', Base.metadata, autoload_with=engine
    )

    def get_raid_type(self) -> RaidType:
        with get_session() as session:
            return session.query(RaidType).filter(
                RaidType.id == self.raid_type_id
            ).first()

    def get_scale(self) -> Scale:
        with get_session() as session:
            return session.query(Scale).filter(
                Scale.id == self.scale_id
            ).first()

    def get_players(self) -> list[Player]:
        with get_session() as session:
            return session.query(Player).filter(
                Player.id.in_(
                    [
                        int(player_id)
                        for player_id
                        in self.players.split(',')
                    ]
                )
            ).all()

    def get_player_names(self) -> list[str]:
        players = self.get_players()
        player_names = [player.name for player in players]

        return player_names
