"""Session is an aggregate with an invariant, not an Entity with a meta bag.

The regressions these guard: fifteen untyped `meta` keys, four `has_*` booleans
duplicating state that `x is not None` already told you, and a second copy of
the artifact-discovery rules in the site's asset staging.
"""

import pathlib

import pytest

from truehand.core.loaders import load_sessions
from truehand.core.session import Session, SessionArtifacts
from truehand.core.summary import SessionSummary


@pytest.fixture(scope="module")
def sessions(paths):
    return load_sessions(paths)


class TestInvariant:
    def test_a_folder_with_no_content_is_not_a_session(self):
        with pytest.raises(ValueError, match="at least one of"):
            Session("2026-01-01")

    @pytest.mark.parametrize("kwargs", [
        {"notes": "n"},
        {"transcript": "t"},
        {"summary": SessionSummary.parse("*In brief: x*")},
    ])
    def test_any_one_source_is_enough(self, kwargs):
        assert Session("2026-01-01", **kwargs).date == "2026-01-01"


class TestIdentity:
    def test_identity_is_the_date(self):
        s = Session("2026-06-16", notes="x")
        assert s.slug == "2026-06-16"
        assert s.name == "Session 2026-06-16"
        assert s.href == "session-2026-06-16.html"
        assert s.aliases == ["2026-06-16"]


class TestDerivedArtifactState:
    def test_absent_audio_derives_everything_consistently(self):
        s = Session("2026-06-16", notes="x")
        assert not s.has_audio and s.audio_name == ""
        assert not s.has_hero and s.hero_name == ""

    def test_published_names_are_date_based_whatever_the_source_is_called(self):
        s = Session("2026-06-16", notes="x", artifacts=SessionArtifacts(
            hero=pathlib.Path("sessions/2026-06-16/images/hero.png"),
            audio=pathlib.Path("sessions/2026-06-16/audio/final.mp3")))
        assert s.audio_name == "2026-06-16.mp3"
        assert s.hero_name == "2026-06-16.png"
        assert s.has_audio and s.has_hero

    def test_beat_image_is_looked_up_by_beat_not_by_re_slugging_html(self):
        doc = SessionSummary.parse("## Fog on the docks\n\nProse.\n")
        beat = doc.beats[0]
        path = pathlib.Path(f"images/{beat.slug}.jpg")
        s = Session("2026-06-16", summary=doc,
                    artifacts=SessionArtifacts(beats={beat.slug: path}))
        assert s.beat_image(beat) == path
        assert s.beat_image(SessionSummary.parse("## Elsewhere\n\np\n").beats[0]) is None


class TestBlurb:
    def test_prefers_the_summary_in_brief(self):
        s = Session("2026-06-16", notes="notes first line",
                    summary=SessionSummary.parse("*In brief: The lead line.*"))
        assert s.blurb == "The lead line."

    def test_falls_back_to_the_first_line_of_notes(self):
        assert Session("2026-06-16", notes="\n\nkill them\nup to level four").blurb == "kill them"

    def test_transcript_only_says_so(self):
        assert Session("2026-06-16", transcript="[00:00] hello").blurb.startswith("Transcript only")


class TestAgainstTheRealArchive:
    def test_sessions_load_oldest_first(self, sessions):
        dates = [s.date for s in sessions]
        assert dates == sorted(dates)

    def test_no_has_flag_can_disagree_with_its_artifact(self, sessions):
        for s in sessions:
            assert s.has_audio == (s.artifacts.audio is not None)
            assert s.has_hero == (s.artifacts.hero is not None)

    def test_every_discovered_artifact_exists_on_disk(self, sessions):
        for s in sessions:
            for path in filter(None, [s.artifacts.audio, s.artifacts.hero,
                                      *s.artifacts.beats.values()]):
                assert path.exists(), path

    def test_hero_is_never_filed_as_a_beat(self, sessions):
        assert all("hero" not in s.artifacts.beats for s in sessions)

    def test_the_library_folder_is_not_a_session(self, sessions):
        assert "library" not in {s.date for s in sessions}


class TestStagingCopiesWhatTheAggregateReports:
    def test_staged_names_match_the_aggregate(self, paths, tmp_path):
        from truehand.site.assets import _stage_session_media
        sessions = load_sessions(paths)
        _stage_session_media(sessions, tmp_path)
        for s in sessions:
            if s.has_audio:
                assert (tmp_path / "audio" / "sessions" / s.audio_name).exists()
            if s.has_hero:
                assert (tmp_path / "images" / "sessions" / s.hero_name).exists()
            for path in s.artifacts.beats.values():
                assert (tmp_path / "images" / "sessions" / s.date / path.name).exists()

    def test_staging_writes_nothing_the_aggregate_did_not_report(self, paths, tmp_path):
        sessions = load_sessions(paths)
        from truehand.site.assets import _stage_session_media
        _stage_session_media(sessions, tmp_path)
        expected = set()
        for s in sessions:
            if s.has_audio:
                expected.add(tmp_path / "audio" / "sessions" / s.audio_name)
            if s.has_hero:
                expected.add(tmp_path / "images" / "sessions" / s.hero_name)
            for path in s.artifacts.beats.values():
                expected.add(tmp_path / "images" / "sessions" / s.date / path.name)
        assert {p for p in tmp_path.rglob("*") if p.is_file()} == expected
