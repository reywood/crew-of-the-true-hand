"""The archive's frontmatter dialect.

The highest-value file in the suite: it pins a format that *looks* like YAML
but is not, against the recurring impulse to "just use PyYAML". Every case
below is drawn from a real file in the archive.
"""

import pytest

from truehand.core.frontmatter import parse_frontmatter


def test_no_frontmatter_returns_empty_and_original_text():
    text = "# Just a heading\n\nbody\n"
    fm, body = parse_frontmatter(text)
    assert fm == {}
    assert body == text


def test_unterminated_frontmatter_is_not_frontmatter():
    text = "---\naliases: A, B\nnever closed\n"
    fm, body = parse_frontmatter(text)
    assert fm == {}
    assert body == text


def test_plain_scalar():
    fm, _ = parse_frontmatter("---\nname: Brindle\n---\nbody\n")
    assert fm["name"] == "Brindle"


def test_comma_values_become_a_list():
    """48 entity files rely on this. Real YAML returns the scalar "A, B"."""
    fm, _ = parse_frontmatter("---\naliases: Boz Hark, Bozhark\n---\n")
    assert fm["aliases"] == ["Boz Hark", "Bozhark"]


def test_bullet_list():
    """The form the retired update-entity-sessions.py fork silently dropped."""
    fm, _ = parse_frontmatter("---\ncarried:\n- A rope\n- A lantern\n---\n")
    assert fm["carried"] == ["A rope", "A lantern"]


def test_bullet_list_tolerates_a_missing_space():
    fm, _ = parse_frontmatter("---\ncarried:\n-A rope\n-A lantern\n---\n")
    assert fm["carried"] == ["A rope", "A lantern"]


def test_empty_value_with_no_bullets_is_an_empty_list():
    fm, _ = parse_frontmatter("---\ncarried:\n---\n")
    assert fm["carried"] == []


def test_body_is_returned_after_the_closing_delimiter():
    _fm, body = parse_frontmatter("---\nname: X\n---\nThe body.\n")
    assert body == "The body.\n"


def test_a_line_without_a_colon_is_skipped():
    fm, _ = parse_frontmatter("---\nname: X\njust a stray line\ntype: NPC\n---\n")
    assert fm == {"name": "X", "type": "NPC"}


class TestThisIsNotYaml:
    """Each of these is a place real YAML diverges from the archive's dialect.

    Verified against PyYAML 6.0.3 over all 88 frontmatter-bearing files:
    one hard ScannerError, 48 files whose aliases degrade to a scalar, and
    103 fields that come back as datetime.date instead of str.
    """

    def test_a_colon_inside_a_value_is_kept_not_treated_as_a_mapping(self):
        """campaign-state.md's objective. PyYAML raises a ScannerError here.

        Note the dialect also comma-splits, so this prose value comes back as
        a list of segments — the colon survives inside one of them.
        """
        text = ("---\nobjective: Extract him, then run the Harper route: "
                "Yackerty in the Trades Ward, a portal to Silverymoon.\n---\n")
        fm, _ = parse_frontmatter(text)
        assert fm["objective"] == [
            "Extract him",
            "then run the Harper route: Yackerty in the Trades Ward",
            "a portal to Silverymoon.",
        ]

    def test_date_shaped_values_stay_strings(self):
        """PyYAML types these as datetime.date, breaking .strip() and regex."""
        fm, _ = parse_frontmatter("---\nfirst_seen: 2025-12-17\n---\n")
        assert fm["first_seen"] == "2025-12-17"
        assert isinstance(fm["first_seen"], str)

    def test_a_single_date_is_a_string_not_a_list(self):
        fm, _ = parse_frontmatter("---\nsessions: 2025-12-07\n---\n")
        assert fm["sessions"] == "2025-12-07"

    def test_a_hash_inside_a_value_is_literal_not_a_comment(self):
        fm, _ = parse_frontmatter("---\nname: Cabin #4\n---\n")
        assert fm["name"] == "Cabin #4"


@pytest.mark.parametrize("path_glob", ["npcs/*.md", "locations/*.md", "items/*.md"])
def test_every_real_entity_file_parses(paths, path_glob):
    files = sorted(paths.root.glob(path_glob))
    assert files, f"no files matched {path_glob}"
    for f in files:
        fm, _ = parse_frontmatter(f.read_text(encoding="utf-8"))
        assert fm.get("name"), f"{f.name} has no name in frontmatter"


def test_campaign_state_parses(paths):
    """The file PyYAML cannot read at all."""
    fm, _ = parse_frontmatter(paths.campaign_state_file.read_text(encoding="utf-8"))
    assert fm["objective"]
    assert isinstance(fm["open_questions"], list)
    assert len(fm["open_questions"]) > 1


def test_campaign_objective_reaches_the_prep_page(paths):
    """Regression: the objective is prose, so the comma-splitting dialect
    returns it as a list; load_campaign_state used to accept only a str and
    silently fall back to "", so next.html rendered no objective at all."""
    from truehand.core.loaders import load_campaign_state
    objective = load_campaign_state(paths)["objective"]
    assert objective, "objective is empty despite being set in campaign-state.md"
    assert ", " in objective, "prose should be rejoined, not left as fragments"


def test_a_prose_objective_round_trips_through_the_dialect():
    from truehand.core.loaders import _rejoin_prose
    source = "Get the map, then run the route: Yackerty first, a portal after."
    fm, _ = parse_frontmatter(f"---\nobjective: {source}\n---\n")
    assert _rejoin_prose(fm["objective"]) == source


def test_rejoin_prose_leaves_a_plain_string_alone():
    from truehand.core.loaders import _rejoin_prose
    assert _rejoin_prose("  no commas here  ") == "no commas here"
    assert _rejoin_prose(None) == ""
