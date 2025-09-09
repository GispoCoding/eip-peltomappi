from pathlib import Path


def testdata_path() -> Path:
    return Path(__file__).resolve().parent.parent / "testdata"
