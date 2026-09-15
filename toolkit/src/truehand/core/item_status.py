"""What an item's `status:` and `holder:` mean — the QuestStatus move for the ledger.

`quest_status.py` exists because behaviour keyed off a display label drifted
silently. The ledger still had that disease. The status vocabulary and its CSS
lived on the items page, while the prep hub independently tested the same
string literals to decide which items are still a mystery worth an expert
(`== "Unresolved"`) and which count as a PC's holdings (`in ("Active",
"Unresolved")`). Renaming `Unresolved` to `Open` in the item files would have
emptied two prep-hub blocks while the ledger page kept working — no error,
because a chip label meant for readers was doing double duty as a flag.

`holder:` had the same split: the prep hub matched it exactly against a PC's
name, the graph resolved it through the alias table and excluded "Party". A
file saying `holder: Hisfiz` therefore drew a held_by edge on the chart but
never appeared under Fiz's holdings.

Both questions now hang off one place, so a label is only ever a label.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, order=False)
class ItemStatus:
    """What an item's `status:` means.

    - ``label``         — what the reader sees on the chip.
    - ``css_class``     — the ``status-<x>`` modifier on that chip.
    - ``display_order`` — order of the groups on the ledger.
    """

    label: str
    css_class: str
    display_order: int

    @property
    def is_open(self) -> bool:
        """Still a mystery worth an expert — the prep hub's
        "Unresolved items & who can crack them"."""
        return self is UNRESOLVED

    @property
    def is_carried(self) -> bool:
        """Still in a pack, so it counts toward a PC's holdings."""
        return self in (ACTIVE, UNRESOLVED)

    def __str__(self) -> str:
        return self.label


UNRESOLVED = ItemStatus("Unresolved", "unresolved", 0)
ACTIVE = ItemStatus("Active", "active", 1)
CONSUMED = ItemStatus("Consumed", "completed", 2)
LOST = ItemStatus("Lost", "completed", 3)
SOLD = ItemStatus("Sold", "completed", 4)

BY_LABEL = {s.label: s for s in (UNRESOLVED, ACTIVE, CONSUMED, LOST, SOLD)}

#: Ledger group order — unresolved first, so mysteries lead.
DISPLAY_ORDER = sorted(BY_LABEL.values(), key=lambda s: s.display_order)


def for_label(label: str) -> ItemStatus:
    """The status a `status:` line denotes.

    An item with no status is Active — the ledger's long-standing default for a
    thing the crew simply has. An unrecognized label keeps its own text, renders
    as a plain chip and sorts last, so adding a status to an item file degrades
    gracefully instead of raising mid-build.
    """
    if not label:
        return ACTIVE
    return BY_LABEL.get(label, ItemStatus(label, "active", 99))


#: What `holder: Party` means: the crew holds it in common, nobody carries it.
PARTY = "party"


def holder_of(item) -> str | None:
    """Who carries this item, or None when the party holds it in common.

    Returns the name as written; callers match it against a PC's aliases, since
    the archive may name a holder any way the crew does (`Fiz`, `Hisfiz`).
    """
    holder = item.meta["holder"].one()
    return holder if holder and holder.lower() != PARTY else None
