"""find_root() and the Paths model.

The regression that matters most here is the toolkit/pyproject.toml trap: an
upward walk keyed on a packaging file would stop inside toolkit/ and never
reach the archive.
"""

import dataclasses
import pathlib
import shutil

import pytest

from truehand.errors import UserError
from truehand.paths import MARKERS, ROOT_ENV_VAR, Paths, find_root, is_archive_root


@pytest.fixture
def fake_archive(tmp_path: pathlib.Path) -> pathlib.Path:
    (tmp_path / "campaign-state.md").write_text("---\nobjective: x\n---\n")
    (tmp_path / "quests.md").write_text("# Quests\n")
    (tmp_path / "sessions").mkdir()
    (tmp_path / "sessions" / "2026-01-01").mkdir()
    return tmp_path


def test_finds_root_from_the_root(fake_archive):
    assert find_root(fake_archive) == fake_archive


def test_finds_root_from_a_session_dir(fake_archive):
    assert find_root(fake_archive / "sessions" / "2026-01-01") == fake_archive


def test_does_not_stop_at_a_nested_pyproject(fake_archive):
    """The whole reason MARKERS is not ('pyproject.toml',)."""
    nested = fake_archive / "toolkit" / "src" / "truehand"
    nested.mkdir(parents=True)
    (fake_archive / "toolkit" / "pyproject.toml").write_text("[project]\n")
    assert find_root(nested) == fake_archive


def test_env_var_overrides_the_walk(fake_archive, tmp_path, monkeypatch):
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.setenv(ROOT_ENV_VAR, str(fake_archive))
    assert find_root(elsewhere) == fake_archive


def test_env_var_pointing_at_a_non_archive_raises(tmp_path, monkeypatch):
    monkeypatch.setenv(ROOT_ENV_VAR, str(tmp_path))
    with pytest.raises(UserError, match=ROOT_ENV_VAR):
        find_root()


def test_no_archive_anywhere_raises(tmp_path, monkeypatch):
    monkeypatch.delenv(ROOT_ENV_VAR, raising=False)
    with pytest.raises(UserError, match="not inside a campaign archive"):
        find_root(tmp_path)


@pytest.mark.parametrize("missing", MARKERS)
def test_every_marker_is_required(fake_archive, missing, monkeypatch):
    monkeypatch.delenv(ROOT_ENV_VAR, raising=False)
    target = fake_archive / missing
    if target.is_dir():
        shutil.rmtree(target)
    else:
        target.unlink()
    assert not is_archive_root(fake_archive)


def test_paths_are_derived_from_one_root(fake_archive):
    p = Paths.at(fake_archive)
    assert p.site == fake_archive / "website" / "site"
    assert p.static == fake_archive / "website" / "static"
    assert p.audio_credits == fake_archive / "sessions" / "library" / "audio" / "CREDITS.md"
    assert p.session_audio("2026-01-01") == fake_archive / "sessions" / "2026-01-01" / "audio"


def test_paths_is_frozen(fake_archive):
    p = Paths.at(fake_archive)
    with pytest.raises(dataclasses.FrozenInstanceError):
        p.root = fake_archive  # type: ignore[misc]


def test_real_archive_is_detected(paths):
    assert is_archive_root(paths.root)
    assert paths.quests_file.exists()
