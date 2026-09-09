"""Derived cross-entity relations: the joins that are not written in any file.

Two relations in this archive are computed rather than authored:

  * **expertise** — an item declares `expertise_needed:` and an NPC declares
    `expertise:`; overlapping tags mean that NPC could help with that item.
  * **quest dependencies** — the table in `data/quest_dependencies.toml` says
    which quest advances which, and the reverse direction is derived from it.

These used to be computed by the site layer and stashed on `Entity.meta`, which
meant `core.graph` read fields only `site.pages.index` could write: moving
`build_graph` above those two calls silently dropped the `can_help` and
`depends_on` edges from graph.json, the search index and every Connections
block, with nothing to raise. They are domain relations, not rendering, so they
live here and travel as an explicit value that callers must be handed.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .. import data as _data


@dataclass(frozen=True)
class Relations:
    """Every derived join, keyed by entity href. Computed once per build.

    Read through the accessors rather than the dicts: they return a stable
    empty list for an entity with no such relation, which is the common case.
    """

    helpers: dict[str, list] = field(default_factory=dict)  # item href -> [npc]
    can_help_with: dict[str, list] = field(default_factory=dict)  # npc href  -> [item]
    helps: dict[str, list] = field(default_factory=dict)  # quest href -> [quest]
    supported_by: dict[str, list] = field(default_factory=dict)  # quest href -> [quest]
    warnings: list[str] = field(default_factory=list)

    def helpers_for(self, item) -> list:
        """NPCs whose expertise matches this item's `expertise_needed:`."""
        return self.helpers.get(item.href, [])

    def can_help_with_for(self, npc) -> list:
        """Items this NPC's `expertise:` tags bear on."""
        return self.can_help_with.get(npc.href, [])

    def helps_for(self, quest) -> list:
        """Quests this one advances."""
        return self.helps.get(quest.href, [])

    def supported_by_for(self, quest) -> list:
        """Quests that advance this one."""
        return self.supported_by.get(quest.href, [])


def build_relations(items, npcs, quests) -> Relations:
    """Compute every derived join. Unresolvable quest names are collected as
    warnings for the caller to surface, not printed from here."""
    rel = Relations()

    for item in items:
        needs = set(item.meta["expertise_needed"].tags())
        if not needs:
            continue
        for npc in npcs:
            if needs & set(npc.meta["expertise"].tags()):
                rel.helpers.setdefault(item.href, []).append(npc)
                rel.can_help_with.setdefault(npc.href, []).append(item)

    by_name = {q.name: q for q in quests}
    for src_name, targets in _data.load("quest_dependencies")["helps"].items():
        src = by_name.get(src_name)
        if src is None:
            rel.warnings.append(f"dep source quest not found: {src_name!r}")
            continue
        for tgt_name in targets:
            tgt = by_name.get(tgt_name)
            if tgt is None:
                rel.warnings.append(
                    f"dep target quest not found: {tgt_name!r} (referenced by {src_name!r})"
                )
                continue
            rel.helps.setdefault(src.href, []).append(tgt)
            rel.supported_by.setdefault(tgt.href, []).append(src)

    return rel
