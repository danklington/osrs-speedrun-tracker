from db import Session as session
from models.player import Player
from models.raid_type import RaidType
from models.scale import Scale
from models.speedrun_time import SpeedrunTime
import interactions

class Pb():
    def __init__(
        self,
        ctx: interactions.SlashContext,
        raid_type: str = None,
        scale: int = None,
        runner: interactions.Member = None
    ):
        self.ctx = ctx
        self._raid_type = raid_type
        self._scale = scale
        self._runner = runner

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

    @property
    def player(self) -> Player:
        player = session.query(Player).filter(
            Player.discord_id == str(self._runner.id)
        ).first()
        return player

    def get_pb(self) -> SpeedrunTime:
        # Find the player's personal best
        pb_time = session.query(SpeedrunTime).filter(
            SpeedrunTime.raid_type_id == self.raid_type.id,
            SpeedrunTime.scale_id == self.scale.id,
            SpeedrunTime.players.contains(str(self.player.id))
        ).order_by(SpeedrunTime.time).first()

        return pb_time

    def get_player_names_in_pb(self) -> list[str]:
        pb_time = self.get_pb()
        all_runners = pb_time.players.split(',')

        # Find the names of the runners.
        runner_names = []
        for runner in all_runners:
            player_obj = session.query(Player).filter(
                Player.id == runner
            ).first()
            runner_names.append(player_obj.name)

        return runner_names

    async def display(self):
        from embed import pb_to_embed

        if not self.player:
            await self.ctx.send(
                'Placeholder until embed for no player is made.'
            )
            return

        pb = self.get_pb()
        if not pb:
            await self.ctx.send(
                'Placeholder until embed for no PB is made.'
            )
            return

        embed = pb_to_embed(self)

        if pb.screenshot:
            screenshot = interactions.File(f'attachments/{pb.screenshot}')
            await self.ctx.send(embed=embed, files=[screenshot])
            return

        # If there is no screenshot, send the embed without a file.
        else:
            await self.ctx.send(embed=embed)
            return
