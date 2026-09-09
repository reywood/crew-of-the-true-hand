"""The "Tales of the True Hand" script as a parsed document.

`sessions/<date>/audio/script.md` has a specified shape (CLAUDE.md, step 2.7):
an H1 naming the show and date, a line-2 `## <episode title>`, then bracketed
section headings — `[COLD OPEN]`, `[TITLE]`, `## ACT ONE`, `[CLOSING]` — with
every spoken line prefixed `VANDAL: *(delivery cue)*` and `[MUSIC: …]` /
`[STING: …]` cues between them.

Two parsers used to read this file. `parse_script` walked it properly, while
`core/loaders._read_audio_subtitle` opened it separately and sliced line 2 with
two `readline()` calls — so a blank line after the H1 silently cost the episode
its title in `feed.xml` and in the session page's share metadata. This is the
same disease `core/summary.py` was written to cure for `summary.md`, and the
cure is the same: one parser, one document object.

**Why this lives in `core/` rather than beside the audio pipeline.** `core/` is
where the archive's *documents* are read — frontmatter, `summary.md`,
`quests.md`, `campaign-state.md` — and `script.md` is another file in the
session folder. Putting the parser in `pipelines/` would make `core` import
from `pipelines` to learn an episode's title, inverting the one dependency rule
the package actually enforces. What stays in `pipelines/session_audio.py` is
everything that *produces* an episode: what a cue means for the mix, which
asset it pulls, how loud it sits, and the TTS. This module only says what the
document contains.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace

#: The show has one narrator, and every spoken line is his.
NARRATOR = "VANDAL"

#: Inserted after each spoken line so the delivery has room to land.
LINE_GAP_MS = 250

_SFX_MS = 350
_DEFAULT_PAUSE_MS = 500


@dataclass(frozen=True)
class Speak:
    """One line of narration, with the delivery cue that colours it."""

    text: str
    delivery: str = ""


@dataclass(frozen=True)
class Silence:
    duration_ms: int


@dataclass(frozen=True)
class MusicCue:
    """A `[MUSIC: …]` cue. What the label *means* for the mix is the audio
    pipeline's business; this only carries it."""

    label: str


@dataclass(frozen=True)
class StingCue:
    label: str


@dataclass(frozen=True)
class ChapterMark:
    """A zero-duration ID3 chapter boundary: the cold open, an act, the close."""

    title: str


def _chapter_title(heading: str) -> str | None:
    """The chapter a section heading opens, or None if it opens none.

    Chapters are the cold open, each act, and the closing. The H1 show title,
    the episode title and the short `[TITLE]` card are not chapters.
    """
    m = re.match(r"^(#+)\s*(.*)$", heading.strip())
    if not m or len(m.group(1)) != 2:          # only H2 headings are sections
        return None
    text = m.group(2).strip()
    # Some scripts bracket their section headings and some don't. Unwrap, then
    # treat both alike.
    if bracket := re.match(r"^\[(.+?)\]$", text):
        text = bracket.group(1).strip()
    keyword = re.split(r"\s*[—–-]\s*", text, maxsplit=1)[0].strip().upper()
    if keyword == "COLD OPEN":
        return "Cold Open"
    if keyword == "CLOSING":
        return "Closing"
    if keyword == "TITLE":
        return None                            # the title card is too short
    # \b matters: an episode called "Acts of the Deep Speaker" is not an act.
    if re.match(r"^ACT\b", text, re.IGNORECASE):
        parts = re.split(r"\s*[—–]\s*", text, maxsplit=1)
        label = parts[0].strip().title()       # "ACT ONE" -> "Act One"
        if len(parts) == 2 and parts[1].strip():
            return f"{label} — {parts[1].strip()}"
        return label
    return None                                # the episode title, etc.


@dataclass(frozen=True)
class EpisodeScript:
    """A parsed `script.md`."""

    episode_title: str
    events: tuple[object, ...]

    @classmethod
    def parse(cls, markdown: str) -> EpisodeScript:
        events: list[object] = []
        title = ""

        def add_silence(ms: int):
            """Consecutive gaps collapse into one, so a pause after a line
            does not stack with the line's own trailing gap."""
            if events and isinstance(events[-1], Silence):
                events[-1] = replace(events[-1], duration_ms=events[-1].duration_ms + ms)
            else:
                events.append(Silence(ms))

        for raw in (markdown or "").split("\n"):
            line = raw.strip()
            if not line:
                continue

            if line.startswith("#"):
                if chapter := _chapter_title(line):
                    events.append(ChapterMark(chapter))
                elif not title and not events and line.startswith("## "):
                    # The first H2 that opens no chapter, before any content,
                    # is the episode title — however many blank lines or rules
                    # sit between it and the H1.
                    candidate = line[3:].strip()
                    if not candidate.startswith("["):
                        title = candidate
                continue

            if set(line) == {"-"}:             # a horizontal rule
                continue

            if line.startswith("[") and line.endswith("]"):
                inner = line[1:-1].strip()
                key = inner.split(":", 1)[0].split()[0].upper()
                label = inner.split(":", 1)[1].strip() if ":" in inner else ""
                if key == "MUSIC":
                    events.append(MusicCue(label))
                elif key == "STING":
                    events.append(StingCue(label))
                elif key == "SFX":
                    add_silence(_SFX_MS)
                elif key == "PAUSE":
                    m = re.search(r"(\d+(?:\.\d+)?)\s*s", inner)
                    add_silence(int(float(m.group(1)) * 1000) if m else _DEFAULT_PAUSE_MS)
                continue

            if line.startswith(f"{NARRATOR}:"):
                content = line[len(NARRATOR) + 1:].strip()
                if m := re.match(r"^\*\((.+?)\)\*\s*(.*)$", content):
                    delivery, spoken = m.group(1), m.group(2).strip()
                else:
                    delivery, spoken = "", content
                spoken = re.sub(r"\*+", "", spoken).strip()
                if spoken:
                    events.append(Speak(spoken, delivery))
                    events.append(Silence(LINE_GAP_MS))

        return cls(episode_title=title, events=tuple(events))

    @property
    def spoken_lines(self) -> list[Speak]:
        return [e for e in self.events if isinstance(e, Speak)]

    @property
    def character_count(self) -> int:
        """Billable characters. Calibration is ~888 per finished minute."""
        return sum(len(line.text) for line in self.spoken_lines)

    def count(self, event_type) -> int:
        return sum(1 for e in self.events if isinstance(e, event_type))
