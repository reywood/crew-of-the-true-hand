"""How the crew stands with an NPC.

An NPC's `type:` is campaign vocabulary — "Old shipmate", "Politically uneasy",
"Ally (sought)" — and several phrasings collapse to one standing. That fact
used to be a `(label, css_class)` tuple handed out of `core`, which meant the
pure archive layer named a domain concept after its widget, and that page
renderers asked domain questions by string-matching CSS:

    (chip_for(n.meta["type"].one()) or ("", ""))[1] in ("standing-ally", ...)

`QuestStatus` already showed the shape of the answer. This is the same move for
the other chip vocabulary: behaviour hangs off the standing, so a label is only
ever a label and a class only ever a class.
"""

from __future__ import annotations

from dataclasses import dataclass

from .. import data as _data


@dataclass(frozen=True)
class Standing:
    """What an NPC's `type:` means for the crew."""

    label: str
    css_class: str

    @property
    def is_approachable(self) -> bool:
        """Someone worth seeking out where you are — the prep hub's question.

        Allies, leads and old shipmates; not foes, ghosts, gods or passers-by.
        """
        return self.css_class in _APPROACHABLE


_APPROACHABLE = frozenset({"standing-ally", "standing-lead", "standing-crew"})

#: Campaign vocabulary, edited in truehand/data/npc_standing.toml, not here.
_DATA = _data.load("npc_standing")

BY_TYPE = {name: Standing(label, css) for name, (label, css) in _DATA["standing"].items()}

#: Words in a `location:` meaning "we don't really know" — such an NPC groups
#: under Adrift rather than under a port.
PROVISIONAL = tuple(_DATA["provisional"])


def for_type(npc_type: str) -> Standing | None:
    """The standing a `type:` denotes, or None if it denotes none — an
    unmapped type renders no chip and says nothing about the NPC."""
    return BY_TYPE.get(npc_type.strip()) if npc_type else None
