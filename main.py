from config import TOKEN
from db import Session
from embed import leaderboard_to_embed
from embed import pb_to_embed
from models.cm_individual_room_pb_time import CmIndividualRoomPbTime
from models.cm_raid_pb_time import CmRaidPbTime
from models.leaderboards import Leaderboards
from models.pb import Pb
from models.player import Player
from models.raid_type import RaidType
from models.scale import Scale
from models.speedrun_time import SpeedrunTime
from util import add_runners_to_database
from util import download_attachment
from util import format_discord_ids
from util import get_discord_name_from_ids
from util import get_raid_choices
from util import get_scale_choices
from util import is_valid_gametime
from util import ticks_to_time_string
from util import time_string_to_ticks
import datetime
import interactions
import re


# Intents.
intents = interactions.Intents.ALL
intents.members = True

# Initialize the bot.
bot = interactions.Client(token=TOKEN, intents=intents)

# Get all raid and scale choices for the slash commands.
raid_choices = get_raid_choices()
scale_choices = get_scale_choices()


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

    # Make sure image is a PNG or JPEG.
    if screenshot.content_type not in ['image/png', 'image/jpeg']:
        await ctx.send('The image submitted is not a PNG or JPEG.')
        return

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

    # Sanitise the players input.
    runners = runners.replace(' ', '').split(',')

    # Make sure the runner string is formatted correctly.
    for runner in runners:
        if runner[0:2] != '<@' or runner[-1] != '>' or runner.count('@') != 1:
            await ctx.send(
                'One or more of the runners has not been entered correctly.'
            )
            return

    # Remove the '<@' and '>' from the runner string.
    formatted_runners_list = format_discord_ids(runners)

    # Make sure the number of submitted runners matches the number of players
    # for the scale.
    if len(formatted_runners_list) != scale:
        await ctx.send(
            'The number of runners submitted does not match the scale of '
            f'the raid. Expected {scale}, got {len(formatted_runners_list)}.'
        )
        return

    # Associate the runner IDs with their names.
    discord_id_and_names = get_discord_name_from_ids(
        ctx, formatted_runners_list
    )
    if discord_id_and_names is None:
        await ctx.send('One of the users submitted is not on this server.')
        return

    print(f'Runners submitted: {discord_id_and_names}')

    add_runners_to_database(discord_id_and_names)

    # Find the players in the database.
    existing_runners = session.query(Player).filter(
        Player.discord_id.in_(formatted_runners_list)
    ).all()

    # Format the runners for the database query, and for adding it later if we
    # do not find an identical run.
    runner_db_id_string = ','.join(
        [str(runner.id) for runner in existing_runners]
    )

    # Check if this exact run has already been submitted.
    run_exists = session.query(SpeedrunTime).filter(
        RaidType.identifier == raid_type,
        SpeedrunTime.raid_type_id == RaidType.id,
        Scale.value == scale,
        SpeedrunTime.scale_id == Scale.id,
        SpeedrunTime.time == time_in_ticks,
        SpeedrunTime.players == runner_db_id_string
    ).first()
    if run_exists:
        await ctx.send('An identical raid time has already been submitted.')
        return

    # Save the screenshot.
    image_name = f'{screenshot.id}.{screenshot.content_type.split('/')[1]}'
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
        players=runner_db_id_string,
        screenshot=image_name
    )
    session.add(new_time)

    # Commit everything.
    session.commit()

    # Format the time for the response.
    formatted_time = ticks_to_time_string(time_in_ticks)

    # TODO: Create an embed for the response.

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
    lb = Leaderboards(raid_type, scale)

    leaderboard = lb.get_leaderboard()
    if not leaderboard:
        await ctx.send('No leaderboards found.')
        return

    embed = leaderboard_to_embed(leaderboard)
    embed.title = f'Leaderboard for {raid_type} ({lb.scale.identifier} scale)'

    await ctx.send(embed=embed)
    return


@interactions.slash_command(
    name='pb',
    description='Display a player\'s personal best for a raid',
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
        ),
        interactions.SlashCommandOption(
            name='runner',
            description='Enter the name of the runner',
            type=interactions.OptionType.USER,
            required=True
        )
    ]
)
async def pb(
    ctx: interactions.SlashContext,
    raid_type: str,
    scale: int,
    runner: interactions.Member
):
    personal_best = Pb(raid_type, scale, runner)
    if not personal_best.player:
        await ctx.send('Player not found in database.')
        return

    pb_time = personal_best.get_pb()
    if not pb_time:
        await ctx.send('No personal best found.')
        return

    embed = pb_to_embed(personal_best, pb_time)

    if pb_time.screenshot:
        screenshot = interactions.File(f'attachments/{pb_time.screenshot}')
        await ctx.send(embed=embed, files=[screenshot])
        return

    # If there is no screenshot, send the embed without a file.
    else:
        await ctx.send(embed=embed)
        return


