from db import get_session
from models.player import Player
from models.player_group import PlayerGroup
from models.raid_type import RaidType
from models.scale import Scale
from models.speedrun_time import SpeedrunTime


class RaidTime():
    def __init__(
        self,
        player_id: int,
        scale_id: int,
        speedrun_time_id: int,
        **kwargs
    ):
        self.player_id = player_id
        self.scale_id = scale_id
        self.speedrun_time_id = speedrun_time_id
        for key, value in kwargs.items():
            setattr(self, key, value)

    def get_raid_type(self) -> RaidType:
        """Each child class of RaidTime must implement this method."""

        raise NotImplementedError(
            "This method should be implemented in subclasses."
        )

    def get_scale(self) -> Scale:
        with get_session() as session:
            return session.query(Scale).filter(
                Scale.id == self.get_speedrun_time().scale_id
            ).first()

    def get_players(self) -> list[Player]:
        with get_session() as session:
            speedrun_time = session.query(SpeedrunTime).filter(
                SpeedrunTime.id == self.speedrun_time_id
            ).first()
            if not speedrun_time:
                return []

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

    def get_room_times(self) -> dict[str, str]:
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
                SpeedrunTime.id == self.speedrun_time_id
            ).first()
