from db import get_session
from models.player import Player
from models.player_group import PlayerGroup
from models.raid_type import RaidType
from models.scale import Scale
from models.speedrun_time import SpeedrunTime


class RoomTime():
    def __init__(self, player_id: int, scale_id: int, **kwargs):
        self.player_id = player_id
        self.scale_id = scale_id
        for key, value in kwargs.items():
            setattr(self, key, value)

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

    def get_raid_type(self) -> RaidType:
        """Each child class of RoomTime must implement this method."""

        raise NotImplementedError(
            "This method should be implemented in subclasses."
        )

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
            return session.query(SpeedrunTime).join(
                PlayerGroup,
                SpeedrunTime.player_group_id == PlayerGroup.id
            ).filter(
                SpeedrunTime.raid_type_id == self.get_raid_type().id,
                SpeedrunTime.scale_id == self.get_scale().id,
                PlayerGroup.player_id == self.get_player().id
            ).order_by(SpeedrunTime.time).first()

    def update_room_times(
        self, new_room_times: dict[str, str]
    ) -> dict[str, str]:
        before_after = {}

        for room, new_time in new_room_times.items():
            old_time = getattr(self, room, None)
            if old_time is not None and (new_time < old_time):
                setattr(self, room, new_time)
                before_after[room] = (old_time, new_time)

        return before_after
