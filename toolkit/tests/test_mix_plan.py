"""The mix policy is decided before any money is spent, so it can be tested.

What a cue means for the show — which cues open a bed, where the signature
headroom goes, what an unresolvable sting costs in silence — used to be
interleaved with the TTS calls and the ffmpeg invocations inside a ~200-line
pass over the script. None of it could run without an ElevenLabs key, so none
of it was tested; `resolve_bed_spans` had already been pulled out of the same
function for exactly this reason, and its docstring makes the argument.

These tests call no backend, spend nothing, and touch no audio.
"""

import itertools
import pathlib

import pytest

from truehand.core.episode_script import EpisodeScript
from truehand.pipelines.session_audio import (
    SIGNATURE_HEADROOM_MS,
    AssetPlay,
    BedMarker,
    Chapter,
    Gap,
    MixPlan,
    SpeechSlot,
    plan_mix,
    resolve_bed_spans,
)

LIBRARY = pathlib.Path("sessions/library/audio")


def _plan(markdown, **kw):
    return plan_mix(EpisodeScript.parse(markdown), LIBRARY, **kw)


def _kinds(plan):
    return [type(e).__name__ for e in plan.elements]


SCRIPT = """# Tales of the True Hand — 2026-01-01
## A Test of the Mix

[COLD OPEN — 25s]
[MUSIC: low ember bed; a distant tavern hum]
VANDAL: *(hushed)* A line in the dark.
[STING: sharp low chord, held — 3s]
[TITLE — 8s]
[MUSIC: signature theme]
VANDAL: *(signature)* I am Vandal Lovelace.

## ACT ONE — The Thing That Happened
[MUSIC: settles under, becomes bed]
VANDAL: *(storyteller)* And then it happened.
[STING: chime]

## CLOSING
[MUSIC: minor swell]
VANDAL: *(closing)* This has been a Tale.
"""


class TestTheShapeOfAPlan:
    def test_every_spoken_line_becomes_a_slot_in_order(self):
        plan = _plan(SCRIPT)
        assert [s.index for s in plan.speech] == [0, 1, 2, 3]
        assert plan.speech[1].text == "I am Vandal Lovelace."

    def test_a_delivery_cue_resolves_to_a_preset(self):
        plan = _plan(SCRIPT)
        assert plan.speech[0].delivery_key == "hushed"
        assert plan.speech[0].settings

    def test_an_unknown_delivery_cue_falls_back_to_default(self):
        plan = _plan("# T — 2026-01-01\n## S\nVANDAL: *(bewildered)* Eh?\n")
        assert plan.speech[0].delivery_key == "default"

    def test_chapter_marks_survive_as_zero_duration_elements(self):
        """Titles arrive title-cased from the parser, not as the script shouts
        them."""
        titles = [e.title for e in _plan(SCRIPT).elements if isinstance(e, Chapter)]
        assert titles == ["Act One — The Thing That Happened", "Closing"]

    def test_the_plan_carries_no_positions(self):
        """Where a bed opens depends on how long the narration ran, which is
        not knowable until the audio exists. The executor stamps the clock."""
        for el in _plan(SCRIPT).elements:
            assert not hasattr(el, "at_ms")


class TestBeds:
    def test_the_ember_cue_opens_the_cold_open_bed(self):
        beds = [e for e in _plan(SCRIPT).elements if isinstance(e, BedMarker)]
        assert beds[0].kind == "start_cold_open"

    def test_the_signature_cue_opens_its_own_bed(self):
        beds = [e for e in _plan(SCRIPT).elements if isinstance(e, BedMarker)]
        assert beds[1].kind == "start_signature"

    def test_settles_under_opens_the_hearth_bed(self):
        beds = [e for e in _plan(SCRIPT).elements if isinstance(e, BedMarker)]
        assert beds[2].kind == "start_hearth"

    def test_the_minor_swell_closes_whatever_is_open(self):
        beds = [e for e in _plan(SCRIPT).elements if isinstance(e, BedMarker)]
        assert beds[-1].kind == "end"

    def test_the_signature_headroom_follows_its_marker_immediately(self):
        """The theme must play alone for a beat before the title line."""
        els = _plan(SCRIPT).elements
        i = next(i for i, e in enumerate(els) if isinstance(e, BedMarker) and "signature" in e.kind)
        nxt = els[i + 1]
        assert isinstance(nxt, Gap) and nxt.duration_ms == SIGNATURE_HEADROOM_MS


