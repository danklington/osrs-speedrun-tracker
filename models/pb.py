from db import Session
from models.player import Player
from models.raid_type import RaidType
from models.scale import Scale
from models.speedrun_time import SpeedrunTime
import interactions

class Pb():
    def __init__(
        self, raid_type: str = None,
        scale: int = None,
        runner: interactions.Member = None
    ):
        self._raid_type = raid_type
        self._scale = scale
        self._runner = runner

    @property
    def raid_type(self) -> RaidType:
        session = Session()
        raid = session.query(RaidType).filter(
            RaidType.identifier == self._raid_type
        ).first()
        return raid

    @property
    def scale(self) -> Scale:
        session = Session()
        scale = session.query(Scale).filter(
            Scale.value == self._scale
        ).first()
        return scale

    @property
    def player(self) -> Player:
        session = Session()
        player = session.query(Player).filter(
            Player.discord_id == str(self._runner.id)
        ).first()
        return player

    def get_pb(self) -> SpeedrunTime:
        session = Session()

        # Find the player's personal best
        pb_time = session.query(SpeedrunTime).filter(
            SpeedrunTime.raid_type_id == self.raid_type.id,
            SpeedrunTime.scale_id == self.scale.id,
            SpeedrunTime.players.contains(str(self.player.id))
        ).order_by(SpeedrunTime.time).first()

        return pb_time

    def get_player_names_in_pb(self, pb_time: SpeedrunTime) -> list[str]:
        session = Session()

        all_runners = pb_time.players.split(',')

        # Find the names of the runners.
        runner_names = []
        for runner in all_runners:
            player_obj = session.query(Player).filter(
                Player.id == runner
            ).first()
            runner_names.append(player_obj.name)

        return runner_names
