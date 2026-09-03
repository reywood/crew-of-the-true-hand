"""slugify and asset_slug — which look like the same function and are not."""

import pytest

from truehand.core.text import slugify


@pytest.mark.parametrize("raw,expected", [
    ("What's next", "whats-next"),          # load-bearing: beat-image lookup
    ("What’s next", "whats-next"),     # curly apostrophe
    ("The Cambion at the Gate", "the-cambion-at-the-gate"),
    ("Act One — Set down among the wheat", "act-one-set-down-among-the-wheat"),
    ("Ink & Iron", "ink-iron"),
    ("  leading and trailing  ", "leading-and-trailing"),
    ("under_scores", "under-scores"),
    ("multiple   spaces", "multiple-spaces"),
    ("---edges---", "edges"),
])
def test_slugify(raw, expected):
    assert slugify(raw) == expected


def test_slugify_matches_the_beat_images_on_disk(paths):
    """Beat images are matched by slug; a change here silently unlinks them."""
    from truehand.core.text import slugify as s
    checked = 0
    for summary in sorted(paths.sessions.glob("*/summary.md")):
        img_dir = summary.parent / "images"
        if not img_dir.exists():
            continue
        stems = {p.stem for p in img_dir.glob("*.jpg")} - {"hero"}
        if not stems:
            continue
        headings = {s(line[3:].strip())
                    for line in summary.read_text(encoding="utf-8").splitlines()
                    if line.startswith("## ")}
        assert stems <= headings, (
            f"{summary.parent.name}: images with no matching heading: "
            f"{sorted(stems - headings)}"
        )
        checked += 1
    assert checked >= 5, f"only checked {checked} sessions"


def test_asset_slug_is_deliberately_different_from_slugify():
    """The audio pipeline's slug truncates at 40 chars and names *cached*
    files. Merging the two would rename every cached asset."""
    import re

    from truehand.core.text import slugify as site_slug
    label = "a very long music cue label that certainly exceeds forty characters"
    audio_slug = re.sub(r"[^a-z0-9]+", "-", label.lower())[:40].strip("-")
    assert len(audio_slug) <= 40
    assert site_slug(label) != audio_slug
