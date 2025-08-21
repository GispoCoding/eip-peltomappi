from pathlib import Path

import tempfile

from peltomappi.config import Config
from peltomappi.project import Project


def test_divider(
    dummy_project: Path,
    field_parcel_config: Path,
):
    temp_dir = tempfile.TemporaryDirectory()
    temp_dir_path = Path(temp_dir.name)

    config = Config(field_parcel_config)
    project = Project(
        dummy_project,
        output_directory=temp_dir_path,
        config=config,
    )

    project.create_subprojects()

    subproject_1_folder = temp_dir_path / "area1"
    subproject_2_folder = temp_dir_path / "area2"

    def test_subproject(folder: Path):
        assert folder.exists()
        assert (folder / "dummy").exists()
        assert (folder / "field_parcel_mock_ds.gpkg").exists()
        assert not (folder / "field_parcel_mock_ds.gpkg-shm").exists()
        assert not (folder / "field_parcel_mock_ds.gpkg-wal").exists()
        assert not (folder / "proj").exists()
        assert not (folder / ".mergin").exists()

    test_subproject(subproject_1_folder)
    test_subproject(subproject_2_folder)
