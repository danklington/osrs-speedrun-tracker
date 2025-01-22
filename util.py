def format_discord_ids(discord_ids: list[str]) -> list[int]:
    """IDs when submitted as a string come through as '<@000000000000000000>'.
       This function strips the '<@>' and returns the ID as an integer.
    """

    return [int(_id[2:-1]) for _id in discord_ids]


def string_to_ticks(time: str) -> int:
    """Converts a string time to ticks."""

    pass