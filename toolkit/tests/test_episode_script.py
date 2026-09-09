"""One parser for script.md, in one place.

The regression this guards: two parsers read the podcast script. `parse_script`
walked it properly while `core/loaders._read_audio_subtitle` opened it again
and sliced line 2 with two readline() calls, so a blank line after the H1 cost
the episode its title in feed.xml and in the session page's share metadata.
"""

import pytest

from truehand.core.episode_script import (
    ChapterMark,
    EpisodeScript,
    MusicCue,
    Silence,
    Speak,
    StingCue,
    _chapter_title,
)

SCRIPT = """# Tales of the True Hand — 2026-06-16
## Milk-White Eyes at the Deep Water Inn

---

## [COLD OPEN — 25s]

[MUSIC: low ember bed; a distant tavern hum]

VANDAL: *(hushed, drawing close)* Listen. There came a night.

[STING: sharp low chord]

## [TITLE — 8s]

VANDAL: *(signature)* I am Vandal Lovelace.

## ACT ONE — The Wazoo

VANDAL: They came ashore in the dark.

[PAUSE 2s]

## CLOSING

VANDAL: *(closing)* This has been a Tale of the True Hand.
"""


@pytest.fixture(scope="module")
def script():
    return EpisodeScript.parse(SCRIPT)


class TestEpisodeTitle:
    def test_reads_the_title(self, script):
        assert script.episode_title == "Milk-White Eyes at the Deep Water Inn"

    def test_survives_a_blank_line_after_the_h1(self):
        """The old two-readline reader returned "" here and the episode
        silently lost its name in the feed."""
        doc = EpisodeScript.parse(
            "# Tales of the True Hand — 2099-01-01\n\n## The Real Title\n\nVANDAL: *(warm)* Hi.\n"
        )
        assert doc.episode_title == "The Real Title"

    def test_a_bracketed_section_is_not_the_title(self):
        doc = EpisodeScript.parse(
            "# Tales of the True Hand — 2099-01-01\n\n## [COLD OPEN — 25s]\n\nVANDAL: Hi.\n"
        )
        assert doc.episode_title == ""

    def test_a_title_beginning_with_acts_is_not_an_act(self):
        """`ACT\\b` matters: "Acts of the Deep Speaker" is a name, not an act."""
        doc = EpisodeScript.parse(
            "# Tales of the True Hand — 2099-01-01\n## Acts of the Deep Speaker\n\nVANDAL: Hi.\n"
        )
        assert doc.episode_title == "Acts of the Deep Speaker"
        assert doc.count(ChapterMark) == 0


class TestEvents:
    def test_spoken_lines_carry_their_delivery(self, script):
        first = script.spoken_lines[0]
        assert first.text == "Listen. There came a night."
        assert first.delivery == "hushed, drawing close"

    def test_a_line_with_no_cue_still_parses(self, script):
        plain = [line for line in script.spoken_lines if not line.delivery]
        assert plain and plain[0].text == "They came ashore in the dark."

    def test_cues_are_typed_and_keep_their_label(self, script):
        assert [e.label for e in script.events if isinstance(e, MusicCue)] == [
            "low ember bed; a distant tavern hum"
        ]
        assert [e.label for e in script.events if isinstance(e, StingCue)] == ["sharp low chord"]

    def test_chapters_are_the_cold_open_acts_and_close(self, script):
        assert [e.title for e in script.events if isinstance(e, ChapterMark)] == [
            "Cold Open",
            "Act One — The Wazoo",
            "Closing",
        ]

    def test_the_title_card_is_too_short_to_chapter(self):
        assert _chapter_title("## [TITLE — 8s]") is None

    def test_every_line_is_followed_by_a_gap(self, script):
        for i, e in enumerate(script.events):
            if isinstance(e, Speak):
                assert isinstance(script.events[i + 1], Silence)

    def test_consecutive_gaps_collapse(self):
        """A pause after a line must not stack with the line's own gap."""
        doc = EpisodeScript.parse("VANDAL: Hi.\n\n[PAUSE 2s]\n")
        gaps = [e for e in doc.events if isinstance(e, Silence)]
        assert len(gaps) == 1 and gaps[0].duration_ms == 250 + 2000

    def test_character_count_is_spoken_text_only(self, script):
        """Cue lines and delivery cues are not billed."""
        assert script.character_count == sum(len(line.text) for line in script.spoken_lines)
        assert "MUSIC" not in "".join(line.text for line in script.spoken_lines)


class TestAgainstTheRealArchive:
    def test_every_script_has_a_title_and_lines(self, paths):
        scripts = sorted(paths.sessions.glob("*/audio/script.md"))
        assert len(scripts) >= 10
        for path in scripts:
            doc = EpisodeScript.parse(path.read_text(encoding="utf-8"))
            assert doc.episode_title, path
            assert doc.spoken_lines, path

    def test_the_session_artifacts_title_matches_the_script(self, paths):
        from truehand.core.loaders import load_sessions

        for session in load_sessions(paths):
            script = paths.session_audio(session.date) / "script.md"
            if not script.exists():
                continue
            assert (
                session.artifacts.episode_title
                == EpisodeScript.parse(script.read_text(encoding="utf-8")).episode_title
            )
