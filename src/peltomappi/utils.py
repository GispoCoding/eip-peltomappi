import hashlib
import re

from pathlib import Path
from peltomappi.exception import InvalidPeltomappiFileError, MissingPeltomappiFileError

FIELD_PARCEL_FILE_PREFIX = "Peltolohkot_"


def clean_string_to_filename(string: str) -> str:
    """Remove anything not alphanumeric or _ from a string.

    Returns:
        Cleaned up string.

    """
    return re.sub(r"\W+", "", string)


def sha256_file(path: Path) -> str:
    """Calculate SHA256 of a file.

    Returns:
        Hexdigest of SHA256 value of the given file.

    """
    sha256 = hashlib.new("sha256")

    with open(path, "rb") as file:
        while chunk := file.read(8192):
            sha256.update(chunk)

    return sha256.hexdigest()


def representative_field_parcel_dataset(full_data_directory: Path) -> Path:
    """Determine representative (latest) field parcel dataset.

    Returns:
        Path to dataset.

    Raises:
        InvalidPeltomappiFileError: If incorrect type of file with field parcel
            prefix is found.

    """
    files = list(full_data_directory.glob(f"{FIELD_PARCEL_FILE_PREFIX}*"))

    if not files:
        msg = "No field parcel dataset files found."
        raise MissingPeltomappiFileError(msg)

    for file in files:
        if not file.name.endswith(".gpkg"):
            msg = "Non-GeoPackage field parcel dataset found."
            raise InvalidPeltomappiFileError(msg)

        split = file.stem.split("_")

        if len(split) != 2:
            msg = "Invalid name for field parcel dataset."
            raise InvalidPeltomappiFileError(msg)

        year_str = split[1]

        if not year_str.isdigit():
            msg = "Field parcel file does not contain number correctly."
            raise InvalidPeltomappiFileError(msg)

    files.sort(key=lambda path: int(path.stem.split("_")[1]), reverse=True)

    return files[0]
