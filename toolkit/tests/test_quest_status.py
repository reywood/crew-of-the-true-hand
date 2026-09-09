"""Quest status is a value object; a display label is only ever a label.

The regression this guards: four tables keyed off the human-readable status
label, one of them by substring (`"Active" in q.status`). Renaming a label was
a silent four-way breakage. These tests rename one and assert nothing moves.
"""

import dataclasses

import pytest

from truehand.core import quest_status as qs
from truehand.core.loaders import load_quests


class TestStatusOwnsItsAttributes:
    def test_active_is_impact_not_a_substring_of_the_label(self):
        renamed = dataclasses.replace(qs.MAIN_ARC, label="Main arc")
        assert "Active" not in renamed.label
        assert renamed.is_active
        assert renamed.impact == qs.MAIN_ARC.impact
        assert renamed.css_class == qs.MAIN_ARC.css_class

    def test_completed_is_not_active_and_scores_zero(self):
        assert not qs.COMPLETED.is_active
        assert qs.COMPLETED.impact == 0

    def test_unresolved_is_ranked_but_not_active(self):
        assert not qs.UNRESOLVED.is_active
        assert qs.UNRESOLVED.impact > qs.COMPLETED.impact

    def test_main_arc_outranks_every_other_status(self):
        assert qs.MAIN_ARC.impact == max(s.impact for s in qs.DISPLAY_ORDER)

    def test_display_order_is_total_and_unique(self):
        orders = [s.display_order for s in qs.DISPLAY_ORDER]
        assert orders == sorted(orders) == sorted(set(orders))

    def test_str_is_the_label(self):
        assert str(qs.LEAD) == "Active — lead"

    def test_statuses_are_hashable_grouping_keys(self):
        assert len({qs.LEAD, qs.LEAD, qs.REGION}) == 2


class TestSectionResolution:
    @pytest.mark.parametrize("section,expected", list(qs.SECTION_TO_STATUS.items()))
    def test_every_known_heading_resolves(self, section, expected):
        assert qs.for_section(section) is expected

    def test_unknown_heading_keeps_its_text_and_stays_off_the_home_page(self):
        st = qs.for_section("Some new section")
        assert st.label == "Some new section"
        assert st.css_class == "active"
        assert st.impact == 0 and not st.is_active


class TestAgainstTheRealQuestLog:
    def test_every_heading_in_quests_md_is_mapped(self, paths):
        text = paths.quests_file.read_text(encoding="utf-8")
        headings = [ln[3:].strip() for ln in text.split("\n") if ln.startswith("## ")]
        assert headings, "expected ## sections in quests.md"
        assert [h for h in headings if h not in qs.SECTION_TO_STATUS] == []

    def test_loaded_quests_carry_status_objects(self, paths):
        quests = load_quests(paths)
        assert quests
        assert all(isinstance(q.status, qs.QuestStatus) for q in quests)

    def test_personal_quests_are_not_surfaced(self, paths):
        """The loader is the single place that decides this."""
        assert all(q.status is not qs.PERSONAL for q in load_quests(paths))
