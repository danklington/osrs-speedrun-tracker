from db import get_session
from decimal import Decimal, getcontext
from models.cm_room_time import CmRoomTime
from models.cm_raid_time import CmRaidTime
from models.player import Player
from models.player_group import PlayerGroup
from models.raid_type import RaidType
from models.scale import Scale
from models.speedrun_time import SpeedrunTime
from sqlalchemy import func
import aiohttp
import datetime
import interactions
import os


def get_raid_choices() -> list[interactions.SlashCommandChoice]:
    """ Returns the choices for all raid types. """

    with get_session() as session:
        raid_types = session.query(RaidType).all()
        raid_choices = [
            interactions.SlashCommandChoice(
                name=raid.identifier, value=raid.identifier
            )
            for raid in raid_types
        ]

        return sorted(raid_choices, key=lambda x: str(x.name))


def get_scale_choices() -> list[interactions.SlashCommandChoice]:
    """ Returns the choices for all scales. """

    with get_session() as session:
        scales = session.query(Scale).all()
        scale_choices = [
            interactions.SlashCommandChoice(
                name=scale.identifier, value=scale.value
            )
            for scale in scales
        ]

        return sorted(scale_choices, key=lambda x: x.value)


def get_cm_rooms() -> list[interactions.SlashCommandChoice]:
    """ Returns the names of the CM rooms. """

    cm_rooms = CmRoomTime.__table__.columns.keys()[3:]

    # Convert the list to a dictionary for the interaction.
    cm_rooms = [
        interactions.SlashCommandChoice(
            name=cm_room.capitalize(), value=cm_room
        )
        for cm_room in cm_rooms
    ]

    return cm_rooms


def format_discord_ids(discord_ids: list[str]) -> list[int]:
    """ IDs when submitted as a string come through as '<@000000000000000000>'.
        This function strips the '<@>' and returns the ID as an integer.
    """

    return [int(_id[2:-1]) for _id in discord_ids]


def is_valid_gametime(number: float) -> bool:
    """ Determines if a decimal is divisible by 0.6.
        The tolerance is set to 1e-9 to account for floating point errors.
    """

    tolerance = Decimal('1e-9')
    getcontext().prec = 28

    number = Decimal(str(number))
    divisor = Decimal('0.6')

    return abs(number % divisor) < tolerance


def is_valid_runner_list(runner_list: list[str]) -> bool:
    """ Determines if the runner list is valid. """

    for runner in runner_list:
        if runner[0:2] != '<@' or runner[-1] != '>' or runner.count('@') != 1:
            return False

    return True


def ticks_to_time_string(ticks: int) -> str:
    """ Converts ticks to a formatted string. """

    if ticks is None:
        return 'N/A'

    seconds = ticks * 0.6
    time_obj = datetime.datetime.utcfromtimestamp(seconds)
    return time_obj.strftime('%M:%S.%f')[:-5]


def time_string_to_ticks(time_string: str) -> int:
    """ Converts a formatted string to ticks. """

    time_obj = datetime.datetime.strptime(time_string, '%M:%S.%f')
    return int((
        (time_obj.minute * 60) +
        time_obj.second +
        (time_obj.microsecond / 1000000)
    ) / 0.6)


async def download_attachment(
    screenshot: interactions.Attachment, save_as: str
) -> None:
    """ Downloads the attachment from the URL. """

    # Ensure the attachments directory exists
    attachments_dir = 'attachments'
    if not os.path.exists(attachments_dir):
        os.makedirs(attachments_dir)

    # Download the attachment
    async with aiohttp.ClientSession() as client_session:
        async with client_session.get(screenshot.url) as response:
            if response.status == 200:
                file_content = await response.read()
                file_path = os.path.join(attachments_dir, save_as)
                with open(file_path, 'wb') as f:
                    f.write(file_content)
                print(f"File saved to {file_path}")
            else:
                raise Exception(
                    f"Failed to download attachment: {response.status}"
                )


async def open_attachment(attachment: interactions.Attachment) -> str:
    """ Loads the attachment content into memory. """

    # Download the attachment
    async with aiohttp.ClientSession() as client_session:
        async with client_session.get(attachment.url) as response:
            if response.status == 200:
                file_content = await response.read()
                return file_content.decode('utf-8')
            else:
                raise Exception(
                    f'Failed to load attachment: {response.status}'
                )


def add_runners_to_database(runners: dict) -> None:
    """ Adds the runners to the database. """

    # List of players that now have a DB entry.
    players = []

    with get_session() as session:
        # Compare the submitted players to the database of previous players.
        for discord_id in runners:
            # Check if the player is already in the database.
            player = session.query(Player).filter(
                Player.discord_id == discord_id
            ).first()
            if not player:
                print(f'Player does not exist in the DB. Adding: {discord_id}')
                player = Player(
                    discord_id=discord_id, name=runners[discord_id]
                )
                session.add(player)
                session.flush()
                continue

            players.append(player)

            print(f'Player exists in DB: {discord_id}')

        # Check if there's a player group which contains all of the
        # players.
        player_ids = [player.id for player in players]
        group_id = get_player_group_id(player_ids)
        if group_id:
            print(f'Player group exists: {group_id}')
            return

        print('Player group does not exist. Creating new group.')

        # Get a new group ID.
        group_id = session.query(func.max(PlayerGroup.id)).scalar()
        if group_id is None:
            group_id = 1
        else:
            group_id += 1

        # Add the players to the group.
        for player in players:
            player_group = PlayerGroup(
                id=group_id,
                player_id=player.id
            )
            print(
                f'Adding player {player.name} ({player.id}) to group '
                f'{group_id}.'
            )
            session.add(player_group)

        session.commit()


