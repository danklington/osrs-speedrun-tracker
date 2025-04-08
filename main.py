from config import TOKEN
from db import get_session
from embed import confirmation_to_embed
from embed import error_to_embed
from embed import leaderboard_to_embed
from embed import pb_cm_individual_room_to_embed
from embed import pb_cm_raid_to_embed
from embed import pb_to_embed
from models.cm_individual_room_pb_time import CmIndividualRoomPbTime
from models.cm_raid_pb_time import CmRaidPbTime
from models.leaderboards import Leaderboards
from models.player import Player
from models.raid_type import RaidType
from models.scale import Scale
from models.speedrun_time import SpeedrunTime
from models.tob_raid_time import TobRaidTime
from util import add_runners_to_database
from util import download_attachment
from util import format_discord_ids
from util import get_cm_rooms
from util import get_discord_name_from_ids
from util import get_raid_choices
from util import get_scale_choices
from util import is_valid_cm_paste
from util import is_valid_gametime
from util import is_valid_runner_list
from util import open_attachment
from util import sync_screenshot_state
from util import ticks_to_time_string
from util import time_string_to_ticks
from util import validate_runners
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
cm_rooms = get_cm_rooms()


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
    # Make sure image is a PNG or JPEG.
    if screenshot.content_type not in ['image/png', 'image/jpeg']:
        message = ('The image submitted is not a PNG or JPEG.')
        embed = error_to_embed('Submission', message)
        await ctx.send(embed=embed)
        return

    # Validate the time submitted.
    total_time_in_seconds = datetime.timedelta(
        minutes=minutes,
        seconds=seconds,
        milliseconds=milliseconds * 100
    ).total_seconds()

    # Check if the time submitted can be an actual time in-game.
    if not is_valid_gametime(total_time_in_seconds):
        message = ('The time submitted is not valid.')
        embed = error_to_embed('Submission', message)
        await ctx.send(embed=embed)
        return

    time_in_ticks = int(round(total_time_in_seconds / 0.6, 1))

    # Validate the runners submitted.
    formatted_runners_list = await validate_runners(ctx, runners, scale)

    with get_session() as session:
        # Find the players in the database.
        existing_runners = session.query(Player).filter(
            Player.discord_id.in_(formatted_runners_list)
        ).all()

        # Format the runners for the database query, and for adding it later
        # if we do not find an identical run.
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
            message = ('An identical run has already been submitted.')
            embed = error_to_embed('Submission', message)
            await ctx.send(embed=embed)
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
        message = (
            f'Submitted `{formatted_time}` in {raid.identifier} with '
            f'{scale.identifier} scale.'
        )
        embed = confirmation_to_embed('Submission', message)
        await ctx.send(embed=embed)

        # Display the new time.
        embed = pb_to_embed(new_time)
        screenshot = interactions.File(
            f'attachments/{new_time.screenshot}'
        )
        await ctx.send(embed=embed, file=screenshot)


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
            description='Enter the milliseconds in the time you wish to delete',  # noqa
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
    # Validate the time submitted.
    total_time_in_seconds = datetime.timedelta(
        minutes=minutes,
        seconds=seconds,
        milliseconds=milliseconds * 100
    ).total_seconds()

    time_in_ticks = int(round(total_time_in_seconds / 0.6, 1))

    # Sanitise the players input.
    runners = runners.replace(' ', '').split(',')

    # Make sure the runner string is formatted correctly.
    if not is_valid_runner_list(runners):
        message = (
            'One or more of the runners has not been entered correctly.'
        )
        embed = error_to_embed('Deletion', message)
        await ctx.send(embed=embed)
        return

    formatted_runners_list = format_discord_ids(runners)

    with get_session() as session:
        # Find the players in the database.
        existing_runners = session.query(Player).filter(
            Player.discord_id.in_(formatted_runners_list)
        ).all()

        # Format the runners for the database query, and for adding it later
        # if we do not find an identical run.
        runner_db_id_string = ','.join(
            [str(runner.id) for runner in existing_runners]
        )

        speedruntime_found = session.query(SpeedrunTime).filter(
            RaidType.identifier == raid_type,
            SpeedrunTime.raid_type_id == RaidType.id,
            Scale.value == scale,
            SpeedrunTime.scale_id == Scale.id,
            SpeedrunTime.time == time_in_ticks,
            SpeedrunTime.players == runner_db_id_string
        ).first()

        # Get the scale object to display the identifier in the message.
        scale = session.query(Scale).filter(
            Scale.value == scale
        ).first()

        if speedruntime_found:
            # Look for a CM time to delete.
            if raid_type == 'Chambers of Xeric: Challenge Mode':
                cm_raid_pb = session.query(CmRaidPbTime).filter(
                    CmRaidPbTime.speedrun_time_id == speedruntime_found.id
                ).first()
                if cm_raid_pb:
                    session.delete(cm_raid_pb)

            session.delete(speedruntime_found)
            session.commit()

            message = (
                f'{raid_type} {scale.identifier} ({', '.join(runners)}) '
                'deleted.'
            )
            embed = confirmation_to_embed('Deletion', message)
            await ctx.send(embed=embed)

        else:
            message = (
                f'{raid_type} {scale.identifier} ({', '.join(runners)}) not '
                'found.'
            )
            embed = error_to_embed('Deletion', message)
            await ctx.send(embed=embed)


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

    # Check if the leaderboard exists.
    if not lb.get_leaderboard():
        embed = error_to_embed(
            'No leaderboard found',
            'There are no runs in this leaderboard yet.'
        )
        await ctx.send(embed=embed)
        return

    # Display the leaderboard in an embed.
    embed = leaderboard_to_embed(lb)
    await ctx.send(embed=embed)


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
    with get_session() as session:
        # Find the player.
        player = session.query(Player).filter(
            Player.discord_id == str(runner.id)
        ).first()

        # Find the scale.
        scale = session.query(Scale).filter(
            Scale.value == scale
        ).first()

        # Find the raid_type.
        raid_type = session.query(RaidType).filter(
            RaidType.identifier == raid_type
        ).first()

        # Find the personal best.
        speedrun_time = session.query(SpeedrunTime).filter(
            SpeedrunTime.raid_type_id == raid_type.id,
            SpeedrunTime.scale_id == scale.id,
            SpeedrunTime.players.contains(
                ','.join([str(player.id)])
            )
        ).order_by(SpeedrunTime.time).first()

        if not speedrun_time:
            message = (
                f'{runner.display_name} does not have a personal best for '
                f'{raid_type.identifier} with {scale.identifier}.'
            )
            embed = error_to_embed('No PB found', message)
            await ctx.send(embed=embed)
            return

        # Check if the run is a CM raid.
        if raid_type.identifier == 'Chambers of Xeric: Challenge Mode':
            cm_raid_pb = session.query(CmRaidPbTime).filter(
                CmRaidPbTime.speedrun_time_id == speedrun_time.id
            ).first()
            if cm_raid_pb:
                # Display the run in an embed.
                embed = pb_cm_raid_to_embed(cm_raid_pb)
                await ctx.send(embed=embed)
                return

        # Sync the state of the screenshot in the database.
        sync_screenshot_state(speedrun_time)

        # Embed the run.
        embed = pb_to_embed(speedrun_time)

        if speedrun_time.screenshot:
            screenshot = interactions.File(
                f'attachments/{speedrun_time.screenshot}'
            )
            await ctx.send(embed=embed, file=screenshot)
            return

        await ctx.send(embed=embed)


