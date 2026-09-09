"""Where the crew is and what they are trying to do.

`campaign-state.md` is the one bit of "where are we / what's the goal" the
archive does not otherwise capture, and it drives the prep hub. It is small,
hand-maintained and fully known, so it is a value object rather than a dict of
three `.get()`s with defaults — a file that has already produced one silent
empty (see `objective` below) earns a type.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CampaignState:
    """The party's current objective, open questions, and location override."""

    #: A sentence. The frontmatter dialect splits any comma-bearing value into
    #: a list, so this must be rejoined from fragments: a str-only guard once
    #: discarded it and next.html rendered no objective at all.
    objective: str = ""
    open_questions: tuple[str, ...] = ()
    #: Set only to override the location derived from the latest session —
    #: mid-journey, say.
    location_override: str | None = None

    @property
    def has_objective(self) -> bool:
        return bool(self.objective)
