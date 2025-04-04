from db import get_session
from models.cm_individual_room_pb_time import CmIndividualRoomPbTime
from models.cm_raid_pb_time import CmRaidPbTime
from models.leaderboards import Leaderboards
from models.player import Player
from models.speedrun_time import SpeedrunTime
from util import ticks_to_time_string
import interactions


EMBED_COLOUR = 0xc1005d


def confirmation_to_embed(title: str, message: str) -> interactions.Embed:
    return interactions.Embed(
        title=':white_check_mark:  ' + title,
        description='### ' + message,
        color=EMBED_COLOUR
    )


def error_to_embed(title: str, error_message: str) -> interactions.Embed:
    return interactions.Embed(
        title=':x:  ' + title,
        description='### ' + error_message,
        color=EMBED_COLOUR
    )


def leaderboard_to_embed(lb_obj: Leaderboards) -> interactions.Embed:
    leaderboard = lb_obj.get_leaderboard()

    output = ''
    emoji_list = [
        ':first_place:', ':second_place:', ':third_place:', ':four:', ':five:',
        ':six:', ':seven:', ':eight:', ':nine:', ':keycap_ten:'
    ]

    with get_session() as session:
        for index, run in enumerate(leaderboard):
            formatted_time = ticks_to_time_string(run.time)
            players = run.players.split(',')
            player_names = []
            for player in players:
                player_obj = session.query(Player).filter(
                    Player.id == player
                ).first()
                player_names.append(player_obj.name)
            player_string = ', '.join(player_names)
            output += emoji_list[index]
            output += f' | `{formatted_time}` - **{player_string}**\n\n'

    return interactions.Embed(
        title=(
            f'{lb_obj.raid_type.identifier} '
            f'({lb_obj.scale.identifier} scale) leaderboard'
        ),
        description=output,
        color=EMBED_COLOUR
    )


def pb_to_embed(speedrun_time: SpeedrunTime) -> interactions.Embed:
    runner_names = speedrun_time.get_player_names()
    formatted_time = ticks_to_time_string(speedrun_time.time)

    output = (
        '### :man_running_facing_right: '
        f'Runner{'s' if speedrun_time.get_scale().value > 1 else ''}:\n'
        f'**{', '.join(runner_names)}**\n\n'
        f'### :clock1: Time:\n'
        f'### `{formatted_time}`'
    )

    embed = interactions.Embed(
        title=(
            f'Team {', '.join(runner_names)}: Personal best for '
            f'{speedrun_time.get_raid_type().identifier} '
            f'({speedrun_time.get_scale().identifier} scale)'
        ),
        description=output,
        color=EMBED_COLOUR
    )
    if speedrun_time.screenshot:
        embed.set_image(url=f'attachment://{speedrun_time.screenshot}')

    return embed


def pb_cm_raid_to_embed(cm_raid_pb: CmRaidPbTime) -> interactions.Embed:
    players = [player.name for player in cm_raid_pb.get_players()]
    times = cm_raid_pb.get_room_times()

    # HACK: The spaces are the only way to make the formatting consistent.
    # Could calculate the max length of the string and pad it with spaces.
    # Max length of a line is 33.
    output = (
        f'### <:tektiny:1332765052792471707> `Tekton:                   {times['tekton']}`\n'
        f'### <:jewelled_crab:1332766850492399718> `Crabs:                    {times['crabs']}`\n'
        f'### <:ice_demon:1332766691352117339> `Ice Demon:                {times['icedemon']}`\n'
        f'### <:lizardmen:1332767026430869565> `Shamans:                  {times['shamans']}`\n'
        f'### <:slayer_helmet:1332769405276393607> `Floor 1:                  {times['floor1']}`\n'
        f'### <:Mini_vanguard:1332765436277952574> `Vanguards:                {times['vanguards']}`\n'
        f'### <:thieving_icon:1332765676863230003> `Thieving:                 {times['thieving']}`\n'
        f'### <:vespina:1332765870963036271> `Vespula:                  {times['vespula']}`\n'
        f'### <:keystone_crystal:1332767726510276751> `Tightrope:                {times['tightrope']}`\n'
        f'### <:phoenix_necklace:1332769426734321717> `Floor 2:                  {times['floor2']}`\n'
        f'### <:guardian:1332767232568197191> `Guardians:                {times['guardians']}`\n'
        f'### <:vasa_minirio:1332766068455903354> `Vasa:                     {times['vasa']}`\n'
        f'### <:skeletal_mystic:1332767413036515470> `Skeletal Mystics:         {times['mystics']}`\n'
        f'### <:puppadile:1332766216464498690> `Muttadiles:               {times['muttadiles']}`\n'
        f'### <:zamorak_godsword:1332769446472847421> `Floor 3:                  {times['floor3']}`\n'
        f'### <:olmlet:1332766373989974037> `Olm P1 Mage Hand:         {times['olmmagehandphase1']}`\n'
        f'### <:olmlet:1332766373989974037> `Olm P1:                   {times['olmphase1']}`\n'
        f'### <:olmlet:1332766373989974037> `Olm P2 Mage Hand:         {times['olmmagehandphase2']}`\n'
        f'### <:olmlet:1332766373989974037> `Olm P2:                   {times['olmphase2']}`\n'
        f'### <:olmlet:1332766373989974037> `Olm P3:                   {times['olmphase3']}`\n'
        f'### <:olmlet:1332766373989974037> `Olm Head Phase:           {times['olmhead']}`\n'
        f'### <:olmlet:1332766373989974037> `Olm:                      {times['olm']}`\n'
        f'### <:xeric_symbol:1332768391446138971> `Total:                    {times['completed']}`'
    )
    embed = interactions.Embed(
        title=(
            f'CM Raid personal best for {', '.join(players)} '
            f'({cm_raid_pb.get_scale().identifier} scale)'
        ),
        description=output,
        color=EMBED_COLOUR
    )

    return embed


