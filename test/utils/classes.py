import shutil
import tempfile
from typing import Any, NamedTuple

from pathlib import Path

from peltomappi.composition import Composition, CompositionBackend


class CompositionBackendTest(CompositionBackend):
    __projects_path: Path

    def __init__(self, projects_path: Path) -> None:
        self.__projects_path = projects_path

    def download_project(self, project_name: str, destination: Path) -> None:
        shutil.copytree(self.__projects_path / project_name, destination)

    def upload_project(self, project_name: str, directory: Path) -> None:
        shutil.copytree(directory, self.__projects_path / project_name)

    def projects_list(self, workspace: str) -> list[str]:
        return [dir.stem for dir in self.__projects_path.iterdir() if dir.stem != "template"]

    def pull_project(self, directory: Path) -> Any:
        pass


class ContainedComposition(NamedTuple):
    """
    Helper class for testing, contains a composition and holds a reference to
    its temporary output directory, so it exists for the duration the
    composition is used for.
    """

    temp_dir: tempfile.TemporaryDirectory
    composition: Composition
