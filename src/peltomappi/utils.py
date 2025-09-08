import re


def clean_string_to_filename(string: str) -> str:
    """
    Removes anything not alphanumeric or _ from a string.

    Returns:
        Cleaned up string.
    """

    return re.sub(r"\W+", "", string)
