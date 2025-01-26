from db import Session as session
from models.player import Player
from models.raid_type import RaidType
from models.scale import Scale
from models.speedrun_time import SpeedrunTime
from models.cm_individual_room_pb_time import CmIndividualRoomPbTime
from models.cm_raid_pb_time import CmRaidPbTime
from util import sync_screenshot_state
from util import ticks_to_time_string
import interactions

class Pb():
    def __init__(
        self,
        ctx: interactions.SlashContext,
        raid_type: str = None,
        scale: int = None,
        runner: list[Player] = None
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
    def players(self) -> list[Player]:
        return self._runner

    def get_pb(self) -> SpeedrunTime:
        # Find the player's personal best
        pb_time = session.query(SpeedrunTime).filter(
            SpeedrunTime.raid_type_id == self.raid_type.id,
            SpeedrunTime.scale_id == self.scale.id,
            SpeedrunTime.players.contains(
                ','.join([str(player.id) for player in self.players])
            )
        ).order_by(SpeedrunTime.time).first()

        return pb_time

    def get_player_names_in_pb(self) -> list[str]:
        players = self.players
        runner_names = [player.name for player in players]

        return runner_names

    def get_all_players_in_pb(self) -> list[Player]:
        pb = self.get_pb()
        players = session.query(Player).filter(
            Player.id.in_([int(player) for player in pb.players.split(',')])
        ).all()

        return players

    async def display(self) -> None:
        from embed import error_to_embed
        from embed import pb_to_embed

        if not self.players:
            embed = error_to_embed(
                'No players found',
                'Could not find player(s) in the database.'
            )
            await self.ctx.send(embed=embed)
            return

        pb = self.get_pb()
        if not pb:
            embed = error_to_embed(
                'No personal best found',
                'Could not find a personal best for this player.'
            )
            await self.ctx.send(embed=embed)
            return

        # Checks if the file exists on the server and sets the screenshot to
        # None if not.
        sync_screenshot_state(pb)

        embed = pb_to_embed(self)

        if pb.screenshot:
            screenshot = interactions.File(f'attachments/{pb.screenshot}')
            await self.ctx.send(embed=embed, files=[screenshot])
            return

        # If there is no screenshot, send the embed without a file.
        else:
            await self.ctx.send(embed=embed)
            return


class CmRaidPb():
    def __init__(
        self,
        ctx: interactions.SlashContext,
        scale: int = None,
        runners: list[Player] = None
    ):
        self.ctx = ctx
        self._scale = scale
        self._runners = runners

    @property
    def raid_type(self) -> RaidType:
        raid_type = session.query(RaidType).filter(
            RaidType.identifier == 'Chambers of Xeric: Challenge Mode'
        ).first()
        return raid_type

    @property
    def scale(self) -> Scale:
        scale = session.query(Scale).filter(
            Scale.value == self._scale
        ).first()
        return scale

    @property
    def players(self) -> list[Player]:
        return self._runners

    @property
    def times_dict(self) -> dict:
        raid_pb_time = self.get_raid_times()

        # Convert the raid times object to a dictionary. Strip out the
        # unnecessary keys.
        times = {
            attr: getattr(raid_pb_time, attr)
            for attr in vars(raid_pb_time)
            if attr not in [
                '_sa_instance_state', 'id', 'scale_id', 'speedrun_time_id'
            ]
        }
        for key, value in times.items():
            times[key] = ticks_to_time_string(value)

        return times

    def get_pb(self) -> SpeedrunTime:
        # Find the players' personal best
        pb_time = session.query(SpeedrunTime).filter(
            SpeedrunTime.raid_type_id == self.raid_type.id,
            SpeedrunTime.scale_id == self.scale.id,
            SpeedrunTime.players.contains(
                ','.join([str(player.id) for player in self.players])
            )
        ).order_by(SpeedrunTime.time).first()

        return pb_time

    def get_raid_times(self) -> CmRaidPbTime:
        pb = self.get_pb()
        raid_times = session.query(CmRaidPbTime).filter(
            CmRaidPbTime.speedrun_time_id == pb.id
        ).first()

        return raid_times

    async def display(self) -> None:
        from embed import error_to_embed
        from embed import pb_cm_raid_to_embed
        from embed import pb_to_embed

        raid_times = self.get_raid_times()
        if not raid_times:
            # The player may have submitted the total time manually instead of
            # using the clipboard so we need to check for it.
            pb = Pb(
                self.ctx,
                raid_type='Chambers of Xeric: Challenge Mode',
                scale=self.scale.value,
                runner=self.players
            )
            if pb.get_pb():
                embed = pb_to_embed(pb)
                await self.ctx.send(embed=embed)
                return

            embed = error_to_embed(
                'No raid times found',
                'Could not find any raid times for this group of players.'
            )
            await self.ctx.send(embed=embed)
            return

        pb = self.get_pb()
        if not pb:
            embed = error_to_embed(
                'No personal best found',
                'Could not find a personal best for this group of players.'
            )
            await self.ctx.send(embed=embed)
            return

        embed = pb_cm_raid_to_embed(self)
        await self.ctx.send(embed=embed)


class CmIndividualRoomPb():
    def __init__(
        self,
        ctx: interactions.SlashContext,
        scale: int = None,
        player: interactions.Member = None
    ):
        self.ctx = ctx
        self._scale = scale
        self._player = player

    @property
    def raid_type(self) -> RaidType:
        raid_type = session.query(RaidType).filter(
            RaidType.identifier == 'Chambers of Xeric: Challenge Mode'
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
            Player.discord_id == str(self._player.id)
        ).first()
        return player

    @property
    def times_dict(self) -> dict:
        room_pb_time = self.get_individual_room_times()

        # Convert the room times object to a dictionary. Strip out the
        # unnecessary keys.
        times = {
            attr: getattr(room_pb_time, attr)
            for attr in vars(room_pb_time)
            if attr not in [
                '_sa_instance_state', 'id', 'scale_id', 'player_id'
            ]
        }
        for key, value in times.items():
            times[key] = ticks_to_time_string(value)

        return times

    def get_pbs(self) -> SpeedrunTime:
        # Find the player's personal best for each room.
        pb_times = session.query(SpeedrunTime).filter(
            SpeedrunTime.raid_type_id == self.raid_type.id,
            SpeedrunTime.scale_id == self.scale.id,
            SpeedrunTime.players.contains(str(self.player.id))
        ).order_by(SpeedrunTime.time).first()

        return pb_times

    def get_individual_room_times(self) -> CmIndividualRoomPbTime:
        room_times = session.query(CmIndividualRoomPbTime).filter(
            CmIndividualRoomPbTime.player_id == self.player.id,
            CmIndividualRoomPbTime.scale_id == self.scale.id
        ).first()

        return room_times

    async def display(self) -> None:
        from embed import error_to_embed
        from embed import pb_cm_individual_room_to_embed

        room_times = self.get_individual_room_times()
        if not room_times:
            message = (
                'Could not find any individual room times for '
                f'{self.player.name} in {self.scale.identifier} scale.'
            )
            embed = error_to_embed(
                'No individual room times found',
                message
            )
            await self.ctx.send(embed=embed)
            return

        embed = pb_cm_individual_room_to_embed(self)
        await self.ctx.send(embed=embed)
