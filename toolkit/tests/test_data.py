"""The TOML campaign data.

These files are hand-edited when a session is added or a chart pin moves, so
the parse is worth guarding: a malformed entry would otherwise surface as a
missing chip or a pin at (0, 0) rather than an error.
"""

import pytest

from truehand import data
from truehand.core.loaders import SESSION_LOCATIONS
from truehand.site.pages.locations import CARTOUCHE_ORDER, LOCATION_MAP_DATA


def test_every_session_folder_has_a_locations_entry(paths):
    on_disk = {p.name for p in paths.sessions.iterdir()
               if p.is_dir() and p.name != "library"}
    missing = on_disk - set(SESSION_LOCATIONS)
    assert not missing, f"sessions with no SESSION_LOCATIONS entry: {sorted(missing)}"


def test_no_entry_for_a_session_that_does_not_exist(paths):
    on_disk = {p.name for p in paths.sessions.iterdir() if p.is_dir()}
    assert not set(SESSION_LOCATIONS) - on_disk


def test_session_location_slugs_resolve_to_real_files(paths):
    known = {p.stem for p in paths.locations.glob("*.md")}
    for date, slugs in SESSION_LOCATIONS.items():
        for slug in slugs:
            assert slug in known, f"{date} references unknown location '{slug}'"


def test_map_slugs_resolve_to_real_files(paths):
    known = {p.stem for p in paths.locations.glob("*.md")}
    for slug in LOCATION_MAP_DATA:
        assert slug in known, f"map.toml pins unknown location '{slug}'"


@pytest.mark.parametrize("slug,entry", sorted(LOCATION_MAP_DATA.items()))
def test_each_map_entry_is_a_pin_or_a_cartouche(slug, entry):
    if "cartouche" in entry:
        assert entry["cartouche"] in CARTOUCHE_ORDER, \
            f"{slug} uses cartouche '{entry['cartouche']}' not in cartouche_order"
        assert "x" not in entry and "y" not in entry
    else:
        assert 0 <= entry["x"] <= 100 and 0 <= entry["y"] <= 100, \
            f"{slug} pin is off the chart"
        if "dir" in entry:
            assert entry["dir"] in {"n", "s", "e", "w", "ne", "nw", "se", "sw"}


def test_data_load_is_cached():
    assert data.load("map") is data.load("map")
