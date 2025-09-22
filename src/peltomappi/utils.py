import hashlib
import re

from pathlib import Path


def clean_string_to_filename(string: str) -> str:
    """
    Removes anything not alphanumeric or _ from a string.

    Returns:
        Cleaned up string.
    """

    return re.sub(r"\W+", "", string)


def sha256_file(path: Path) -> str:
    sha256 = hashlib.new("sha256")

    with open(path, "rb") as file:
        while chunk := file.read(8192):
            sha256.update(chunk)

    return sha256.hexdigest()
