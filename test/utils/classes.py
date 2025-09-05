import tempfile
from typing import NamedTuple

from peltomappi.composition import Composition


class ContainedComposition(NamedTuple):
    """
    Helper class for testing, contains a composition and holds a reference to
    its temporary output directory, so it exists for the duration the
    composition is used for.
    """

    temp_dir: tempfile.TemporaryDirectory
    composition: Composition
