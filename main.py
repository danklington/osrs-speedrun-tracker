from config import TOKEN
from db import get_session
from embed import confirmation_to_embed
from embed import error_to_embed
from embed import leaderboard_to_embed
from embed import pb_cm_raid_to_embed
from embed import pb_cm_room_to_embed
from embed import pb_to_embed
from embed import pb_tob_raid_to_embed
from embed import pb_tob_room_to_embed
from models.cm_raid_time import CmRaidTime
from models.cm_room_time import CmRoomTime
from models.leaderboards import Leaderboards
from models.player import Player
from models.player_group import PlayerGroup
from models.raid_type import RaidType
from models.scale import Scale
from models.speedrun_time import SpeedrunTime
from models.tob_raid_time import TobRaidTime
from models.tob_room_time import TobRoomTime
from util import download_attachment
from util import format_discord_ids
from util import get_cm_rooms
from util import get_player_group_id
from util import get_players_from_discord_ids
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
        {
            "name": "raid_type",
            "description": "Which raid do you want to submit a time for?",
            "type": interactions.OptionType.STRING,
            "choices": raid_choices,
            "required": True
        },
        {
            "name": "scale",
            "description": "Submit the scale of the raid",
            "type": interactions.OptionType.INTEGER,
            "choices": scale_choices,
            "required": True
        },
        {
            "name": "runners",
            "description": (
                "Submit the names of the runner(s) (comma separated)"
            ),
            "type": interactions.OptionType.STRING,
            "required": True
        },
        {
            "name": "minutes",
            "description": "Enter the minutes in the time you got",
            "type": interactions.OptionType.INTEGER,
            "min_value": 0,
            "max_value": 59,
            "required": True
        },
        {
            "name": "seconds",
            "description": "Enter the seconds in the time you got",
            "type": interactions.OptionType.INTEGER,
            "min_value": 0,
            "max_value": 59,
            "required": True
        },
        {
            "name": "milliseconds",
            "description": "Enter the milliseconds in the time you got",
            "type": interactions.OptionType.INTEGER,
            "min_value": 0,
            "max_value": 8,
            "required": True
        },
        {
            "name": "screenshot",
            "description": "Submit a screenshot of the time",
            "type": interactions.OptionType.ATTACHMENT,
            "required": True
        }
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
    if not formatted_runners_list:
        return

    with get_session() as session:
        # Check if the players are in a group.
        players = get_players_from_discord_ids(formatted_runners_list)
        player_ids = [player.id for player in players]
        player_group_id = get_player_group_id(player_ids)

        # Check if this exact run has already been submitted.
        run_exists = session.query(SpeedrunTime).filter(
            RaidType.identifier == raid_type,
            SpeedrunTime.raid_type_id == RaidType.id,
            Scale.value == scale,
            SpeedrunTime.scale_id == Scale.id,
            SpeedrunTime.time == time_in_ticks,
            SpeedrunTime.player_group_id == player_group_id
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
            player_group_id=player_group_id,
            time=time_in_ticks,
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
        {
            "name": "raid_type",
            "description": "Which raid do you want to delete a time for?",
            "type": interactions.OptionType.STRING,
            "choices": raid_choices,
            "required": True
        },
        {
            "name": "scale",
            "description": "Enter the scale of the raid",
            "type": interactions.OptionType.INTEGER,
            "choices": scale_choices,
            "required": True
        },
        {
            "name": "runners",
            "description": (
                "Enter the names of the runner(s) (comma separated)"
            ),
            "type": interactions.OptionType.STRING,
            "required": True
        },
        {
            "name": "minutes",
            "description": "Enter the minutes in the time you wish to delete",
            "type": interactions.OptionType.INTEGER,
            "min_value": 0,
            "max_value": 59,
            "required": True
        },
        {
            "name": "seconds",
            "description": "Enter the seconds in the time you wish to delete",
            "type": interactions.OptionType.INTEGER,
            "min_value": 0,
            "max_value": 59,
            "required": True
        },
        {
            "name": "milliseconds",
            "description": (
                "Enter the milliseconds in the time you wish to delete"
            ),
            "type": interactions.OptionType.INTEGER,
            "min_value": 0,
            "max_value": 8,
            "required": True
        }
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

    players = get_players_from_discord_ids(formatted_runners_list)
    player_ids = [player.id for player in players]
    player_group_id = get_player_group_id(player_ids)

    with get_session() as session:
        speedruntime_found = session.query(SpeedrunTime).filter(
            RaidType.identifier == raid_type,
            SpeedrunTime.raid_type_id == RaidType.id,
            Scale.value == scale,
            SpeedrunTime.scale_id == Scale.id,
            SpeedrunTime.time == time_in_ticks,
            SpeedrunTime.player_group_id == player_group_id
        ).first()

        # Get the scale object to display the identifier in the message.
        scale = session.query(Scale).filter(
            Scale.value == scale
        ).first()

        if speedruntime_found:
            # Look for a CM time to delete.
            if raid_type == 'Chambers of Xeric: Challenge Mode':
                cm_raid_pb = session.query(CmRaidTime).filter(
                    CmRaidTime.speedrun_time_id == speedruntime_found.id
                ).first()
                if cm_raid_pb:
                    session.delete(cm_raid_pb)
                    session.flush()

            if raid_type == 'Theatre of Blood':
                tob_raid_pb = session.query(TobRaidTime).filter(
                    TobRaidTime.speedrun_time_id == speedruntime_found.id
                ).first()
                if tob_raid_pb:
                    session.delete(tob_raid_pb)
                    session.flush()

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
        {
            "name": "raid_type",
            "description": (
                "Which raid do you want to see the leaderboards for?"
            ),
            "type": interactions.OptionType.STRING,
            "choices": raid_choices,
            "required": True
        },
        {
            "name": "scale",
            "description": "Enter the scale of the raid",
            "type": interactions.OptionType.INTEGER,
            "choices": scale_choices,
            "required": True
        }
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
        {
            "name": "raid_type",
            "description": (
                "Which raid do you want to see the leaderboards for?"
            ),
            "type": interactions.OptionType.STRING,
            "choices": raid_choices,
            "required": True
        },
        {
            "name": "scale",
            "description": "Enter the scale of the raid",
            "type": interactions.OptionType.INTEGER,
            "choices": scale_choices,
            "required": True
        },
        {
            "name": "runner",
            "description": "Enter the name of the runner",
            "type": interactions.OptionType.USER,
            "required": True
        }
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
        speedrun_time = session.query(SpeedrunTime).join(
            PlayerGroup, SpeedrunTime.player_group_id == PlayerGroup.id
        ).filter(
            SpeedrunTime.raid_type_id == raid_type.id,
            SpeedrunTime.scale_id == scale.id,
            PlayerGroup.player_id == player.id
        ).order_by(SpeedrunTime.time).first()

        if not speedrun_time:
            message = (
                f'{runner.display_name} does not have a {scale.identifier} '
                f'personal best for {raid_type.identifier}.'
            )
            embed = error_to_embed('No PB found', message)
            await ctx.send(embed=embed)
            return

        # Check if the run is a CM raid.
        if raid_type.identifier == 'Chambers of Xeric: Challenge Mode':
            cm_raid_pb = session.query(CmRaidTime).filter(
                CmRaidTime.speedrun_time_id == speedrun_time.id
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
        {
            "name": "scale",
            "description": "Enter the scale of the raid",
            "type": interactions.OptionType.INTEGER,
            "choices": scale_choices,
            "required": True
        },
        {
            "name": "runner",
            "description": (
                "Enter the names of the runner(s) (comma separated)"
            ),
            "type": interactions.OptionType.USER,
            "required": True
        }
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
        room_pbs = session.query(CmRoomTime).filter(
            CmRoomTime.player_id == player.id,
            CmRoomTime.scale_id == scale.id,
        ).first()

        if not room_pbs:
            message = (
                f'{runner.display_name} does not have any room personal '
                'bests.'
            )
            embed = error_to_embed('No room PBs found', message)
            await ctx.send(embed=embed)
            return

        embed = pb_cm_room_to_embed(room_pbs)
        await ctx.send(embed=embed)


@interactions.slash_command(
    name='pb_tob_rooms',
    description='Display a player\'s personal best for every room in a TOB raid',  # noqa
    options=[
        {
            "name": "scale",
            "description": "Enter the scale of the raid",
            "type": interactions.OptionType.INTEGER,
            "choices": scale_choices,
            "required": True
        },
        {
            "name": "runner",
            "description": (
                "Enter the names of the runner(s) (comma separated)"
            ),
            "type": interactions.OptionType.USER,
            "required": True
        }
    ]
)
async def pb_tob_rooms(
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
        room_pbs = session.query(TobRoomTime).filter(
            TobRoomTime.player_id == player.id,
            TobRoomTime.scale_id == scale.id,
        ).first()

        if not room_pbs:
            message = (
                f'{runner.display_name} does not have any room personal '
                'bests.'
            )
            embed = error_to_embed('No room PBs found', message)
            await ctx.send(embed=embed)
            return

        embed = pb_tob_room_to_embed(room_pbs)
        await ctx.send(embed=embed)


@interactions.slash_command(
    name='submit_cm_from_clipboard',
    description='Use the cox analytics plugin to paste in your room times',
    options=[
        {
            "name": "runners",
            "description": (
                "Enter the names of the runner(s) (comma separated)"
            ),
            "type": interactions.OptionType.STRING,
            "required": True
        },
        {
            "name": "room_times",
            "description": "Paste in your room times",
            "type": interactions.OptionType.STRING,
            "required": True
        }
    ]
)
async def submit_cm_from_clipboard(
    ctx: interactions.SlashContext,
    runners: str,
    room_times: str
):
    # Split the string into a list before every capital letter.
    capital_letters_at_start = r'[A-Z][^A-Z]*'
    room_times_list = re.findall(capital_letters_at_start, room_times)

    # Remove the last 6 elements as they are not useful, and remove elements
    # that do not contain a colon.
    clean_room_times = [x.lower() for x in room_times_list[:-6] if ':' in x]

    # Strip unneeded characters.
    clean_room_times = [
        x.replace(' ', '').replace('|', '') for x in clean_room_times
    ]

    # Split each element into a key value pair, e.g. {'tekton': '1:04.8', ...}
    room_times_dict = {
        x.split(':', 1)[0]: x.split(':', 1)[1] for x in clean_room_times
    }

    if not is_valid_cm_paste(room_times_dict):
        message = ('The room times submitted are not formatted correctly.')
        embed = error_to_embed('Submission', message)
        await ctx.send(embed=embed)
        return

    # Grab the scale from the string and then pop it so we do not run our time
    # function on it.
    scale = int(room_times_dict.pop('size'))

    # Convert the times to ticks.
    for room in room_times_dict:
        room_times_dict[room] = time_string_to_ticks(room_times_dict[room])

    # Store the total raid time and remove it from the dictionary to avoid the
    # get and set attr running on it.
    total_raid_time = room_times_dict.pop('completed')

    with get_session() as session:
        # Get the CoX: CM raid type.
        raid_type = session.query(RaidType).filter(
            RaidType.identifier == 'Chambers of Xeric: Challenge Mode'
        ).first()
        if not raid_type:
            message = 'No raid type found.'
            embed = error_to_embed('Submission', message)
            await ctx.send(embed=embed)
            return

        # Check if the scale exists in the database.
        raid_scale = session.query(Scale).filter(
            Scale.value == scale
        ).first()
        if not raid_scale:
            message = 'Invalid CM scale submitted.'
            embed = error_to_embed('Submission', message)
            await ctx.send(embed=embed)
            return

        print(f'Room times submitted: {room_times}')

        # Validate the runners submitted.
        formatted_runners_list = await validate_runners(ctx, runners, scale)
        if not formatted_runners_list:
            return

        # Get the group ID.
        players = get_players_from_discord_ids(formatted_runners_list)
        player_ids = [player.id for player in players]
        player_group_id = get_player_group_id(player_ids)

        # Add to speedrun_time table.
        # Check if this exact run has already been submitted.
        speedrun_time = session.query(SpeedrunTime).filter(
            SpeedrunTime.raid_type_id == raid_type.id,
            SpeedrunTime.scale_id == raid_scale.id,
            SpeedrunTime.player_group_id == player_group_id,
            SpeedrunTime.time == total_raid_time
        ).first()
        if not speedrun_time:
            # Save the run to the database.
            speedrun_time = SpeedrunTime(
                raid_type_id=raid_type.id,
                scale_id=raid_scale.id,
                player_group_id=player_group_id,
                time=total_raid_time
            )
            session.add(speedrun_time)
            session.flush()

        # Update individual room time PBs per player.
        player_times = {}
        for runner in players:
            # Get the player's best room times.
            best_times = session.query(CmRoomTime).filter(
                CmRoomTime.player_id == runner.id,
                CmRoomTime.scale_id == raid_scale.id
            ).first()

            if not best_times:
                new_run = CmRoomTime(
                    player_id=runner.id,
                    scale_id=raid_scale.id,
                    **room_times_dict
                )
                session.add(new_run)
                session.flush()
                continue

            before_after = best_times.update_room_times(room_times_dict)
            session.commit()

            if len(before_after) > 0:
                player_times[runner] = before_after

        if len(player_times) > 0:
            message = (
                'The room times submitted have been updated for the following '
                'rooms:\n'
            )

            for runner, before_after in player_times.items():
                for room, (before, after) in before_after.items():
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

        # Check if the run is a PB.
        better_run_exists = session.query(CmRaidTime).filter(
            CmRaidTime.speedrun_time_id == speedrun_time.id,
            CmRaidTime.completed <= total_raid_time
        ).first()
        if not better_run_exists:
            new_run = CmRaidTime(
                speedrun_time_id=speedrun_time.id,
                completed=total_raid_time,
                **room_times_dict
            )
            session.add(new_run)
            session.commit()
            message = (
                f'Submitted `{ticks_to_time_string(total_raid_time)}` in CoX: '
                f'CM with {raid_scale.identifier} scale.'
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
        {
            "name": "scale",
            "description": "Enter the scale of the raid",
            "type": interactions.OptionType.INTEGER,
            "choices": scale_choices,
            "required": True
        },
        {
            "name": "runner",
            "description": "Enter the name of the runner",
            "type": interactions.OptionType.USER,
            "required": True
        },
        {
            "name": "room",
            "description": "Enter the room you want to delete the PB for",
            "type": interactions.OptionType.STRING,
            "choices": cm_rooms,
            "required": True
        }
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
        room_pb = session.query(CmRoomTime).filter(
            CmRoomTime.scale_id == scale.id,
            CmRoomTime.player_id == player.id
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
        {
            "name": "scale",
            "description": "Enter the scale of the raid",
            "type": interactions.OptionType.INTEGER,
            "choices": scale_choices,
            "required": True
        },
        {
            "name": "runner",
            "description": "Enter the name of the runner",
            "type": interactions.OptionType.USER,
            "required": True
        }
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
        room_pbs = session.query(CmRoomTime).filter(
            CmRoomTime.scale_id == scale.id,
            CmRoomTime.player_id == player.id
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
        {
            "name": "runners",
            "description": (
                "Enter the names of the runner(s) (comma separated)"
            ),
            "type": interactions.OptionType.STRING,
            "required": True
        },
        {
            "name": "file",
            "description": "Submit a raid from a CSV file",
            "type": interactions.OptionType.ATTACHMENT,
            "required": True
        }
    ]
)
async def submit_tob_from_csv(
    ctx: interactions.SlashContext,
    runners: str,
    file: interactions.Attachment
):
    tobdata = await open_attachment(file)
    scale = None

    csv_ids = {
        '1': 'scale',
        '13': 'maiden_70',
        '14': 'maiden_50',
        '15': 'maiden_30',
        '17': 'maiden',
        '23': 'bloat',
        '35': 'nylocas_waves',
        '36': 'nylocas_cleanup',
        '45': 'nylocas',
        '52': 'sotetseg_maze1_start',
        '53': 'sotetseg_maze1_end',
        '54': 'sotetseg_maze2_start',
        '55': 'sotetseg_maze2_end',
        '57': 'sotetseg',
        '63': 'xarpus_screech',
        '65': 'xarpus',
        '73': 'verzik_p1',
        '80': 'verzik_reds',
        '74': 'verzik_p2',
        '76': 'verzik'
    }

    tob_times = {}

    for line in tobdata.strip().splitlines():
        parts = line.split(',')

        if len(parts) < 3:
            continue

        if parts[3] not in csv_ids:
            continue

        room_type = csv_ids.get(parts[3])

        if room_type == 'scale':
            players = [x for x in parts[-5:] if x]
            scale = len(players)
            print(f"Scale: {scale}")
            formatted_runners_list = await validate_runners(
                ctx, runners, scale
            )
            if not formatted_runners_list:
                break
            continue

        room_time = int(parts[4])
        tob_times[room_type] = room_time

    # Boss spawn is always 16 ticks after cleanup ends.
    tob_times['nylocas_bossspawn'] = tob_times['nylocas_cleanup'] + 16

    # Verzik p3 doesn't have an ID, so we calculate it manually.
    tob_times['verzik_p3'] = tob_times['verzik'] - tob_times['verzik_p2']

    # Calculate the total time.
    total_raid_time = (
        tob_times['maiden'] +
        tob_times['bloat'] +
        tob_times['nylocas'] +
        tob_times['sotetseg'] +
        tob_times['xarpus'] +
        tob_times['verzik']
    )

    with get_session() as session:
        raid_type = session.query(RaidType).filter(
            RaidType.identifier == 'Theatre of Blood'
        ).first()
        if not raid_type:
            message = 'No raid type found.'
            embed = error_to_embed('Submission', message)
            await ctx.send(embed=embed)
            return

        scale_type = session.query(Scale).filter(
            Scale.value == scale
        ).first()
        if not scale_type:
            message = 'Invalid scale submitted.'
            embed = error_to_embed('Submission', message)
            await ctx.send(embed=embed)
            return

        # Find the players in the database.
        players = get_players_from_discord_ids(formatted_runners_list)
        player_ids = [player.id for player in players]
        player_group_id = get_player_group_id(player_ids)

        # Add to speedrun_time table.
        # Check if this exact run has already been submitted.
        speedrun_time = session.query(SpeedrunTime).filter(
            SpeedrunTime.raid_type_id == raid_type.id,
            SpeedrunTime.scale_id == scale_type.id,
            SpeedrunTime.player_group_id == player_group_id,
            SpeedrunTime.time == total_raid_time
        ).first()
        if not speedrun_time:
            # Save the run to the database.
            speedrun_time = SpeedrunTime(
                raid_type_id=raid_type.id,
                scale_id=scale_type.id,
                player_group_id=player_group_id,
                time=total_raid_time
            )
            session.add(speedrun_time)
            session.flush()

        # Update individual room time PBs per player.
        player_times = {}
        for runner in players:
            # Get the player's best room times.
            best_times = session.query(TobRoomTime).filter(
                TobRoomTime.player_id == runner.id,
                TobRoomTime.scale_id == scale_type.id
            ).first()

            if not best_times:
                new_run = TobRoomTime(
                    player_id=runner.id,
                    scale_id=scale_type.id,
                    **tob_times
                )
                session.add(new_run)
                session.flush()
                continue

            before_after = best_times.update_room_times(tob_times)
            session.commit()

            if len(before_after) > 0:
                player_times[runner] = before_after

        if len(player_times) > 0:
            message = (
                'The room times submitted have been updated for the following '
                'rooms:\n'
            )

            for runner, before_after in player_times.items():
                for room, (before, after) in before_after.items():
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

        # Check if the run is a PB.
        better_run_exists = session.query(TobRaidTime).filter(
            TobRaidTime.speedrun_time_id == speedrun_time.id,
            TobRaidTime.completed <= total_raid_time
        ).first()
        if not better_run_exists:
            new_run = TobRaidTime(
                speedrun_time_id=speedrun_time.id,
                completed=total_raid_time,
                **tob_times
            )
            session.add(new_run)
            session.commit()
            message = (
                f'Submitted `{ticks_to_time_string(total_raid_time)}` '
                f'in ToB with {scale_type.identifier} scale.'
            )
            embed = confirmation_to_embed('Submission', message)
            await ctx.send(embed=embed)

            # Display the run in an embed.
            embed = pb_tob_raid_to_embed(new_run)
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
    name='delete_tob_room_pb',
    description='Delete a player\'s personal best for a room in a ToB raid',
    options=[
        {
            "name": "scale",
            "description": "Enter the scale of the raid",
            "type": interactions.OptionType.INTEGER,
            "choices": scale_choices,
            "required": True
        },
        {
            "name": "runner",
            "description": "Enter the name of the runner",
            "type": interactions.OptionType.USER,
            "required": True
        },
        {
            "name": "room",
            "description": "Enter the room you want to delete the PB for",
            "type": interactions.OptionType.STRING,
            "choices": cm_rooms,
            "required": True
        }
    ]
)
async def delete_tob_room_pb(
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
        room_pb = session.query(TobRoomTime).filter(
            TobRoomTime.scale_id == scale.id,
            TobRoomTime.player_id == player.id
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
    name='delete_all_tob_room_pb',
    description='Delete all room PBs for a player in a ToB raid',
    options=[
        {
            "name": "scale",
            "description": "Enter the scale of the raid",
            "type": interactions.OptionType.INTEGER,
            "choices": scale_choices,
            "required": True
        },
        {
            "name": "runner",
            "description": "Enter the name of the runner",
            "type": interactions.OptionType.USER,
            "required": True
        }
    ]
)
async def delete_all_tob_room_pb(
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
        room_pbs = session.query(TobRoomTime).filter(
            TobRoomTime.scale_id == scale.id,
            TobRoomTime.player_id == player.id
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


bot.start()
