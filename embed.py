from models.cm_raid_time import CmRaidTime
from models.cm_room_time import CmRoomTime
from models.leaderboards import Leaderboards
from models.speedrun_time import SpeedrunTime
from models.tob_raid_time import TobRaidTime
from models.tob_room_time import TobRoomTime
from util import space_line_for_embed
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


def leaderboard_to_embed(leaderboards: Leaderboards) -> interactions.Embed:
    output = ''
    emoji_list = [
        ':first_place:', ':second_place:', ':third_place:', ':four:', ':five:',
        ':six:', ':seven:', ':eight:', ':nine:', ':keycap_ten:'
    ]

    for index, run in enumerate(leaderboards.get_leaderboard()):
        formatted_time = ticks_to_time_string(run.time)
        players = leaderboards.get_players(run)
        player_names = [player.name for player in players]
        player_string = ', '.join(player_names)
        output += emoji_list[index]
        output += f' | `{formatted_time}` - **{player_string}**\n\n'

    return interactions.Embed(
        title=(
            f'{leaderboards.get_raid_type().identifier} '
            f'({leaderboards.get_scale().identifier} scale) leaderboard'
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


def pb_cm_raid_to_embed(cm_raid_pb: CmRaidTime) -> interactions.Embed:
    players = [player.name for player in cm_raid_pb.get_players()]
    times = cm_raid_pb.get_room_times()

    emojis = {
        'tekton': '<:tektiny:1332765052792471707>',
        'crabs': '<:jewelled_crab:1332766850492399718>',
        'icedemon': '<:ice_demon:1332766691352117339>',
        'shamans': '<:lizardmen:1332767026430869565>',
        'floor1': '<:slayer_helmet:1332769405276393607>',
        'vanguards': '<:Mini_vanguard:1332765436277952574>',
        'thieving': '<:thieving_icon:1332765676863230003>',
        'vespula': '<:vespina:1332765870963036271>',
        'tightrope': '<:keystone_crystal:1332767726510276751>',
        'floor2': '<:phoenix_necklace:1332769426734321717>',
        'guardians': '<:guardian:1332767232568197191>',
        'vasa': '<:vasa_minirio:1332766068455903354>',
        'mystics': '<:skeletal_mystic:1332767413036515470>',
        'muttadiles': '<:puppadile:1332766216464498690>',
        'floor3': '<:zamorak_godsword:1332769446472847421>',
        'olmmagehandphase1': '<:olmlet:1332766373989974037>',
        'olmphase1': '<:olmlet:1332766373989974037>',
        'olmmagehandphase2': '<:olmlet:1332766373989974037>',
        'olmphase2': '<:olmlet:1332766373989974037>',
        'olmphase3': '<:olmlet:1332766373989974037>',
        'olmhead': '<:olmlet:1332766373989974037>',
        'olm': '<:olmlet:1332766373989974037>',
        'completed': '<:xeric_symbol:1332768391446138971>'
    }

    output = space_line_for_embed(emojis['tekton'], 'Tekton', times['tekton'])
    output += space_line_for_embed(emojis['crabs'], 'Crabs', times['crabs'])
    output += space_line_for_embed(emojis['icedemon'], 'Ice Demon', times['icedemon'])  # noqa
    output += space_line_for_embed(emojis['shamans'], 'Shamans', times['shamans'])  # noqa
    output += space_line_for_embed(emojis['floor1'], 'Floor 1', times['floor1'])  # noqa
    output += space_line_for_embed(emojis['vanguards'], 'Vanguards', times['vanguards'])  # noqa
    output += space_line_for_embed(emojis['thieving'], 'Thieving', times['thieving'])  # noqa
    output += space_line_for_embed(emojis['vespula'], 'Vespula', times['vespula'])  # noqa
    output += space_line_for_embed(emojis['tightrope'], 'Tightrope', times['tightrope'])  # noqa
    output += space_line_for_embed(emojis['floor2'], 'Floor 2', times['floor2'])  # noqa
    output += space_line_for_embed(emojis['guardians'], 'Guardians', times['guardians'])  # noqa
    output += space_line_for_embed(emojis['vasa'], 'Vasa', times['vasa'])
    output += space_line_for_embed(emojis['mystics'], 'Skeletal Mystics', times['mystics'])  # noqa
    output += space_line_for_embed(emojis['muttadiles'], 'Muttadiles', times['muttadiles'])  # noqa
    output += space_line_for_embed(emojis['floor3'], 'Floor 3', times['floor3'])  # noqa
    output += space_line_for_embed(emojis['olmmagehandphase1'], 'Olm P1 Mage Hand', times['olmmagehandphase1'])  # noqa
    output += space_line_for_embed(emojis['olmphase1'], 'Olm P1', times['olmphase1'])  # noqa
    output += space_line_for_embed(emojis['olmmagehandphase2'], 'Olm P2 Mage Hand', times['olmmagehandphase2'])  # noqa
    output += space_line_for_embed(emojis['olmphase2'], 'Olm P2', times['olmphase2'])  # noqa
    output += space_line_for_embed(emojis['olmphase3'], 'Olm P3', times['olmphase3'])  # noqa
    output += space_line_for_embed(emojis['olmhead'], 'Olm Head Phase', times['olmhead'])  # noqa
    output += space_line_for_embed(emojis['olm'], 'Olm', times['olm'])
    output += space_line_for_embed(emojis['completed'], 'Total', times['completed'])  # noqa

    embed = interactions.Embed(
        title=(
            f'CM Raid personal best for {', '.join(players)} '
            f'({cm_raid_pb.get_scale().identifier} scale)'
        ),
        description=output,
        color=EMBED_COLOUR
    )

    return embed


def pb_cm_room_to_embed(
    cm_individual_room_pbs: CmRoomTime
) -> interactions.Embed:
    player = cm_individual_room_pbs.get_player()
    times = cm_individual_room_pbs.get_individual_room_times()

    emojis = {
        'tekton': '<:tektiny:1332765052792471707>',
        'crabs': '<:jewelled_crab:1332766850492399718>',
        'icedemon': '<:ice_demon:1332766691352117339>',
        'shamans': '<:lizardmen:1332767026430869565>',
        'floor1': '<:slayer_helmet:1332769405276393607>',
        'vanguards': '<:Mini_vanguard:1332765436277952574>',
        'thieving': '<:thieving_icon:1332765676863230003>',
        'vespula': '<:vespina:1332765870963036271>',
        'tightrope': '<:keystone_crystal:1332767726510276751>',
        'floor2': '<:phoenix_necklace:1332769426734321717>',
        'guardians': '<:guardian:1332767232568197191>',
        'vasa': '<:vasa_minirio:1332766068455903354>',
        'mystics': '<:skeletal_mystic:1332767413036515470>',
        'muttadiles': '<:puppadile:1332766216464498690>',
        'floor3': '<:zamorak_godsword:1332769446472847421>',
        'olmmagehandphase1': '<:olmlet:1332766373989974037>',
        'olmphase1': '<:olmlet:1332766373989974037>',
        'olmmagehandphase2': '<:olmlet:1332766373989974037>',
        'olmphase2': '<:olmlet:1332766373989974037>',
        'olmphase3': '<:olmlet:1332766373989974037>',
        'olmhead': '<:olmlet:1332766373989974037>',
        'olm': '<:olmlet:1332766373989974037>',
    }

    output = space_line_for_embed(emojis['tekton'], 'Tekton', times['tekton'])
    output += space_line_for_embed(emojis['crabs'], 'Crabs', times['crabs'])
    output += space_line_for_embed(emojis['icedemon'], 'Ice Demon', times['icedemon'])  # noqa
    output += space_line_for_embed(emojis['shamans'], 'Shamans', times['shamans'])  # noqa
    output += space_line_for_embed(emojis['floor1'], 'Floor 1', times['floor1'])  # noqa
    output += space_line_for_embed(emojis['vanguards'], 'Vanguards', times['vanguards'])  # noqa
    output += space_line_for_embed(emojis['thieving'], 'Thieving', times['thieving'])  # noqa
    output += space_line_for_embed(emojis['vespula'], 'Vespula', times['vespula'])  # noqa
    output += space_line_for_embed(emojis['tightrope'], 'Tightrope', times['tightrope'])  # noqa
    output += space_line_for_embed(emojis['floor2'], 'Floor 2', times['floor2'])  # noqa
    output += space_line_for_embed(emojis['guardians'], 'Guardians', times['guardians'])  # noqa
    output += space_line_for_embed(emojis['vasa'], 'Vasa', times['vasa'])
    output += space_line_for_embed(emojis['mystics'], 'Skeletal Mystics', times['mystics'])  # noqa
    output += space_line_for_embed(emojis['muttadiles'], 'Muttadiles', times['muttadiles'])  # noqa
    output += space_line_for_embed(emojis['floor3'], 'Floor 3', times['floor3'])  # noqa
    output += space_line_for_embed(emojis['olmmagehandphase1'], 'Olm P1 Mage Hand', times['olmmagehandphase1'])  # noqa
    output += space_line_for_embed(emojis['olmphase1'], 'Olm P1', times['olmphase1'])  # noqa
    output += space_line_for_embed(emojis['olmmagehandphase2'], 'Olm P2 Mage Hand', times['olmmagehandphase2'])  # noqa
    output += space_line_for_embed(emojis['olmphase2'], 'Olm P2', times['olmphase2'])  # noqa
    output += space_line_for_embed(emojis['olmphase3'], 'Olm P3', times['olmphase3'])  # noqa
    output += space_line_for_embed(emojis['olmhead'], 'Olm Head Phase', times['olmhead'])  # noqa
    output += space_line_for_embed(emojis['olm'], 'Olm', times['olm'])

    embed = interactions.Embed(
        title=(
            f'CM room time personal bests for {player.name} '
            f'({cm_individual_room_pbs.get_scale().identifier} scale)'
        ),
        description=output,
        color=EMBED_COLOUR
    )

    return embed


def pb_tob_raid_to_embed(tob_raid_pb: TobRaidTime) -> interactions.Embed:
    players = [player.name for player in tob_raid_pb.get_players()]
    times = tob_raid_pb.get_room_times()

    emojis = {
        'maiden': '<:maiden:1408123879595184363>',
        'bloat': '<:bloat:1408123907638169690>',
        'nylocas': '<:nylo:1408123939535851635>',
        'sotetseg': '<:sote:1408123952550903928>',
        'xarpus': '<:xarp:1408123965842657330>',
        'verzik': '<:verzik:1408123977578188800>',
        'completed': '<:scythe:1408124465828597912>'
    }

    output = space_line_for_embed(emojis['maiden'], 'Maiden 70s', times['maiden_70'])  # noqa
    output += space_line_for_embed(emojis['maiden'], 'Maiden 50s', times['maiden_50'])  # noqa
    output += space_line_for_embed(emojis['maiden'], 'Maiden 30s', times['maiden_30'])  # noqa
    output += space_line_for_embed(emojis['maiden'], 'Maiden', times['maiden'])  # noqa
    output += space_line_for_embed(emojis['bloat'], 'Bloat', times['bloat'])  # noqa
    output += space_line_for_embed(emojis['nylocas'], 'Nylocas Waves', times['nylocas_waves'])  # noqa
    output += space_line_for_embed(emojis['nylocas'], 'Nylocas Cleanup', times['nylocas_cleanup'])  # noqa
    output += space_line_for_embed(emojis['nylocas'], 'Nylocas Boss Spawn', times['nylocas_bossspawn'])  # noqa
    output += space_line_for_embed(emojis['nylocas'], 'Nylocas', times['nylocas'])  # noqa
    output += space_line_for_embed(emojis['sotetseg'], 'Sotetseg Maze 1 start', times['sotetseg_maze1_start'])  # noqa
    output += space_line_for_embed(emojis['sotetseg'], 'Sotetseg Maze 1 end', times['sotetseg_maze1_end'])  # noqa
    output += space_line_for_embed(emojis['sotetseg'], 'Sotetseg Maze 2 start', times['sotetseg_maze2_start'])  # noqa
    output += space_line_for_embed(emojis['sotetseg'], 'Sotetseg Maze 2 end', times['sotetseg_maze2_end'])  # noqa
    output += space_line_for_embed(emojis['sotetseg'], 'Sotetseg', times['sotetseg'])  # noqa
    output += space_line_for_embed(emojis['xarpus'], 'Xarpus Screech', times['xarpus_screech'])  # noqa
    output += space_line_for_embed(emojis['xarpus'], 'Xarpus', times['xarpus'])  # noqa
    output += space_line_for_embed(emojis['verzik'], 'Verzik P1', times['verzik_p1'])  # noqa
    output += space_line_for_embed(emojis['verzik'], 'Verzik Reds', times['verzik_reds'])  # noqa
    output += space_line_for_embed(emojis['verzik'], 'Verzik P2', times['verzik_p2'])  # noqa
    output += space_line_for_embed(emojis['verzik'], 'Verzik P3', times['verzik_p3'])  # noqa
    output += space_line_for_embed(emojis['verzik'], 'Verzik', times['verzik'])  # noqa
    output += space_line_for_embed(emojis['completed'], 'Total', times['completed'])  # noqa

    embed = interactions.Embed(
        title=(
            f'ToB Raid personal best for {', '.join(players)} '
            f'({tob_raid_pb.get_scale().identifier} scale)'
        ),
        description=output,
        color=EMBED_COLOUR
    )

    return embed


def pb_tob_room_to_embed(
    tob_individual_room_pbs: TobRoomTime
) -> interactions.Embed:
    player = tob_individual_room_pbs.get_player()
    times = tob_individual_room_pbs.get_individual_room_times()

    emojis = {
        'maiden': '<:maiden:1408123879595184363>',
        'bloat': '<:bloat:1408123907638169690>',
        'nylocas': '<:nylo:1408123939535851635>',
        'sotetseg': '<:sote:1408123952550903928>',
        'xarpus': '<:xarp:1408123965842657330>',
        'verzik': '<:verzik:1408123977578188800>',
        'completed': '<:scythe:1408124465828597912>'
    }

    output = space_line_for_embed(emojis['maiden'], 'Maiden 70s', times['maiden_70'])  # noqa
    output += space_line_for_embed(emojis['maiden'], 'Maiden 50s', times['maiden_50'])  # noqa
    output += space_line_for_embed(emojis['maiden'], 'Maiden 30s', times['maiden_30'])  # noqa
    output += space_line_for_embed(emojis['maiden'], 'Maiden', times['maiden'])  # noqa
    output += space_line_for_embed(emojis['bloat'], 'Bloat', times['bloat'])  # noqa
    output += space_line_for_embed(emojis['nylocas'], 'Nylocas Waves', times['nylocas_waves'])  # noqa
    output += space_line_for_embed(emojis['nylocas'], 'Nylocas Cleanup', times['nylocas_cleanup'])  # noqa
    output += space_line_for_embed(emojis['nylocas'], 'Nylocas Boss Spawn', times['nylocas_bossspawn'])  # noqa
    output += space_line_for_embed(emojis['nylocas'], 'Nylocas', times['nylocas'])  # noqa
    output += space_line_for_embed(emojis['sotetseg'], 'Sotetseg Maze 1 start', times['sotetseg_maze1_start'])  # noqa
    output += space_line_for_embed(emojis['sotetseg'], 'Sotetseg Maze 1 end', times['sotetseg_maze1_end'])  # noqa
    output += space_line_for_embed(emojis['sotetseg'], 'Sotetseg Maze 2 start', times['sotetseg_maze2_start'])  # noqa
    output += space_line_for_embed(emojis['sotetseg'], 'Sotetseg Maze 2 end', times['sotetseg_maze2_end'])  # noqa
    output += space_line_for_embed(emojis['sotetseg'], 'Sotetseg', times['sotetseg'])  # noqa
    output += space_line_for_embed(emojis['xarpus'], 'Xarpus Screech', times['xarpus_screech'])  # noqa
    output += space_line_for_embed(emojis['xarpus'], 'Xarpus', times['xarpus'])  # noqa
    output += space_line_for_embed(emojis['verzik'], 'Verzik P1', times['verzik_p1'])  # noqa
    output += space_line_for_embed(emojis['verzik'], 'Verzik Reds', times['verzik_reds'])  # noqa
    output += space_line_for_embed(emojis['verzik'], 'Verzik P2', times['verzik_p2'])  # noqa
    output += space_line_for_embed(emojis['verzik'], 'Verzik P3', times['verzik_p3'])  # noqa
    output += space_line_for_embed(emojis['verzik'], 'Verzik', times['verzik'])  # noqa

    embed = interactions.Embed(
        title=(
            f'ToB room time personal bests for {player.name} '
            f'({tob_individual_room_pbs.get_scale().identifier} scale)'
        ),
        description=output,
        color=EMBED_COLOUR
    )

    return embed
