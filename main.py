from config import TOKEN
from db import Session
from models.player import Player
from models.raid_type import RaidType
from models.scale import Scale
from models.speedrun_time import SpeedrunTime
from util import format_discord_ids
import interactions


# Intents.
intents = interactions.Intents.ALL
intents.members = True

# Initialize the bot.
bot = interactions.Client(token=TOKEN, intents=intents)

# Find the raid types and construct a dictionary for the slash command.
session = Session()
raid_types = session.query(RaidType).all()
raid_choices = []
for raid in raid_types:
    raid_choices.append({'name': raid.identifier, 'value': raid.identifier})

# Find the scales and construct a dictionary for the slash command.
scales = session.query(Scale).all()
scale_choices = []
for scale in scales:
    scale_choices.append({'name': scale.identifier, 'value': str(scale.value)})

@interactions.slash_command(
    name='submit_run',
    description='Submit a speedrun time',
    options=[
        interactions.SlashCommandOption(
            name='raid_type',
            description='Which raid do you want to submit a time for?',
            type=interactions.OptionType.STRING,
            choices=raid_choices,
            required=True
        ),
        interactions.SlashCommandOption(
            name='time',
            description='Submit the time you got (including decimals)',
            type=interactions.OptionType.STRING,
            required=True
        ),
        interactions.SlashCommandOption(
            name='scale',
            description='Submit the scale of the raid',
            type=interactions.OptionType.STRING,
            choices=scale_choices,
            required=True
        ),
        interactions.SlashCommandOption(
            name='runners',
            description='Submit the names of the runner(s) (comma separated)',
            type=interactions.OptionType.STRING,
            required=True
        ),
        interactions.SlashCommandOption(
            name='screenshot',
            description='Submit a screenshot of the time',
            type=interactions.OptionType.STRING,
            required=True
        )
    ]
)
async def submit_run(
    ctx: interactions.SlashContext,
    raid_type: str = "",
    time: str = "0",
    scale: str = "",
    runners: str = "",
    screenshot: str = ""
):
    session = Session()

    print('DEBUG: ', raid_type, time, scale, runners, screenshot)

    # Validate runner string.
    if not runners:
        await ctx.send('Please submit at least one runner.')
        return

    # Sanitise the players input.
    runners = runners.replace(' ', '')

    # Make sure the runner string is formatted correctly.
    runners = runners.split(',')
    for runner in runners:
        if runner[0:2] != '<@' or runner[-1] != '>' or runner.count('@') != 1:
            await ctx.send(
                'One or more of the runners is not formatted correctly.'
            )
            return

    # Remove the '<@' and '>' from the runner string.
    runner_list = format_discord_ids(runners)

    # Associate the runner IDs with their names.
    runners_submitted = {}
    for runner in runner_list:
        member = ctx.guild.get_member(runner)
        if member:
            runners_submitted[runner] = member.display_name
        else:
            await ctx.send('User does not exist in the server.')
            return

    print(f'Runners submitted: {runners_submitted}')

    # Compare the submitted players to the database of previous players.
    for runner in runners_submitted:
        # Check if the player is already in the database.
        found_player = session.query(Player.discord_id == runner).first()
        if not found_player:
            print(f'Player does not exist in the DB. Adding: {runner}')
            new_player = Player(
                discord_id=runner, name=runners_submitted[runner]
            )
            session.add(new_player)
            session.flush()
            continue

        print(f'Player exists in DB: {runner}')

    # Commit everything.
    session.commit()

    await ctx.send('Run submitted successfully!')
    return


bot.start()
