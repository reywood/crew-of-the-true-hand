"""A session: the archive's one aggregate with real structure.

Everything for one evening of play lives in `sessions/YYYY-MM-DD/` — notes,
transcript, summary, hero and beat images, the audio recap. A session is not a
variant of an NPC: it is identified by a date rather than a slug, it holds
sub-documents, and it has an invariant (a folder with none of notes, transcript
or summary is not a session at all).

It used to be an Entity with fifteen keys in an untyped `meta` dict — two Path
objects sitting beside parsed frontmatter strings, and four `has_*` booleans
duplicating state that `audio is not None` already tells you. Derived values
are properties here, so they cannot drift from what they describe, and the URL
naming rules live in exactly one place instead of being restated by whatever
copies the files.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .summary import SessionSummary

#: Image extensions the archive publishes, in the order they are discovered.
IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png", ".webp")


@dataclass(frozen=True)
class SessionArtifacts:
    """What the media pipelines produced for one session.

    `hero` is the 16:9 banner (`images/hero.<ext>`); `beats` maps a summary
    beat's slug to its illustration; `audio` is the stitched "Tales of the True
    Hand" recap, and `episode_title` is what that episode is called — line 2
    of its script. CLAUDE.md calls it the episode title, so this does too; it
    was `audio_subtitle` here, which it never was.
    """

    hero: Path | None = None
    beats: dict[str, Path] = field(default_factory=dict)
    audio: Path | None = None
    episode_title: str = ""


@dataclass(eq=False)
class Session:
    """One session of play. Identified by its real-world date."""

    date: str
    notes: str = ""
    transcript: str = ""
    summary: SessionSummary = field(default_factory=lambda: SessionSummary("", ()))
    carried: tuple[str, ...] = ()
    #: Location slugs, most important first. Authored out-of-band in
    #: data/session_locations.toml because it is an annotation, not something
    #: extractable from the summary — but it is Session state all the same,
    #: not ambient config for three modules to reach for independently.
    locations: tuple[str, ...] = ()
    artifacts: SessionArtifacts = field(default_factory=SessionArtifacts)

    def __post_init__(self):
        if not (self.notes or self.transcript or self.summary):
            raise ValueError(
                f"session {self.date}: needs at least one of notes, transcript "
                f"or summary to be a session at all")

    # -- identity, shared with Entity so pages and the graph treat both alike --
    kind = "session"

    @property
    def slug(self) -> str:
        return self.date

    @property
    def name(self) -> str:
        return f"Session {self.date}"

    @property
    def aliases(self) -> list[str]:
        return [self.date]

    @property
    def href(self) -> str:
        return f"session-{self.date}.html"

    @property
    def blurb(self) -> str:
        """The row line on sessions.html: the summary's `*In brief:*` when there
        is one, else the first line of the player's notes, else a note that the
        session has only raw material."""
        if lead := self.summary.lead_line:
            return lead
        for line in self.notes.split("\n"):
            if line.strip():
                return line.strip()
        return "Transcript only — no written notes." if self.transcript else "No content."

    @property
    def in_transit(self) -> bool:
        """No fixed place — the sessions list shows a dashed em-dash chip."""
        return not self.locations

    # -- artifacts: one set of naming rules, derived, never stored -------------
    @property
    def has_audio(self) -> bool:
        return self.artifacts.audio is not None

    @property
    def audio_name(self) -> str:
        """The published filename. The site URL stays date-based however the
        source is laid out on disk (it is always audio/final.mp3)."""
        return f"{self.date}.mp3" if self.has_audio else ""

    @property
    def has_hero(self) -> bool:
        return self.artifacts.hero is not None

    @property
    def hero_name(self) -> str:
        """Date-based too, though the source is images/hero.<ext>."""
        hero = self.artifacts.hero
        return f"{self.date}{hero.suffix}" if hero else ""

    def beat_image(self, beat) -> Path | None:
        """The illustration for a summary beat, if one was generated."""
        return self.artifacts.beats.get(beat.slug)
