"""The session summary as a parsed document rather than a blob of markdown.

`sessions/<date>/summary.md` has a specified shape (CLAUDE.md, step 2): an
`*In brief: …*` lead line, then `##` beat sections, closing with a
forward-looking `## What's next` / `## Loose ends`. That is a value object, and
five modules used to re-derive it from the raw text independently — the
in-brief extraction existed three times and the section walk twice, with
*different* heading rules: the prep hub normalized smart quotes and trailing
colons, the image pipeline only lowercased. A `## What’s next` typed with a
curly apostrophe would therefore be harvested as an open thread *and* billed to
Gemini as an illustration of a bullet list.

One parser, one set of heading rules, here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .text import _norm_heading, slugify

# Deliberately as strict as core.markdown.md_to_html's own heading rule: the
# Beat sequence must line up one-for-one with the <h2> elements it renders,
# because that is how beat images are placed. An indented "##" is a heading to
# neither.
_HEADING = re.compile(r"^##\s+(.*)$")
_BULLET = re.compile(r"^\s*[-*]\s+(.*)$")

#: Headings that close a summary rather than narrate it. These list leads and
#: status; they feed the open-threads board and are never illustrated.
FORWARD_HEADINGS = frozenset({
    "what's next", "whats next", "next steps", "up next", "next",
    "loose ends", "loose end", "loose threads", "leads",
})


@dataclass(frozen=True)
class Beat:
    """One `##` section of a summary."""

    title: str
    body: str

    @property
    def slug(self) -> str:
        """Matches the beat-image filename: sessions/<date>/images/<slug>.jpg."""
        return slugify(self.title)

    @property
    def is_forward_looking(self) -> bool:
        return _norm_heading(self.title) in FORWARD_HEADINGS

    @property
    def bullets(self) -> list[str]:
        return [m.group(1).strip()
                for line in self.body.split("\n")
                if (m := _BULLET.match(line.rstrip()))]

    @property
    def is_illustratable(self) -> bool:
        """A story beat worth an image: narrative prose, not a list of leads."""
        if self.is_forward_looking or not self.body:
            return False
        return any(ln.strip() and not ln.strip().startswith(("-", "*"))
                   for ln in self.body.splitlines())


@dataclass(frozen=True)
class SessionSummary:
    """A parsed summary.md body (frontmatter already stripped)."""

    raw: str
    beats: tuple[Beat, ...]

    @classmethod
    def parse(cls, markdown: str) -> SessionSummary:
        markdown = markdown or ""
        beats: list[Beat] = []
        title, body = None, []

        def flush():
            if title is not None:
                beats.append(Beat(title, "\n".join(body).strip()))

        for line in markdown.splitlines():
            m = _HEADING.match(line.rstrip())
            if m:
                flush()
                title, body = m.group(1).strip(), []
            elif title is not None:
                body.append(line)
        flush()
        return cls(raw=markdown, beats=tuple(beats))

    @property
    def in_brief(self) -> str:
        """The author's own compressed statement of the session, unwrapped."""
        for line in self.raw.split("\n"):
            s = line.strip()
            if s.startswith("*In brief:") and s.endswith("*"):
                return s[len("*In brief:"):-1].strip()
        return ""

    @property
    def lead_line(self) -> str:
        """The first line that says anything: the `*In brief:*` one-liner when
        it leads (it always does today), else the first line of prose. This is
        the row blurb on sessions.html."""
        for line in self.raw.split("\n"):
            s = line.strip()
            if s.startswith("*In brief:") and s.endswith("*"):
                return s[len("*In brief:"):-1].strip()
            if s and not s.startswith("#"):
                return s.strip("*").strip()
        return ""

    @property
    def illustratable_beats(self) -> list[Beat]:
        return [b for b in self.beats if b.is_illustratable]

    @property
    def forward_sections(self) -> list[Beat]:
        """Closing sections that carry at least one bullet — the open threads."""
        return [b for b in self.beats if b.is_forward_looking and b.bullets]

    def __bool__(self) -> bool:
        return bool(self.raw.strip())
