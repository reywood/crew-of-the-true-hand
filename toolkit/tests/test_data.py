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


class TestCampaignContentLivesInData:
    """§8 of the DDD review: campaign and show decisions belong in data/, not
    scattered through loaders, page renderers and pipeline modules."""

    def test_the_party_is_stated_once(self):
        """PC_DEFS, PC_SLUGS and the image prompts must agree on the roster."""
        from truehand.content.pc_identity import LEAN_CAST, PC_ANCHORS, PC_SLUGS
        from truehand.core.loaders import PC_DEFS
        assert tuple(PC_DEFS) == PC_SLUGS
        assert set(PC_ANCHORS) == set(PC_SLUGS) == set(LEAN_CAST)

    def test_every_pc_carries_its_own_name_in_its_aliases(self):
        from truehand.core.loaders import PC_DEFS
        for slug, pc in PC_DEFS.items():
            assert pc["name"] in pc["aliases"], slug
            assert pc["summary"] and pc["full_name"]

    def test_pc_files_and_portraits_exist_for_every_slug(self, paths):
        from truehand.core.loaders import PC_DEFS
        for slug in PC_DEFS:
            assert (paths.characters / f"{slug}.md").exists(), slug

    def test_standing_vocabulary_resolves(self):
        from truehand.core.loaders import PROVISIONAL, chip_for
        assert chip_for("Old shipmate") == ("Crew", "standing-crew")
        assert chip_for("Not a standing") is None
        assert chip_for("") is None
        assert "last known" in PROVISIONAL

    def test_every_npc_type_in_the_archive_has_a_chip(self, paths):
        """A `type:` missing from the vocabulary renders no chip at all and
        says nothing about it, so every type in use must be mapped."""
        from truehand.core.loaders import STANDING_MAP, load_dir_entities
        unmapped = {e.meta["type"].one() for e in load_dir_entities("npc", paths.npcs)
                    if e.meta["type"].one()} - set(STANDING_MAP)
        assert unmapped == set()

    def test_every_chip_class_is_styled(self, repo_root):
        """An unstyled standing-* class renders as unpainted text."""
        from truehand.core.loaders import STANDING_MAP
        css = (repo_root / "website" / "static" / "style.css").read_text(encoding="utf-8")
        for _label, cls in STANDING_MAP.values():
            assert f".{cls}" in css, cls

    def test_region_pins_are_declared_on_the_chart_not_in_the_renderer(self):
        from truehand import data
        pins = data.load("map")["locations"]
        regions = {slug for slug, d in pins.items() if d.get("region")}
        assert regions == {"spine-of-the-world", "silver-marches"}
        # A region label has no dot, so it has nothing to nudge a label away from.
        assert all("dir" not in pins[slug] for slug in regions)

    def test_every_charted_location_exists(self, paths):
        from truehand import data
        slugs = {p.stem for p in paths.locations.glob("*.md")}
        assert set(data.load("map")["locations"]) <= slugs


class TestAudioDirection:
    """These tables are inside the TTS cache key or spend ElevenLabs credits,
    so they get pinned harder than the rest."""

    def test_every_delivery_preset_is_complete_and_in_range(self):
        from truehand.pipelines.session_audio import DELIVERY_PRESETS
        assert len(DELIVERY_PRESETS) >= 50
        for name, preset in DELIVERY_PRESETS.items():
            assert set(preset) == {"stability", "similarity_boost", "style",
                                   "use_speaker_boost"}, name
            assert isinstance(preset["use_speaker_boost"], bool), name
            for key in ("stability", "similarity_boost", "style"):
                assert isinstance(preset[key], float), (name, key)
                assert 0.0 <= preset[key] <= 1.0, (name, key)

    def test_default_delivery_always_resolves(self):
        from truehand.pipelines.session_audio import resolve_delivery
        assert resolve_delivery("")[0] == "default"
        assert resolve_delivery("no such cue word")[0] == "default"
        assert resolve_delivery("hushed, drawing close")[0] == "hushed"

    def test_every_cue_asset_exists_in_the_library(self, paths):
        from truehand.pipelines import session_audio as sa
        library = paths.sessions / "library" / "audio"
        names = {entry[0] for entry in sa.STING_ASSETS.values()}
        names |= {entry[0] for entry in sa.MUSIC_ASSETS.values()}
        names |= {entry[0] for entry in sa.BED_OVERLAY_ASSETS.values()}
        names |= {sa.SIGNATURE_ASSET, sa.HEARTH_ASSET}
        missing = [n for n in sorted(names) if not (library / n).exists()]
        assert missing == []

    def test_bed_overlays_track_the_cold_open_level(self):
        """db_offset is relative, so retuning one level moves the family."""
        from truehand.pipelines.session_audio import BED_OVERLAY_ASSETS, COLD_OPEN_OVERLAY_DB
        assert BED_OVERLAY_ASSETS["tavern"][1] == COLD_OPEN_OVERLAY_DB
        assert BED_OVERLAY_ASSETS["bell tolling, faint"][1] == COLD_OPEN_OVERLAY_DB - 4.0
        assert BED_OVERLAY_ASSETS["bell tolling"][1] == COLD_OPEN_OVERLAY_DB - 2.0

    def test_every_delivery_cue_used_by_a_real_script_is_defined(self, paths):
        """An unknown cue silently falls back to 'default' — surface that."""
        import re

        from truehand.pipelines.session_audio import DELIVERY_PRESETS
        unmatched = set()
        for script in sorted(paths.sessions.glob("*/audio/script.md")):
            for line in script.read_text(encoding="utf-8").splitlines():
                m = re.match(r"^VANDAL:\s*\*\((.*?)\)\*", line.strip())
                if m and not any(w in DELIVERY_PRESETS
                                 for w in re.findall(r"[a-zA-Z']+", m.group(1).lower())):
                    unmatched.add(m.group(1))
        assert unmatched == set()
