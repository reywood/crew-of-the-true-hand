"""Where an NPC is: one reading of the `location:` line.

The field is free text with conventions — `Waterdeep`, `Waterdeep, Dock Ward`,
`Silverymoon (last known)`, `Pearl Isles (origin)`, `With the crew`. Three
modules each extracted a different meaning from it, none able to see the
others: `loaders.port_for` stripped provisional wording and took the longest
matching location name, `prep._npc_at_location` did a substring test against a
location's name *or* its slug-with-spaces, and `locations._location_strip_
qualifier` dropped the parenthetical for the roster. They even disagreed on the
field's shape — `one()` (the first comma-fragment) versus `prose()` (the whole
line) — so "is Harshnag at Silverymoon?" got a different answer on the chart,
the prep hub and the roster.

The three answers are still different, because the three questions are. What
changes is that they now differ **on purpose, in one place, with the reason
written down** instead of by accident of which module you are standing in:

- `resolve` reads the **port** — the first fragment. The archive writes a
  comma-list broad-to-specific ("Waterdeep, Trades Ward"), so the port is the
  city, not the ward. This matters: Trades Ward is itself a location, and
  matching the whole line would move the chart edge off Waterdeep onto it.
- `is_at` reads the **whole line**, because "who is where I am" should find an
  NPC in Trades Ward when the crew is in Waterdeep *and* when it is in Trades
  Ward. Provisional wording still counts — a "last known" lead is exactly who
  you would ask after there.
- `place` reads the whole line minus any parenthetical, which is the roster's
  "First Encountered" column.

The provisional test reads the port fragment only, so a line naming a solid
place first is not made provisional by a later hedge.

This module also puts the rule in `core` rather than in the loader, which is
why `core.graph` no longer has to import `core.loaders` to draw a chart edge.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .standing import PROVISIONAL

_QUALIFIER = re.compile(r"\s*\([^)]*\)\s*")


@dataclass(frozen=True)
class Whereabouts:
    """An NPC's `location:`, read by intent rather than re-split per caller."""

    #: The line's comma-fragments, broad to specific. Empty when unset.
    parts: tuple[str, ...] = ()

    @classmethod
    def of(cls, npc) -> Whereabouts:
        return cls(tuple(npc.meta["location"].many()))

    def __bool__(self) -> bool:
        return bool(self.parts)

    def __str__(self) -> str:
        """The source line, rejoined — what `Field.prose()` gave every caller."""
        return ", ".join(self.parts)

    @property
    def port(self) -> str:
        """The broad place the line leads with; "" when unset."""
        return self.parts[0] if self.parts else ""

    @property
    def place(self) -> str:
        """The line minus any parenthetical: 'Silverymoon (last known)' ->
        'Silverymoon'; 'Waterdeep, Trades Ward' kept whole."""
        return _QUALIFIER.sub("", str(self)).strip()

    @property
    def is_provisional(self) -> bool:
        """'last known', 'sought', 'origin'…: we do not really know. Such an
        NPC groups under Adrift on the chart and draws no located_in edge."""
        low = self.port.lower()
        return any(p in low for p in PROVISIONAL)

    def is_at(self, location) -> bool:
        """Whether this line names *location*, loosely — the prep hub's
        "people & leads where you are". Reads the whole line, and provisional
        wording still counts."""
        low = str(self).lower()
        if not low:
            return False
        return location.name.lower() in low or location.slug.replace("-", " ") in low

    def resolve(self, locations):
        """The known location this NPC is *in*, or None for Adrift.

        Longest name wins, so "Silver Marches" beats a stray "Silver".
        """
        if not self or self.is_provisional:
            return None
        low = self.port.lower()
        hits = [loc for loc in locations if loc.name.lower() in low]
        return max(hits, key=lambda loc: len(loc.name), default=None)
