from config import TOKEN
from db import Session
from models.player import Player
from models.raid_type import RaidType
from models.scale import Scale
from models.speedrun_time import SpeedrunTime
from util import download_attachment
from util import format_discord_ids
from util import is_valid_gametime
from util import ticks_to_time_string
import datetime
import interactions


# Intents.
intents = interactions.Intents.ALL
intents.members = True

# Initialize the bot.
bot = interactions.Client(token=TOKEN, intents=intents)

# Find the raid types and construct a dictionary for the slash command.
session = Session()
raid_types = session.query(RaidType).all()
raid_choices = [
    {'name': raid.identifier, 'value': raid.identifier} for raid in raid_types
]

# Find the scales and construct a dictionary for the slash command.
scales = session.query(Scale).all()
scale_choices = [
    {'name': scale.identifier, 'value': str(scale.value)} for scale in scales
]

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
            name='scale',
            description='Submit the scale of the raid',
            type=interactions.OptionType.INTEGER,
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
            name='minutes',
            description='Enter the minutes in the time you got',
            type=interactions.OptionType.INTEGER,
            min_value=0,
            max_value=59,
            required=True
        ),
        interactions.SlashCommandOption(
            name='seconds',
            description='Enter the seconds in the time you got',
            type=interactions.OptionType.INTEGER,
            min_value=0,
            max_value=59,
            required=True
        ),
        interactions.SlashCommandOption(
            name='milliseconds',
            description='Enter the milliseconds in the time you got',
            type=interactions.OptionType.INTEGER,
            min_value=0,
            max_value=8,
            required=True
        ),
        interactions.SlashCommandOption(
            name='screenshot',
            description='Submit a screenshot of the time',
            type=interactions.OptionType.ATTACHMENT,
            required=True
        )
    ]
)
async def submit_run(
    ctx: interactions.SlashContext,
    raid_type: str,
    minutes: int,
    seconds: int,
    milliseconds: int,
    scale: int,
    runners: str,
    screenshot: interactions.Attachment
):
    session = Session()

    # Validate the time submitted.
    total_time_in_seconds = datetime.timedelta(
        minutes=minutes,
        seconds=seconds,
        milliseconds=milliseconds * 100
    ).total_seconds()

    # Check if the time submitted can be an actual time in-game.
    if not is_valid_gametime(total_time_in_seconds):
        await ctx.send('The time submitted is not valid.')
        return

    time_in_ticks = int(round(total_time_in_seconds / 0.6, 1))

    # Make sure image is a PNG or JPEG.
    if screenshot.content_type not in ['image/png', 'image/jpeg']:
        await ctx.send('The image submitted is not a PNG or JPEG.')
        return

    # Validate runner string.
    if not runners:
        await ctx.send('Please submit at least one runner.')
        return

    # Sanitise the players input.
    runners = runners.replace(' ', '').split(',')

    # Make sure the runner string is formatted correctly.
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
        found_player = session.query(Player).filter(
            Player.discord_id == runner
        ).first()
        if not found_player:
            print(f'Player does not exist in the DB. Adding: {runner}')
            new_player = Player(
                discord_id=runner, name=runners_submitted[runner]
            )
            session.add(new_player)
            session.flush()
            continue

        print(f'Player exists in DB: {runner}')

    # Find the players in the database.
    existing_runners = session.query(Player).filter(
        Player.discord_id.in_(runner_list)
    ).all()

    # Format the runners for the database query, and for adding it later if we
    # do not find an identical run.
    formatted_runner_string = ','.join(
        [str(runner.id) for runner in existing_runners]
    )

    # Check if this exact run has already been submitted.
    run_exists = session.query(SpeedrunTime).filter(
        RaidType.identifier == raid_type,
        SpeedrunTime.raid_type_id == RaidType.id,
        Scale.value == scale,
        SpeedrunTime.scale_id == Scale.id,
        SpeedrunTime.time == time_in_ticks,
        SpeedrunTime.players == formatted_runner_string
    ).first()
    if run_exists:
        await ctx.send('An identical raid time has already been submitted.')
        return

    # Save the screenshot.
    image_name = f'{screenshot.id}.{screenshot.content_type.split("/")[1]}'
    await download_attachment(screenshot, image_name)

    # Find the raid type ID.
    raid = session.query(RaidType).filter(
        RaidType.identifier == raid_type
    ).first()

    # Find the scale ID.
    scale = session.query(Scale).filter(
        Scale.value == scale
    ).first()

    # Create a new speedrun time.
    new_time = SpeedrunTime(
        raid_type_id=raid.id,
        scale_id=scale.id,
        time=time_in_ticks,
        players=formatted_runner_string,
        screenshot=image_name
    )
    session.add(new_time)

    # Commit everything.
    session.commit()

    formatted_time = ticks_to_time_string(time_in_ticks)

    await ctx.send(
        f'Submitted {formatted_time} in {raid.identifier} with '
        f'{scale.identifier} scale.'
    )
    return


