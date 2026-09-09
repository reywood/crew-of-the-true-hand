"""A quest's status: one value object, not a display label four tables key off.

`quests.md` states a quest's status by which `##` section it sits under. That
one fact drove four separate lookups — section->label+css in the loader,
label->impact score on the home page, label->display order on the quest log,
and `"Active" in q.status` as an is-it-active test. Renaming a label such as
"Active — main arc" to "Main arc" would therefore have silently zeroed the home
page's active count, emptied its top-quest list, emptied the prep hub's
"Do this next" block and dropped a whole section from the quest log — four
failures, no error, because behaviour keyed off prose meant for readers.

Every attribute now hangs off the status itself, so a label is only ever a
label.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Impact at or above which a quest counts as active. The home page's
#: "N active threads" and its ranked list both read this, rather than testing
#: for the word "Active" inside the display label.
ACTIVE_IMPACT = 3


@dataclass(frozen=True, order=False)
class QuestStatus:
    """What a quest's section heading means.

    - ``label``         — what the reader sees on the chip.
    - ``css_class``     — the ``status-<x>`` modifier on that chip.
    - ``impact``        — how central to the campaign's spine; ranks the home
                          page's top quests, and 0 drops a quest out of them.
    - ``display_order`` — order of the sections on the quest log.
    """

    label: str
    css_class: str
    impact: int
    display_order: int

    @property
    def is_active(self) -> bool:
        return self.impact >= ACTIVE_IMPACT

    def __str__(self) -> str:
        return self.label


MAIN_ARC = QuestStatus("Active — main arc", "active-main", 4, 0)
LEAD = QuestStatus("Active — lead", "active", 3, 1)
REGION = QuestStatus("Active — region", "active", 3, 2)
UNRESOLVED = QuestStatus("Unresolved", "unresolved", 2, 3)
PERSONAL = QuestStatus("Personal", "personal", 1, 4)
COMPLETED = QuestStatus("Completed", "completed", 0, 5)

#: Mirrors the `##` headings in quests.md. Whether a section is surfaced at all
#: is decided once, in load_quests — the Personal section is not.
SECTION_TO_STATUS = {
    "Main arc — the giant ordning": MAIN_ARC,
    "Allies to recruit / leads to chase": LEAD,
    "Giant hotspots (intel from Corvin / Chazlauth / Lifferloss)": REGION,
    "Side leads / unresolved": UNRESOLVED,
    "Personal / character": PERSONAL,
    "Completed": COMPLETED,
}

#: Quest-log section order.
DISPLAY_ORDER = sorted(set(SECTION_TO_STATUS.values()), key=lambda s: s.display_order)


def for_section(section: str) -> QuestStatus:
    """The status a `##` heading in quests.md denotes.

    An unrecognized heading keeps its own text as the label and renders as a
    plain active chip — the same fallback the loader has always had, so adding
    a section to quests.md degrades gracefully instead of raising mid-build.
    It scores 0 impact, which keeps an unvetted section off the home page.
    """
    return SECTION_TO_STATUS.get(section, QuestStatus(section, "active", 0, 99))