@interactions.slash_command(
    name='pb_cm_rooms',
    description='Display a player\'s personal best for every room in a CM raid',  # noqa
    options=[
        interactions.SlashCommandOption(
            name='scale',
            description='Enter the scale of the raid',
            type=interactions.OptionType.INTEGER,
            choices=scale_choices,
            required=True
        ),
        interactions.SlashCommandOption(
            name='runner',
            description='Enter the names of the runner(s) (comma separated)',
            type=interactions.OptionType.USER,
            required=True
        )
    ]
)
async def pb_cm_rooms(
    ctx: interactions.SlashContext,
    scale: int,
    runner: interactions.Member
):
    with get_session() as session:
        # Find the player.
        player = session.query(Player).filter(
            Player.discord_id == str(runner.id)
        ).first()

        # Find the scale.
        scale = session.query(Scale).filter(
            Scale.value == scale
        ).first()

        # Find the room pbs.
        room_pbs = session.query(CmIndividualRoomPbTime).filter(
            CmIndividualRoomPbTime.player_id == player.id,
            CmIndividualRoomPbTime.scale_id == scale.id,
        ).first()

        if not room_pbs:
            message = (
                f'{runner.display_name} does not have any room personal '
                'bests.'
            )
            embed = error_to_embed('No room PBs found', message)
            await ctx.send(embed=embed)
            return

        embed = pb_cm_individual_room_to_embed(room_pbs)
        await ctx.send(embed=embed)


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
    # Split the string into a list before every capital letter.
    capital_letters_at_start = r'[A-Z][^A-Z]*'
    room_times = re.findall(capital_letters_at_start, room_times)

    # Remove the last 6 elements as they are not useful, and remove elements
    # that do not contain a colon.
    room_times = [x.lower() for x in room_times[:-6] if ':' in x]

    # Strip unneeded characters.
    room_times = [x.replace(' ', '').replace('|', '') for x in room_times]

    # Split each element into a key value pair, e.g. {'tekton': '1:04.8', ...}
    room_times = {
        x.split(':', 1)[0]: x.split(':', 1)[1] for x in room_times
    }

    if not is_valid_cm_paste(room_times):
        message = ('The room times submitted are not formatted correctly.')
        embed = error_to_embed('Submission', message)
        await ctx.send(embed=embed)
        return

    # Grab the scale from the string and then pop it so we do not run our time
    # function on it.
    scale = int(room_times.pop('size'))

    # Convert the times to ticks.
    for room in room_times:
        room_times[room] = time_string_to_ticks(room_times[room])

    # Store the total raid time and remove it from the dictionary to avoid the
    # get and set attr running on it.
    total_raid_time = room_times.pop('completed')

    with get_session() as session:
        # Check if the scale exists in the database.
        cm_raid_scale = session.query(Scale).filter(
            Scale.value == scale
        ).first()
        if not cm_raid_scale:
            await ctx.send('Invalid CM scale submitted.')
            return

        print('scale:', cm_raid_scale.value)

        print(f'Room times submitted: {room_times}')

        # Validate the runners submitted.
        formatted_runners_list = await validate_runners(ctx, runners, scale)

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

        # Track the updated room times so we can display it in the embed.
        updated_times = []
        room_before_after = ()

        # Update individual room time PBs per player.
        for runner in existing_runners:
            # Get the player's best room times.
            best_times = session.query(CmIndividualRoomPbTime).filter(
                CmIndividualRoomPbTime.player_id == runner.id,
                CmIndividualRoomPbTime.scale_id == cm_raid_scale.id
            ).first()

            if not best_times:
                new_run = CmIndividualRoomPbTime(
                    player_id=runner.id,
                    scale_id=cm_raid_scale.id,
                    **room_times
                )
                session.add(new_run)
                session.flush()
                continue

            # Update the player's best room times if they are faster.
            for room in room_times:
                if not getattr(best_times, room):
                    setattr(best_times, room, room_times[room])
                    updated_times.append(
                        (runner, room, None, room_times[room])
                    )
                    session.flush()
                    continue

                if room_times[room] < getattr(best_times, room):
                    room_before_after = (
                        runner,
                        room,
                        getattr(best_times, room),
                        room_times[room]
                    )
                    setattr(best_times, room, room_times[room])
                    updated_times.append(room_before_after)
                    session.flush()

        if updated_times:
            message = (
                'The room times submitted have been updated for the following '
                'rooms:\n'
            )

            for runner, room, before, after in updated_times:
                # If there was no time before, we can't show a before and
                # after.
                if before is None:
                    message += (
                        f'### {runner.name}: {room} - '
                        f'`{ticks_to_time_string(after)}`\n'
                    )
                    continue

                message += (
                    f'### {runner.name}: {room} - '
                    f'`{ticks_to_time_string(before)}` '
                    f'-> `{ticks_to_time_string(after)}`\n'
                )

            embed = confirmation_to_embed('New room PB(s)', message)
            await ctx.send(embed=embed)

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

            message = (
                f'Submitted `{ticks_to_time_string(total_raid_time)}` in CoX: '
                f'CM with {cm_raid_scale.identifier} scale.'
            )
            embed = confirmation_to_embed('Submission', message)
            await ctx.send(embed=embed)

            # Display the run in an embed.
            embed = pb_cm_raid_to_embed(new_run)
            await ctx.send(embed=embed)

            return

        # Check if the run is a PB.
        better_run_exists = session.query(CmRaidPbTime).filter(
            CmRaidPbTime.scale_id == cm_raid_scale.id,
            CmRaidPbTime.speedrun_time_id == speedrun_time.id,
            CmRaidPbTime.completed <= total_raid_time
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
            message = (
                f'Submitted `{ticks_to_time_string(total_raid_time)}` in CoX: '
                f'CM with {cm_raid_scale.identifier} scale.'
            )
            embed = confirmation_to_embed('Submission', message)
            await ctx.send(embed=embed)

            # Display the run in an embed.
            embed = pb_cm_raid_to_embed(new_run)
            await ctx.send(embed=embed)

        else:
            message = (
                'The run submitted is not a personal best.\n'
                'Any room times that were faster have still been updated.'
            )
            embed = confirmation_to_embed('Submission', message)
            await ctx.send(embed=embed)

        session.commit()


@interactions.slash_command(
    name='delete_cm_room_pb',
    description='Delete a player\'s personal best for a room in a CM raid',
    options=[
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
        ),
        interactions.SlashCommandOption(
            name='room',
            description='Enter the room you want to delete the PB for',
            type=interactions.OptionType.STRING,
            choices=cm_rooms,
            required=True
        )
    ]
)
async def delete_cm_room_pb(
    ctx: interactions.SlashContext,
    scale: int,
    runner: interactions.Member,
    room: str
):

    with get_session() as session:
        # Find the scale.
        scale = session.query(Scale).filter(
            Scale.value == scale
        ).first()

        # Find the player.
        player = session.query(Player).filter(
            Player.discord_id == str(runner.id)
        ).first()

        # Find the player's personal best rooms.
        room_pb = session.query(CmIndividualRoomPbTime).filter(
            CmIndividualRoomPbTime.scale_id == scale.id,
            CmIndividualRoomPbTime.player_id == player.id
        ).first()

        if not room_pb:
            message = (
                'The player does not have a personal best for this room.'
            )
            embed = error_to_embed('Deletion', message)
            await ctx.send(embed=embed)
            return

        # Set the room time to None.
        setattr(room_pb, room, None)
        session.commit()

        embed = confirmation_to_embed(
            'Deletion',
            f'PB for {room} deleted for <@{runner.id}> '
            f'({scale.identifier} scale).'
        )
        await ctx.send(embed=embed)


