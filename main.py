from config import TOKEN
from db import Session
from models.speedrun_times import SpeedrunTimes
from models.raid_type import RaidType
from models.players import Players
import interactions


# Initialize the bot.
bot = interactions.Client(token=TOKEN)


@interactions.slash_command(
    name='submit_run',
    description='Submit a speedrun time',
    options=[
        interactions.SlashCommandOption(
            name='raid_type',
            description='e.g. cox, tob, toa',
            type=interactions.OptionType.STRING,
            required=True
        ),
        interactions.SlashCommandOption(
            name='time',
            description='Submit the time you got (including decimals)',
            type=interactions.OptionType.STRING,
            required=False
        ),
        interactions.SlashCommandOption(
            name='scale',
            description='Submit the scale of the raid (1-5)',
            type=interactions.OptionType.STRING,
            required=False
        )
    ]
)
async def submit_run(
    ctx: interactions.SlashContext,
    raid_type: str,
    time: str = "0",
    scale: str = "0"
):
    print('Raid type:', raid_type)
    print('Time:', time)
    print('Scale:', scale)

bot.start()