@interactions.slash_command(
    name='delete_run',
    description='Delete a speedrun time',
    options=[
        interactions.SlashCommandOption(
            name='raid_type',
            description='Which raid do you want to delete a time for?',
            type=interactions.OptionType.STRING,
            choices=raid_choices,
            required=True
        ),
        interactions.SlashCommandOption(
            name='scale',
            description='Enter the scale of the raid',
            type=interactions.OptionType.INTEGER,
            choices=scale_choices,
            required=True
        ),
        interactions.SlashCommandOption(
            name='runners',
            description='Enter the names of the runner(s) (comma separated)',
            type=interactions.OptionType.STRING,
            required=True
        ),
        interactions.SlashCommandOption(
            name='minutes',
            description='Enter the minutes in the time you wish to delete',
            type=interactions.OptionType.INTEGER,
            min_value=0,
            max_value=59,
            required=True
        ),
        interactions.SlashCommandOption(
            name='seconds',
            description='Enter the seconds in the time you wish to delete',
            type=interactions.OptionType.INTEGER,
            min_value=0,
            max_value=59,
            required=True
        ),
        interactions.SlashCommandOption(
            name='milliseconds',
            description='Enter the milliseconds in the time you wish to delete',
            type=interactions.OptionType.INTEGER,
            min_value=0,
            max_value=8,
            required=True
        )
    ]
)
async def delete_run(
    ctx: interactions.SlashContext,
    raid_type: str,
    scale: int,
    runners: str,
    minutes: int,
    seconds: int,
    milliseconds: int
):
    session = Session()

    # Validate the time submitted.
    total_time_in_seconds = datetime.timedelta(
        minutes=minutes,
        seconds=seconds,
        milliseconds=milliseconds * 100
    ).total_seconds()

    time_in_ticks = int(round(total_time_in_seconds / 0.6, 1))

    run_found = session.query(SpeedrunTime).filter(
        RaidType.identifier == raid_type,
        SpeedrunTime.raid_type_id == RaidType.id,
        Scale.value == scale,
        SpeedrunTime.scale_id == Scale.id,
        SpeedrunTime.time == time_in_ticks
    ).first()

    if run_found:
        session.delete(run_found)
        session.commit()
        await ctx.send('Run deleted.')
        return
    else:
        await ctx.send('Run not found.')
        return


@interactions.slash_command(
    name='leaderboards',
    description='Get the leaderboards for a raid',
    options=[
        interactions.SlashCommandOption(
            name='raid_type',
            description='Which raid do you want to see the leaderboards for?',
            type=interactions.OptionType.STRING,
            choices=raid_choices,
            required=True
        ),
        interactions.SlashCommandOption(
            name='scale',
            description='Enter the scale of the raid',
            type=interactions.OptionType.INTEGER,
            choices=scale_choices,
            required=True
        )
    ]
)
async def leaderboards(
    ctx: interactions.SlashContext,
    raid_type: str,
    scale: int
):
    session = Session()

    # Find the raid type ID.
    raid = session.query(RaidType).filter(
        RaidType.identifier == raid_type
    ).first()

    # Find the scale ID.
    scale = session.query(Scale).filter(
        Scale.value == scale
    ).first()

    # Find the leaderboards.
    leaderboards = session.query(SpeedrunTime).filter(
        SpeedrunTime.raid_type_id == raid.id,
        SpeedrunTime.scale_id == scale.id
    ).order_by(SpeedrunTime.time).limit(10).all()

    if not leaderboards:
        await ctx.send('No leaderboards found.')
        return

    output = ''
    for index, run in enumerate(leaderboards):
        formatted_time = ticks_to_time_string(run.time)
        players = run.players.split(',')
        player_names = []
        for player in players:
            player_obj = session.query(Player).filter(
                Player.id == player
            ).first()
            player_names.append(player_obj.name)
        player_string = ', '.join(player_names)
        if index == 0:
            output += f'{chr(0x1F947)} // '  # Gold medal emoji.
        elif index == 1:
            output += f'{chr(0x1F948)} // '  # Silver medal emoji.
        elif index == 2:
            output += f'{chr(0x1F949)} // '  # Bronze medal emoji.
        else:
            output += f'**{index + 1}** // '
        output += f'{formatted_time} - {player_string}\n\n'

    embed = interactions.Embed(
        title=f'Leaderboards for {raid.identifier} ({scale.identifier} scale)',
        description=output,
        color=0xc1005d,
    )

    await ctx.send(embed=embed)
    return


bot.start()
