"""Derived joins are owned by core and travel explicitly.

The regression these guard: expertise and quest-dependency links used to be
mutated onto Entity.meta by the site layer, while core.graph read them back.
Correctness depended on statement order in build_site — reordering two lines
silently emptied graph.json of can_help/depends_on edges with nothing raised.
"""

import pytest

from truehand.core.entity import Entity
from truehand.core.relations import Relations, build_relations


def _item(slug, needs=None):
    return Entity("item", slug, slug.title(), meta={"expertise_needed": needs} if needs else {})


def _npc(slug, expertise=None):
    return Entity("npc", slug, slug.title(), meta={"expertise": expertise} if expertise else {})


def _quest(name):
    return Entity("quest", name.lower().replace(" ", "-"), name)


class TestExpertiseJoin:
    def test_matching_tag_links_both_directions(self):
        item, npc = _item("horn", "giants"), _npc("harshnag", "giants, runes")
        rel = build_relations([item], [npc], [])
        assert rel.helpers_for(item) == [npc]
        assert rel.can_help_with_for(npc) == [item]

    def test_tag_match_ignores_case_and_whitespace(self):
        item, npc = _item("tome", " Draconic , Dragons"), _npc("naxene", "draconic")
        rel = build_relations([item], [npc], [])
        assert rel.helpers_for(item) == [npc]

    def test_no_overlap_means_no_edge(self):
        item, npc = _item("horn", "giants"), _npc("naxene", "draconic")
        rel = build_relations([item], [npc], [])
        assert rel.helpers_for(item) == []
        assert rel.can_help_with_for(npc) == []

    def test_entity_without_tags_is_absent_not_missing(self):
        """Accessors return [] for an unrelated entity — no KeyError, no None."""
        rel = build_relations([], [], [])
        assert rel.helpers_for(_item("plain")) == []
        assert rel.can_help_with_for(_npc("plain")) == []


class TestQuestDependencies:
    def test_real_table_resolves_against_the_real_quest_log(self, paths):
        """Every name in quest_dependencies.toml matches a quest in quests.md."""
        from truehand.core.loaders import load_quests

        rel = build_relations([], [], load_quests(paths))
        assert rel.warnings == []
        assert rel.helps, "expected at least one dependency edge"

    def test_forward_and_reverse_derive_from_one_edge(self):
        src, tgt = _quest("Find Harshnag"), _quest("Reach the Oracle")
        rel = build_relations([], [], [src, tgt])
        assert rel.helps_for(src) == [tgt]
        assert rel.supported_by_for(tgt) == [src]
        assert rel.helps_for(tgt) == []

    def test_unresolvable_name_warns_rather_than_dropping_silently(self):
        rel = build_relations([], [], [_quest("Reach the Oracle")])
        assert any("Find Harshnag" in w for w in rel.warnings)


class TestGraphTakesRelationsExplicitly:
    def test_build_graph_requires_relations(self):
        """The ordering trap is gone: graph cannot be built without the joins."""
        from truehand.core.graph import build_graph

        with pytest.raises(TypeError):
            build_graph([], [], [], [], [], [], {})

    def test_can_help_edges_come_from_relations(self):
        from truehand.core.graph import build_graph

        item, npc = _item("horn", "giants"), _npc("harshnag", "giants")
        rel = build_relations([item], [npc], [])
        g = build_graph([], [npc], [], [item], [], [], {}, rel)
        assert {"source": npc.href, "target": item.href, "rel": "can_help"} in g.edges

    def test_empty_relations_yield_no_derived_edges(self):
        from truehand.core.graph import build_graph

        item, npc = _item("horn", "giants"), _npc("harshnag", "giants")
        g = build_graph([], [npc], [], [item], [], [], {}, Relations())
        assert not [e for e in g.edges if e["rel"] in ("can_help", "depends_on")]
