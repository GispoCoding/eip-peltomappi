import re
from pathlib import Path


def clean_string_to_filename(string: str) -> str:
    """
    Converts a string into something that can be used as a filename or
    as part of a filename.

    Returns:
        Cleaned up string.
    """

    return re.sub(r"[/\\?%*:|\"<>\x7F\x00-\x1F]", "-", string)


def config_description_to_path(description: str, directory: Path | None = None) -> Path:
    """
    Converts a config description to a valid path.

    Args:
        description: input descriptions
        directory: folder in which path points to

    Returns:
        Cleaned and combined path.
    """
    if directory:
        return Path(directory / clean_string_to_filename(description).lower())

    return Path(clean_string_to_filename(description).lower())
