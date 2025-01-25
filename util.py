from db import Session as session
from decimal import Decimal, getcontext
from models.player import Player
from models.raid_type import RaidType
from models.scale import Scale
from models.speedrun_time import SpeedrunTime
import aiohttp
import datetime
import interactions
import os


def get_raid_choices() -> list[interactions.SlashCommandChoice]:
    """ Returns the choices for all raid types. """

    raid_types = session.query(RaidType).all()
    raid_choices = [
        {'name': raid.identifier, 'value': raid.identifier}
        for raid in raid_types
    ]

    return sorted(raid_choices, key=lambda x: x['name'])


def get_scale_choices() -> list[interactions.SlashCommandChoice]:
    """ Returns the choices for all scales. """

    scales = session.query(Scale).all()
    scale_choices = [
        {'name': scale.identifier, 'value': scale.value}
        for scale in scales
    ]

    return sorted(scale_choices, key=lambda x: x['value'])


def format_discord_ids(discord_ids: list[str]) -> list[int]:
    """ IDs when submitted as a string come through as '<@000000000000000000>'.
        This function strips the '<@>' and returns the ID as an integer.
    """

    return [int(_id[2:-1]) for _id in discord_ids]


def is_valid_gametime(number: float) -> bool:
    """ Determines if a decimal is divisible by 0.6.
        The tolerance is set to 1e-9 to account for floating point errors.
    """

    tolerance=Decimal('1e-9')
    getcontext().prec = 28

    number = Decimal(str(number))
    divisor = Decimal('0.6')

    return abs(number % divisor) < tolerance


def ticks_to_time_string(ticks: int) -> str:
    """ Converts ticks to a formatted string. """

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


def add_runners_to_database(runners: dict) -> None:
    """ Adds the runners to the database. """

    # Compare the submitted players to the database of previous players.
    for discord_id in runners:
        # Check if the player is already in the database.
        found_player = session.query(Player).filter(
            Player.discord_id == discord_id
        ).first()
        if not found_player:
            print(f'Player does not exist in the DB. Adding: {discord_id}')
            new_player = Player(
                discord_id=discord_id, name=runners[discord_id]
            )
            session.add(new_player)
            session.flush()
            continue

        print(f'Player exists in DB: {discord_id}')

    session.commit()


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

    if not speedrun_time.screenshot:
        return

    screenshot = speedrun_time.screenshot
    attachment_path = os.path.join('attachments', screenshot)

    try:
        with open(attachment_path, 'r') as _:
            pass
    except FileNotFoundError:
        print(f"Screenshot does not exist. Fixing in DB: {attachment_path}")
        speedrun_time.screenshot = None
        session.commit()