def pb_cm_individual_room_to_embed(
    cm_individual_room_pbs: CmIndividualRoomPbTime
) -> interactions.Embed:
    player = cm_individual_room_pbs.get_player()
    times = cm_individual_room_pbs.get_individual_room_times()

    # HACK: The spaces are the only way to make the formatting consistent.
    output = (
        f'### <:tektiny:1332765052792471707> `Tekton:                   {times['tekton']}`\n'
        f'### <:jewelled_crab:1332766850492399718> `Crabs:                    {times['crabs']}`\n'
        f'### <:ice_demon:1332766691352117339> `Ice Demon:                {times['icedemon']}`\n'
        f'### <:lizardmen:1332767026430869565> `Shamans:                  {times['shamans']}`\n'
        f'### <:slayer_helmet:1332769405276393607> `Floor 1:                  {times['floor1']}`\n'
        f'### <:Mini_vanguard:1332765436277952574> `Vanguards:                {times['vanguards']}`\n'
        f'### <:thieving_icon:1332765676863230003> `Thieving:                 {times['thieving']}`\n'
        f'### <:vespina:1332765870963036271> `Vespula:                  {times['vespula']}`\n'
        f'### <:keystone_crystal:1332767726510276751> `Tightrope:                {times['tightrope']}`\n'
        f'### <:phoenix_necklace:1332769426734321717> `Floor 2:                  {times['floor2']}`\n'
        f'### <:guardian:1332767232568197191> `Guardians:                {times['guardians']}`\n'
        f'### <:vasa_minirio:1332766068455903354> `Vasa:                     {times['vasa']}`\n'
        f'### <:skeletal_mystic:1332767413036515470> `Skeletal Mystics:         {times['mystics']}`\n'
        f'### <:puppadile:1332766216464498690> `Muttadiles:               {times['muttadiles']}`\n'
        f'### <:zamorak_godsword:1332769446472847421> `Floor 3:                  {times['floor3']}`\n'
        f'### <:olmlet:1332766373989974037> `Olm P1 Mage Hand:         {times['olmmagehandphase1']}`\n'
        f'### <:olmlet:1332766373989974037> `Olm P1:                   {times['olmphase1']}`\n'
        f'### <:olmlet:1332766373989974037> `Olm P2 Mage Hand:         {times['olmmagehandphase2']}`\n'
        f'### <:olmlet:1332766373989974037> `Olm P2:                   {times['olmphase2']}`\n'
        f'### <:olmlet:1332766373989974037> `Olm P3:                   {times['olmphase3']}`\n'
        f'### <:olmlet:1332766373989974037> `Olm Head Phase:           {times['olmhead']}`\n'
        f'### <:olmlet:1332766373989974037> `Olm:                      {times['olm']}`\n'
    )
    embed = interactions.Embed(
        title=(
            f'CM room time personal bests for {player.name} '
            f'({cm_individual_room_pbs.get_scale().identifier} scale)'
        ),
        description=output,
        color=EMBED_COLOUR
    )

    return embed
