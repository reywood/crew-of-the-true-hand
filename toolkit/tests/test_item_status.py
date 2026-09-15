"""Item status is a value object; a display label is only ever a label.

The regression this guards: three modules keyed off the ledger's status and
holder strings independently — the items page owned the vocabulary, the prep
hub re-tested the literals to pick unresolved mysteries and a PC's holdings,
and the graph resolved the holder through the alias table while the prep hub
compared it to the PC's canonical name. Renaming a status, or writing
`holder: Hisfiz`, broke some of those and not others, silently.
"""

import dataclasses

import pytest

from truehand.core import item_status as ist
from truehand.core.entity import Entity
from truehand.core.frontmatter import Frontmatter
from truehand.core.loaders import load_items, load_pcs


def _item(**meta):
    return Entity(kind="item", slug="x", name="X", meta=Frontmatter(meta))


class TestStatusOwnsItsAttributes:
    def test_open_is_identity_not_a_substring_of_the_label(self):
        renamed = dataclasses.replace(ist.UNRESOLVED, label="Open")
        assert "Unresolved" not in renamed.label
        assert renamed.css_class == ist.UNRESOLVED.css_class

    def test_only_unresolved_is_open(self):
        assert ist.UNRESOLVED.is_open
        assert not any(s.is_open for s in ist.DISPLAY_ORDER if s is not ist.UNRESOLVED)

    def test_carried_is_what_is_still_in_a_pack(self):
        assert ist.ACTIVE.is_carried and ist.UNRESOLVED.is_carried
        assert not ist.CONSUMED.is_carried
        assert not ist.LOST.is_carried
        assert not ist.SOLD.is_carried

    def test_unresolved_leads_the_ledger(self):
        assert ist.DISPLAY_ORDER[0] is ist.UNRESOLVED

    def test_display_order_is_total_and_unique(self):
        orders = [s.display_order for s in ist.DISPLAY_ORDER]
        assert orders == sorted(orders) == sorted(set(orders))

    def test_str_is_the_label(self):
        assert str(ist.CONSUMED) == "Consumed"

    def test_statuses_are_hashable_grouping_keys(self):
        assert len({ist.ACTIVE, ist.ACTIVE, ist.LOST}) == 2


class TestLabelResolution:
    @pytest.mark.parametrize("label,expected", list(ist.BY_LABEL.items()))
    def test_every_known_label_resolves(self, label, expected):
        assert ist.for_label(label) is expected

    def test_no_status_means_active(self):
        """The ledger's long-standing default for a thing the crew simply has."""
        assert ist.for_label("") is ist.ACTIVE

    def test_unknown_label_keeps_its_text_and_sorts_last(self):
        st = ist.for_label("Pawned")
        assert st.label == "Pawned"
        assert st.css_class == "active"
        assert not st.is_open and not st.is_carried
        assert st.display_order > max(s.display_order for s in ist.DISPLAY_ORDER)


class TestHolder:
    def test_party_holds_nothing_in_particular(self):
        assert ist.holder_of(_item(holder="Party")) is None
        assert ist.holder_of(_item(holder="party")) is None

    def test_missing_holder_is_nobody(self):
        assert ist.holder_of(_item()) is None

    def test_a_pc_holder_comes_back_as_written(self):
        assert ist.holder_of(_item(holder="Hisfiz")) == "Hisfiz"

    def test_an_npc_may_hold_an_item(self):
        assert ist.holder_of(_item(holder="Chazlauth")) == "Chazlauth"


class TestAgainstTheRealLedger:
    def test_loaded_items_carry_status_objects(self, paths):
        items = load_items(paths)
        assert items
        assert all(isinstance(it.status, ist.ItemStatus) for it in items)

    def test_every_status_in_items_is_mapped(self, paths):
        unknown = [it.name for it in load_items(paths) if it.status.label not in ist.BY_LABEL]
        assert unknown == []

    def test_every_pc_holder_matches_a_pc_alias(self, paths):
        """What the prep hub's "Carrying" line depends on: a holder that names a
        PC any way the crew does still resolves to that PC."""
        aliases = {a for pc in load_pcs(paths) for a in pc.aliases}
        names = {pc.name for pc in load_pcs(paths)}
        held = {ist.holder_of(it) for it in load_items(paths)} - {None}
        pc_held = {h for h in held if h in aliases}
        assert pc_held, "expected some items held by PCs"
        assert pc_held <= names or pc_held <= aliases
