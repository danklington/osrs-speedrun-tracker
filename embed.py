from db import Session as session
from models.leaderboards import Leaderboards
from models.pb import Pb
from models.player import Player
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
        description=output,
        color=EMBED_COLOUR
    )


def pb_to_embed(pb_obj: Pb) -> interactions.Embed:
    runner_names = pb_obj.get_player_names_in_pb()
    pb_time = pb_obj.get_pb()
    formatted_time = ticks_to_time_string(pb_time.time)

    output = (
        '### :man_running_facing_right: '
        f'Runner{'s' if pb_obj.scale.value > 1 else ''}:\n'
        f'**{", ".join(runner_names)}**\n\n'
        f'### :clock1: Time:\n'
        f'### `{formatted_time}`'
    )

    embed = interactions.Embed(
        title=(
            f'{pb_obj.player.name}\'s personal best for '
            f'{pb_obj.raid_type.identifier} '
            f'({pb_obj.scale.identifier} scale)'
        ),
        description=output,
        color=EMBED_COLOUR
    )
    if pb_time.screenshot:
        embed.set_image(url=f'attachment://{pb_time.screenshot}')

    return embed


def pb_cm_to_embed(individual_pb=False):
    raise NotImplementedError("This function is not implemented yet.")