def get_player_group_id(player_ids: list[int]) -> int | None:
    """ Checks if a player group exists with a given list of player IDs. """

    with get_session() as session:
        group_ids = session.query(PlayerGroup.id).filter(
            PlayerGroup.player_id.in_(player_ids)
        ).group_by(
            PlayerGroup.id
        ).having(
            func.count(PlayerGroup.player_id) == len(player_ids)
        ).all()

        for group_id, in group_ids:
            group_player_ids = session.query(PlayerGroup.player_id).filter(
                PlayerGroup.id == group_id
            ).all()
            group_player_ids = {player_id for player_id, in group_player_ids}

            if group_player_ids == set(player_ids):
                return group_id

        return None


def get_players_from_discord_ids(discord_ids: list[int]) -> list[Player]:
    """ Retrieves the players from the database using their Discord IDs. """

    with get_session() as session:
        return session.query(Player).filter(
            Player.discord_id.in_(discord_ids)
        ).all()


async def validate_runners(
        ctx: interactions.SlashContext, runners: str, scale: int
) -> list[int | None]:
    """ Validates the runners submitted by the user. """

    from embed import error_to_embed

    # Sanitise the players input.
    runners = runners.replace(' ', '').split(',')

    # Make sure the runner string is formatted correctly.
    if not is_valid_runner_list(runners):
        message = (
            'One or more of the runners has not been entered correctly.'
        )
        embed = error_to_embed('Submission', message)
        await ctx.send(embed=embed)
        return []

    # Remove the '<@' and '>' from the runner string.
    formatted_runners_list = format_discord_ids(runners)

    # Make sure the number of submitted runners matches the number of players
    # for the scale.
    if len(formatted_runners_list) != scale:
        message = (
            'The number of runners submitted does not match the scale of '
            f'the raid. Expected {scale}, got {len(formatted_runners_list)}.'
        )
        embed = error_to_embed('Submission', message)
        await ctx.send(embed=embed)
        return []

    # Associate the runner IDs with their names.
    discord_id_and_names = get_discord_name_from_ids(
        ctx, formatted_runners_list
    )
    if discord_id_and_names is None:
        message = ('One of the users submitted is not on this server.')
        embed = error_to_embed('Submission', message)
        await ctx.send(embed=embed)
        return []

    print(f'Runners submitted: {discord_id_and_names}')

    add_runners_to_database(discord_id_and_names)

    return formatted_runners_list


def get_discord_name_from_ids(
    ctx: interactions.SlashContext, discord_ids: list[int]
) -> dict:
    """ Retrieves the Discord name from the database. """

    discord_id_and_names = {}
    for runner in discord_ids:
        member = ctx.guild.get_member(runner)
        if member:
            discord_id_and_names[runner] = member.display_name
        else:
            return None

    return discord_id_and_names


def sync_screenshot_state(speedrun_time: SpeedrunTime) -> None:
    """ Sets the screenshot to NULL in the DB if the file does not exist. """

    with get_session() as session:
        if not speedrun_time.screenshot:
            return

        screenshot = speedrun_time.screenshot
        attachment_path = os.path.join('attachments', screenshot)

        try:
            with open(attachment_path, 'r') as _:
                pass
        except FileNotFoundError:
            print(
                f'Screenshot does not exist. Fixing in DB: {attachment_path}'
            )
            speedrun_time.screenshot = None
            session.merge(speedrun_time)
            session.commit()


def is_valid_cm_paste(parsed_paste: dict) -> bool:
    """ Ensures all keys from the parsed dictionary are present.
        (e.g. {'tekton': '1:04.8', ...})
    """

    # Check if the values have decimals.
    for key, value in parsed_paste.items():
        # Ignore size key as this shouldn't be a decimal.
        if key == 'size':
            continue
        if '.' not in value:
            return False

    # Remove first 2 elements because they're just IDs.
    expected_keys = CmRaidTime.__table__.columns.keys()[2:]

    # Add the size key because it's not in the DB but should be in the paste.
    expected_keys.append('size')

    parsed_keys = list(parsed_paste.keys())

    return set(expected_keys) == set(parsed_keys)


def space_line_for_embed(emoji: str, text: str, time: str) -> str:
    """ Formats a line with the proper spacing for an embed. """

    max_line_length = 40
    spaces = ' ' * (max_line_length - (len(text) + len(time)))
    return f'### {emoji} `{text}:{spaces}{time}`\n'
