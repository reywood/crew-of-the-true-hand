"""The site build must stay byte-identical to the committed website/site/.

website/site/ is tracked in git, so the committed tree *is* the golden master.
This test rebuilds into a tmp dir and compares. It is the gate for the whole
package migration: no refactor may change a single output byte.

The build's only nondeterminism is the ffprobe call behind <itunes:duration>,
so a frozen duration table is injected instead — the test then needs no ffmpeg
and runs in about a second.
"""

import difflib
import json
import pathlib

import pytest

from truehand.site.build import DEFAULT_BASE_URL, build_site

BINARY_SUFFIXES = {".mp3", ".jpg", ".jpeg", ".png", ".webp", ".ico"}


@pytest.fixture(scope="module")
def frozen_probe(repo_root):
    """Durations captured from the real ffprobe, keyed by repo-relative path."""
    table = json.loads(
        (pathlib.Path(__file__).parent / "fixtures" / "durations.json").read_text()
    )

    def probe(path):
        rel = pathlib.Path(path).resolve().relative_to(repo_root).as_posix()
        assert rel in table, f"no frozen duration for {rel}; regenerate durations.json"
        return table[rel]

    return probe


def _tree(root):
    return {p.relative_to(root) for p in root.rglob("*") if p.is_file()}


def _explain(actual: pathlib.Path, expected: pathlib.Path, rel) -> str:
    a = actual.read_text(encoding="utf-8", errors="replace").splitlines()
    b = expected.read_text(encoding="utf-8", errors="replace").splitlines()
    diff = list(difflib.unified_diff(b, a, "committed", "rebuilt", lineterm=""))
    return f"{rel} differs:\n" + "\n".join(diff[:40])


@pytest.fixture(scope="module")
def rebuilt(paths, frozen_probe, tmp_path_factory):
    out = tmp_path_factory.mktemp("site")
    result = build_site(paths, base_url=DEFAULT_BASE_URL, out_dir=out, probe=frozen_probe)
    return out, result


def test_at_least_one_episode(rebuilt):
    """Guards the datetime.now() fallbacks in podcast_feed from ever firing."""
    _, result = rebuilt
    assert result["episodes"] > 0


def test_same_file_set(rebuilt, paths):
    out, _ = rebuilt
    assert _tree(out) == _tree(paths.site)


def test_every_file_is_byte_identical(rebuilt, paths):
    out, _ = rebuilt
    mismatches = []
    for rel in sorted(_tree(paths.site), key=str):
        actual, expected = out / rel, paths.site / rel
        if expected.suffix.lower() in BINARY_SUFFIXES:
            if actual.stat().st_size != expected.stat().st_size:
                mismatches.append(f"{rel}: size differs")
        elif actual.read_bytes() != expected.read_bytes():
            mismatches.append(_explain(actual, expected, rel))
    assert not mismatches, "\n\n".join(mismatches[:5])