@interactions.slash_command(
    name='submit_cm_from_clipboard',
    description='Use the cox analytics plugin to paste in your room times',
    options=[
        interactions.SlashCommandOption(
            name='runners',
            description='Enter the names of the runner(s) (comma separated)',
            type=interactions.OptionType.STRING,
            required=True
        ),
        interactions.SlashCommandOption(
            name='room_times',
            description='Paste in your room times',
            type=interactions.OptionType.STRING,
            required=True
        )
    ]
)
async def submit_cm_from_clipboard(
    ctx: interactions.SlashContext,
    runners: str,
    room_times: str
):
    session = Session()

    # Split the string into a list before every capital letter.
    capital_letters_at_start = r'[A-Z][^A-Z]*'
    room_times = re.findall(capital_letters_at_start, room_times)

    # Remove the last 6 elements as they are not useful, and remove elements
    # that do not contain a colon.
    room_times = [x.lower() for x in room_times[:-6] if ':' in x]

    # Strip unneeded characters.
    room_times = [x.replace(' ', '').replace('|', '') for x in room_times]

    # Split each element into a key value pair, e.g. {'Tekton': '1:04.8', ...}
    room_times = {
        x.split(':', 1)[0]: x.split(':', 1)[1] for x in room_times
    }

    # Grab the scale from the string and then pop it so we do not run our time
    # function on it.
    scale = int(room_times.pop('size'))

    # Convert the times to ticks.
    for room in room_times:
        room_times[room] = time_string_to_ticks(room_times[room])

    # Store the total raid time and remove it from the dictionary to avoid the
    # get and set attr running on it.
    total_raid_time = room_times.pop('completed')

    # Check if the scale exists in the database.
    scale_exists = session.query(Scale).filter(
        Scale.value == scale
    ).first()
    if not scale_exists:
        await ctx.send('Invalid CM scale submitted.')
        return

    print(f'Room times submitted: {room_times}')

    # Sanitise the players input.
    runners = runners.replace(' ', '').split(',')

    # Make sure the runner string is formatted correctly.
    for runner in runners:
        if runner[0:2] != '<@' or runner[-1] != '>' or runner.count('@') != 1:
            await ctx.send(
                'One or more of the runners has not been entered correctly.'
            )
            return

    # Remove the '<@' and '>' from the runner string.
    formatted_runners_list = format_discord_ids(runners)

    # Make sure the number of submitted runners matches the number of players
    # for the scale.
    if len(formatted_runners_list) != scale:
        await ctx.send(
            'The number of runners submitted does not match the scale of '
            f'the raid. Expected {scale}, got {len(formatted_runners_list)}.'
        )
        return

    # Associate the runner IDs with their names.
    discord_id_and_names = get_discord_name_from_ids(
        ctx, formatted_runners_list
    )
    if discord_id_and_names is None:
        await ctx.send('One of the users submitted is not on this server.')
        return

    print(f'Runners submitted: {discord_id_and_names}')

    add_runners_to_database(discord_id_and_names)

    # Find the players in the database.
    existing_runners = session.query(Player).filter(
        Player.discord_id.in_(formatted_runners_list)
    ).all()

    # Format the runners for the database query.
    runner_db_id_string = ','.join(
        [str(runner.id) for runner in existing_runners]
    )

    # Get the CoX: CM raid type.
    cm_raid_type = session.query(RaidType).filter(
        RaidType.identifier == 'Chambers of Xeric: Challenge Mode'
    ).first()

    # Get the scale.
    cm_raid_scale = session.query(Scale).filter(
        Scale.value == scale
    ).first()

    # Add to speedrun_time table.
    # Check if this exact run has already been submitted.
    speedrun_time = session.query(SpeedrunTime).filter(
        SpeedrunTime.raid_type_id == cm_raid_type.id,
        SpeedrunTime.scale_id == cm_raid_scale.id,
        SpeedrunTime.time == total_raid_time,
        SpeedrunTime.players == runner_db_id_string
    ).first()
    if not speedrun_time:
        # Save the run to the database.
        speedrun_time = SpeedrunTime(
            raid_type_id=cm_raid_type.id,
            scale_id=cm_raid_scale.id,
            time=total_raid_time,
            players=runner_db_id_string
        )
        session.add(speedrun_time)
        session.flush()

    # Update individual room time PBs per player.
    for runner in existing_runners:
        # Get the player's best room times.
        best_times = session.query(CmIndividualRoomPbTime).filter(
            CmIndividualRoomPbTime.player_id == runner.id
        ).first()

        if not best_times:
            new_run = CmIndividualRoomPbTime(
                player_id=runner.id,
                scale_id=scale,
                **room_times
            )
            session.add(new_run)
            session.flush()
            continue

        # Update the player's best room times if they are faster.
        for room in room_times:
            if room_times[room] < getattr(best_times, room):
                setattr(best_times, room, room_times[room])
                session.flush()

    # If a run doesn't exist, just add it.
    run_exists = session.query(CmRaidPbTime).filter(
        CmRaidPbTime.scale_id == cm_raid_scale.id,
        CmRaidPbTime.speedrun_time_id == speedrun_time.id
    ).first()
    if not run_exists:
        new_run = CmRaidPbTime(
            scale_id=scale,
            speedrun_time_id=speedrun_time.id,
            completed=total_raid_time,
            **room_times
        )
        session.add(new_run)
        session.commit()
        await ctx.send('Run submitted.')
        return

    # Check if the run is a PB.
    better_run_exists = session.query(CmRaidPbTime).filter(
        CmRaidPbTime.scale_id == cm_raid_scale.id,
        CmRaidPbTime.speedrun_time_id == speedrun_time.id,
        CmRaidPbTime.completed < total_raid_time
    ).first()
    if not better_run_exists:
        new_run = CmRaidPbTime(
            scale_id=scale,
            speedrun_time_id=speedrun_time.id,
            completed=total_raid_time,
            **room_times
        )
        session.add(new_run)
        session.flush()
        await ctx.send('Run submitted.')

    else:
        await ctx.send('Run is not a PB.')

    session.commit()
    return


bot.start()
