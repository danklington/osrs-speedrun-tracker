from db import Base
from db import engine
from db import get_session
from models.player import Player
from models.player_group import PlayerGroup
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
            # Find the players for this speedrun time.
            player_group = session.query(PlayerGroup).filter(
                PlayerGroup.id == self.player_group_id
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

    def get_player_names(self) -> list[str]:
        players = self.get_players()
        player_names = [player.name for player in players]

        return player_names
