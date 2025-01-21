from config import TOKEN
from db import Session
from models.players import Players
from models.raid_type import RaidType
from models.speedrun_times import SpeedrunTimes
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
    raid_choices.append({'name': raid.name, 'value': raid.identifier})

@interactions.slash_command(
    name='submit_run',
    description='Submit a speedrun time',
    options=[
        interactions.SlashCommandOption(
            name='raid_type',
            description='e.g. cox, tob, toa',
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
            description='Submit the scale of the raid (1-5)',
            type=interactions.OptionType.STRING,
            choices=[
                {'name': 'Solo', 'value': '1'},
                {'name': 'Duo', 'value': '2'},
                {'name': 'Trio', 'value': '3'},
                {'name': 'Four-man', 'value': '4'},
                {'name': 'Five-man', 'value': '5'}
            ],
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

    # Validate raid type.
    raid_matched = session.query(RaidType).filter(
        RaidType.identifier == raid_type
    ).first()
    if not raid_matched:
        await ctx.send('Invalid raid type.')
        return

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
        found_player = session.query(Players.discord_id == runner).first()
        if not found_player:
            print(f'Player does not exist in the DB. Adding: {runner}')
            new_player = Players(
                discord_id=runner, name=runners_submitted[runner]
            )
            session.add(new_player)
            session.flush()
            continue

        print(f'Player exists in DB: {runner}')

    # Commit everything.
    session.commit()


bot.start()
