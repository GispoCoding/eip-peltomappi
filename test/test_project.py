from pathlib import Path

import tempfile

from peltomappi.config import Config
from peltomappi.project import split_to_subprojects


def test_project(
    dummy_project: Path,
    field_parcel_config: Path,
    dummy_project_full_data: Path,
):
    temp_dir = tempfile.TemporaryDirectory()
    temp_dir_path = Path(temp_dir.name) / "output"

    config = Config(field_parcel_config)

    split_to_subprojects(
        template_project_directory=dummy_project,
        full_data_directory=dummy_project_full_data,
        output_directory=temp_dir_path,
        config=config,
    )

    subproject_1_folder = temp_dir_path / "area1"
    subproject_2_folder = temp_dir_path / "area2"

    def test_subproject(folder: Path):
        assert folder.exists()
        assert (folder / "peltomappi.qgs").exists()
        assert (folder / "mergin-config.json").exists()
        assert (folder / "field_parcel_mock_ds.gpkg").exists()
        assert not (folder / "field_parcel_mock_ds.gpkg-shm").exists()
        assert not (folder / "field_parcel_mock_ds.gpkg-wal").exists()
        assert not (folder / "proj").exists()
        assert not (folder / ".mergin").exists()

    test_subproject(subproject_1_folder)
    test_subproject(subproject_2_folder)
