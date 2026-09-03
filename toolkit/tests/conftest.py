import pathlib

import pytest

from truehand.paths import Paths, find_root


@pytest.fixture(scope="session")
def repo_root() -> pathlib.Path:
    """The real campaign archive this checkout lives in."""
    return find_root(pathlib.Path(__file__).resolve().parent)


@pytest.fixture(scope="session")
def paths(repo_root: pathlib.Path) -> Paths:
    return Paths.at(repo_root)