class TestMuteFlags:
    def test_no_beds_keeps_discrete_cues_but_lays_no_bed(self):
        plan = _plan(SCRIPT, beds=False)
        assert not any(isinstance(e, BedMarker) for e in plan.elements)
        assert any(isinstance(e, AssetPlay) for e in plan.elements)

    def test_no_beds_also_drops_the_signature_headroom(self):
        """The headroom exists to make room for a bed that is no longer there."""
        gaps = [e for e in _plan(SCRIPT, beds=False).elements if isinstance(e, Gap)]
        assert all(g.duration_ms != SIGNATURE_HEADROOM_MS for g in gaps)

    def test_no_music_silences_every_asset(self):
        plan = _plan(SCRIPT, music=False)
        assert not any(isinstance(e, AssetPlay) for e in plan.elements)
        assert not any(isinstance(e, BedMarker) for e in plan.elements)

    def test_a_muted_sting_still_costs_its_beat(self):
        """Pacing around a cue survives muting it."""
        plan = _plan(SCRIPT, music=False)
        assert any(g.duration_ms == 400 for g in plan.elements if isinstance(g, Gap))

    def test_no_music_leaves_the_narration_untouched(self):
        assert len(_plan(SCRIPT, music=False).speech) == len(_plan(SCRIPT).speech)


class TestUnresolvableCues:
    def test_an_unknown_sting_degrades_to_a_beat_of_silence(self):
        plan = _plan("# T — 2026-01-01\n## S\n[STING: a noise nobody sampled]\n")
        gaps = [e for e in plan.elements if isinstance(e, Gap)]
        assert [g.duration_ms for g in gaps] == [500]

    def test_an_unknown_music_cue_plays_nothing_at_all(self):
        """Unlike a sting, a music cue that resolves to nothing takes no time."""
        plan = _plan("# T — 2026-01-01\n## S\n[MUSIC: a tune nobody wrote]\n")
        assert not any(isinstance(e, (AssetPlay, Gap)) for e in plan.elements)

    def test_a_bed_cue_is_never_also_an_inline_asset(self):
        plan = _plan("# T — 2026-01-01\n## S\n[MUSIC: low ember bed; a hum]\n")
        assert any(isinstance(e, BedMarker) for e in plan.elements)
        assert not any(isinstance(e, AssetPlay) for e in plan.elements)


class TestAgainstEveryRealScript:
    @pytest.mark.parametrize(
        "script_path",
        sorted(pathlib.Path("sessions").glob("*/audio/script.md")),
        ids=lambda p: p.parent.parent.name,
    )
    def test_each_episode_plans_without_a_backend(self, script_path):
        plan = plan_mix(EpisodeScript.parse(script_path.read_text(encoding="utf-8")), LIBRARY)
        assert plan.speech, "an episode with no narration"
        assert plan.count(SpeechSlot) == len(plan.speech)

    @pytest.mark.parametrize(
        "script_path",
        sorted(pathlib.Path("sessions").glob("*/audio/script.md")),
        ids=lambda p: p.parent.parent.name,
    )
    def test_every_asset_a_real_script_asks_for_is_in_the_library(self, script_path):
        """A cue naming an asset nobody committed would render as a silent
        gap in the finished episode."""
        plan = plan_mix(EpisodeScript.parse(script_path.read_text(encoding="utf-8")), LIBRARY)
        assets = [e for e in plan.elements if isinstance(e, AssetPlay)]
        missing = [e.label for e in assets if not e.source.exists()]
        assert missing == []

    @pytest.mark.parametrize(
        "script_path",
        sorted(pathlib.Path("sessions").glob("*/audio/script.md")),
        ids=lambda p: p.parent.parent.name,
    )
    def test_bed_markers_resolve_to_non_overlapping_spans(self, script_path):
        """Fed to the executor's clock, every real script yields a sane bed
        timeline — this is what pass 2 consumes."""
        plan = plan_mix(EpisodeScript.parse(script_path.read_text(encoding="utf-8")), LIBRARY)
        markers = [
            {"at_ms": i * 1000, "kind": e.kind, "label": e.label}
            for i, e in enumerate(plan.elements)
            if isinstance(e, BedMarker)
        ]
        spans = resolve_bed_spans(markers, len(plan.elements) * 1000)
        for a, b in itertools.pairwise(spans):
            assert a.end_ms <= b.start_ms, f"{a} overlaps {b}"


class TestMixPlanItself:
    def test_count_matches_the_elements(self):
        plan = _plan(SCRIPT)
        assert plan.count(SpeechSlot) == 4
        assert plan.count(Chapter) == len([k for k in _kinds(plan) if k == "Chapter"])

    def test_an_empty_script_plans_to_nothing(self):
        assert MixPlan(()).speech == []
