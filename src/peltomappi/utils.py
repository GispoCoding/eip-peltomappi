import re


def clean_string_to_filename(string: str) -> str:
    """
    Converts a string into something that can be used as a filename or
    as part of a filename.
    """

    return re.sub(r"[/\\?%*:|\"<>\x7F\x00-\x1F]", "-", string)
