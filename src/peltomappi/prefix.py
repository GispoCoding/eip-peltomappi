from enum import Enum

import click


class PrefixError(Exception):
    pass


def field_parcel(string: str) -> str:
    if not string.startswith("LandUse.ExistingLandUse.GSAAAgriculturalParcel."):
        msg = "invalid input for field parcel layer name"
        raise PrefixError(msg)

    return f"peltolohko_{string[-4:]}"


class PrefixType(Enum):
    # has to be a tuple in order for the function will be
    # considered an attribute
    FIELD_PARCEL = (field_parcel,)

    @staticmethod
    def to_choice() -> click.Choice:
        return click.Choice([option.name for option in PrefixType])