@interactions.slash_command(
    name='delete_all_cm_room_pb',
    description='Delete all room PBs for a player in a CM raid',
    options=[
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
async def delete_all_cm_room_pb(
    ctx: interactions.SlashContext,
    scale: int,
    runner: interactions.Member
):

    with get_session() as session:
        # Find the scale.
        scale = session.query(Scale).filter(
            Scale.value == scale
        ).first()

        # Find the player.
        player = session.query(Player).filter(
            Player.discord_id == str(runner.id)
        ).first()

        # Find the player's personal best rooms.
        room_pbs = session.query(CmIndividualRoomPbTime).filter(
            CmIndividualRoomPbTime.scale_id == scale.id,
            CmIndividualRoomPbTime.player_id == player.id
        ).first()

        if not room_pbs:
            message = (
                'The player does not have any personal bests for this scale.'
            )
            embed = error_to_embed('Deletion', message)
            await ctx.send(embed=embed)
            return

        # Delete the room times.
        session.delete(room_pbs)
        session.commit()

        embed = confirmation_to_embed(
            'Deletion',
            f'All room times deleted for <@{runner.id}> '
            f'({scale.identifier} scale).'
        )
        await ctx.send(embed=embed)


@interactions.slash_command(
    name='submit_tob_from_csv',
    description='Submit a ToB run from a CSV file',
    options=[
        interactions.SlashCommandOption(
            name='runners',
            description='Enter the names of the runner(s) (comma separated)',
            type=interactions.OptionType.STRING,
            required=True
        ),
        interactions.SlashCommandOption(
            name='file',
            description='Submit a raid from a CSV file',
            type=interactions.OptionType.ATTACHMENT,
            required=True
        )
    ]
)
async def submit_tob_from_csv(
    ctx: interactions.SlashContext,
    runners: str,
    file: interactions.Attachment
):
    tobdata = await open_attachment(file)
    print(tobdata)
    scale = 0
    total_time = 0
    verzik_flag = False
    verzik_p1_flag = True
    verzik_redcrabs_flag = True
    # Array for all relevant tob times (in order)
    tob_times = [0] * 22

    for line in tobdata.strip().splitlines():
        parts = line.split(',')
        if len(parts) > 3:
            match parts[3]:
                # Scale
                case '1':
                    players =[x for x in parts[-5:]  if x]
                    scale=len(players)
                    print(f"Scale: {scale}")
                    formatted_runners_list = await validate_runners(ctx, runners, scale)
                    if not formatted_runners_list:
                        break
                 ########## Maiden ##########
                # Maiden 70s
                case '13':
                    tob_times[0] = (int)(parts[4])
                    print("Maiden 70s: " + parts[4])

                # Maiden 50s
                case '14':
                    tob_times[1] = (int)(parts[4])
                    print("Maiden 50s: " + parts[4])

                # Maiden 30s
                case '15':
                    tob_times[2] = (int)(parts[4])
                    print("Maiden 30s: " + parts[4])

                # Maiden total time
                case '17':
                    tob_times[3] = (int)(parts[4])
                    total_time += (int)(parts[4])
                    print("Maiden total time: " + parts[4] + "\n----------")

                ########## Bloat ##########
                case '23':
                    tob_times[4] = (int)(parts[4])
                    total_time += (int)(parts[4])
                    print("Bloat: " + parts[4] + "\n----------")

                ########## Nylocas ##########
                # Nylo waves
                case '35':
                    tob_times[5] = (int)(parts[4])
                    print("Nylo waves: " + parts[4])
                # Nylo cleanup
                case '36':
                    tob_times[6] = (int)(parts[4])
                    print(f"Nylo cleanup: {tob_times[6]}({tob_times[6] - tob_times[5]})")

                    # Nylo boss spawn
                    tob_times[7] = tob_times[6] + 16
                    print(f"Nylo boss spawn: {tob_times[7]}")

                # Nylo total time
                case '45':
                    tob_times[8] = (int)(parts[4])
                    total_time += (int)(parts[4])
                    print("Nylo total time: " + parts[4] + "\n----------")

                ########## Sotetseg ##########
                # Sote Maze 1 start
                case '52':
                    tob_times[9] = (int)(parts[4])
                # Sote Maze 1 end
                case '53':
                    tob_times[10] = (int)(parts[4])
                    print(f"Sote 1st maze: {tob_times[9]}({tob_times[10] - tob_times[9]})")
                # Sote Maze 2 start
                case '54':
                    tob_times[11] = (int)(parts[4])
                # Sote Maze 2 end
                case '55':
                    tob_times[12] = (int)(parts[4])
                    print(f"Sote 2nd maze: {tob_times[11]}({tob_times[12] - tob_times[11]})")
                # Sote total time
                case '57':
                    tob_times[13] = (int)(parts[4])
                    total_time += (int)(parts[4])
                    print(f"Sotesteg total time: {tob_times[13]}" + "\n----------")

                ########## Xarpus ##########
                # Xarpus screech
                case '63':
                    tob_times[14] = (int)(parts[4])
                    print(f"Xarpus screech: {tob_times[14]}")
                # Xarpus total time
                case '65':
                    tob_times[15] = (int)(parts[4])
                    total_time += (int)(parts[4])
                    print(f"Xarpus total time: {tob_times[15]}" + "\n----------")

                ########## Verzik ##########
                # Verzik p1
                case '73':
                    if verzik_p1_flag == True:
                        tob_times[16] = (int)(parts[4])
                        print(f"Verzik p1: {tob_times[16]} ")
                        verzik_p1_flag = False
                # Verzik red crabs
                case '80':
                    if verzik_redcrabs_flag == True:
                        tob_times[17] = (int)(parts[4])
                        print(f"Verzik red crabs: {tob_times[17]}")
                        verzik_redcrabs_flag = False
                # Verzik p2
                case '74':
                    tob_times[18] = (int)(parts[4])
                    print(f"Verzik p2: {tob_times[18]}({tob_times[18] - tob_times[16]}) ")
                # Verzik total time
                case '76':
                    if verzik_flag == True:
                        tob_times[20] = (int)(parts[4])
                        total_time += (int)(parts[4])
                        tob_times[19] = tob_times[20] - tob_times[18]
                        print(f"Verzik p3: {tob_times[19]}"
                              f"\nVerzik total time: {tob_times[20]}")

                    verzik_flag = True

    print("total ticks: " + (str)(total_time) + "\ntotal time: " + (str)((int)(total_time * 0.6 / 60)) + ':' +
          (str)(total_time * 0.6 % (60 * ((int)(total_time * 0.6 / 60)))))
    tob_times[21] = total_time
    formatted_runners_list = await validate_runners(ctx, runners, scale)

    with get_session() as session:
        raid_type=session.query(RaidType).filter(RaidType.identifier=='Theatre of Blood').first()
        scale_type = session.query(Scale).filter(Scale.value == scale).first()
        # Find the players in the database.
        existing_runners = session.query(Player).filter(
            Player.discord_id.in_(formatted_runners_list)
        ).all()

        # Format the runners for the database query.
        runner_db_id_string = ','.join(
            [str(runner.id) for runner in existing_runners]
        )

        speedrun_time = SpeedrunTime(
            raid_type_id=raid_type.id,
            scale_id=scale_type.id,
            time=total_time,
            players=runner_db_id_string
        )

        session.add(speedrun_time)
        session.flush()
        insert_tobtimes = TobRaidTime.__table__.insert().values(
            scale_id = scale,
            speedrun_time_id=speedrun_time.id,
            maiden_70=tob_times[0],
            maiden_50=tob_times[1],
            maiden_30=tob_times[2],
            maiden=tob_times[3],
            bloat=tob_times[4],
            nylocas_waves=tob_times[5],
            nylocas_cleanup=tob_times[6],
            nylocas_bossspawn=tob_times[7],
            nylocas=tob_times[8],
            sotetseg_maze1_start=tob_times[9],
            sotetseg_maze1_end=tob_times[10],
            sotetseg_maze2_start=tob_times[11],
            sotetseg_maze2_end=tob_times[12],
            sotetseg=tob_times[13],
            xarpus_screech=tob_times[14],
            xarpus=tob_times[15],
            verzik_p1=tob_times[16],
            verzik_reds=tob_times[17],
            verzik_p2=tob_times[18],
            verzik_p3=tob_times[19],
            verzik=tob_times[20],
            completed=tob_times[21]
        )
        session.execute(insert_tobtimes)
        session.commit()

bot.start()
