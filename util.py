from decimal import Decimal, getcontext
import aiohttp
import datetime
import interactions
import os

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
