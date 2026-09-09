"""One parser for summary.md, with one set of heading rules.

The regressions these guard: the `*In brief:*` extraction existed in three
modules and the `##`-section walk in two, with divergent heading rules — the
prep hub normalized curly apostrophes and trailing colons, the image pipeline
only lowercased. A `## What's next` typed either way must now behave the same
everywhere.
"""


import pytest

from truehand.core.summary import SessionSummary

SAMPLE = """*In brief: The crew made landfall and lost a boat.*

## Fog on the docks

They came ashore in the dark. Nobody met them.

## The Bells and the Warning

Bells rang out over the water.

- a bullet inside a prose beat
- another

## What's next

- Find Harshnag
- Ask Naxene about the ledger
"""


@pytest.fixture(scope="module")
def doc():
    return SessionSummary.parse(SAMPLE)


class TestInBrief:
    def test_unwraps_the_lead_line(self, doc):
        assert doc.in_brief == "The crew made landfall and lost a boat."

    def test_absent_in_brief_is_empty_not_none(self):
        assert SessionSummary.parse("## Only a beat\n\nProse.").in_brief == ""

    def test_lead_line_falls_back_to_first_prose(self):
        doc = SessionSummary.parse("\n\n*A bare italic line.*\n\n## Beat\n")
        assert doc.in_brief == ""
        assert doc.lead_line == "A bare italic line."

    def test_lead_line_skips_headings_and_blanks(self):
        assert SessionSummary.parse("# Title\n\n\nActual prose.").lead_line == "Actual prose."


class TestBeats:
    def test_beats_are_in_document_order(self, doc):
        assert [b.title for b in doc.beats] == [
            "Fog on the docks", "The Bells and the Warning", "What's next"]

    def test_slug_matches_the_beat_image_filename(self, doc):
        assert doc.beats[1].slug == "the-bells-and-the-warning"

    def test_prose_beat_is_illustratable_even_with_bullets(self, doc):
        assert doc.beats[1].is_illustratable

    def test_forward_section_is_never_illustratable(self, doc):
        assert not doc.beats[2].is_illustratable

    def test_bullet_only_section_is_not_illustratable(self):
        doc = SessionSummary.parse("## Spoils\n\n- a rope\n- a lamp\n")
        assert doc.beats[0].bullets == ["a rope", "a lamp"]
        assert not doc.beats[0].is_illustratable

    def test_empty_section_is_not_illustratable(self):
        assert not SessionSummary.parse("## Empty\n\n").beats[0].is_illustratable

    def test_h3_is_not_a_beat(self):
        assert SessionSummary.parse("### Sub\n\nProse.").beats == ()

    def test_indented_heading_is_a_beat_to_neither_parser_nor_renderer(self):
        """Beats must line up 1:1 with the <h2>s md_to_html renders, since that
        is how beat images are placed."""
        from truehand.core.markdown import md_to_html
        md = "  ## Indented\n\nProse.\n"
        assert SessionSummary.parse(md).beats == ()
        assert "<h2>" not in md_to_html(md)


class TestForwardHeadingsAgreeEverywhere:
    @pytest.mark.parametrize("heading", [
        "What's next", "what's next", "Whats next", "Next steps",
        "Loose ends", "Loose Ends", "What's next:", "What’s next",
    ])
    def test_variants_are_all_forward_looking(self, heading):
        doc = SessionSummary.parse(f"## {heading}\n\n- a lead\n")
        assert doc.beats[0].is_forward_looking
        assert not doc.beats[0].is_illustratable
        assert doc.forward_sections == [doc.beats[0]]

    def test_a_story_beat_is_not_forward_looking(self, doc):
        assert not doc.beats[0].is_forward_looking

    def test_forward_section_without_bullets_is_dropped(self):
        doc = SessionSummary.parse("## Loose ends\n\nNothing in particular.\n")
        assert doc.beats[0].is_forward_looking
        assert doc.forward_sections == []


class TestAgainstTheRealArchive:
    def test_every_summary_leads_with_an_in_brief(self, paths):
        missing = [p.parent.name
                   for p in sorted(paths.sessions.glob("*/summary.md"))
                   if not SessionSummary.parse(p.read_text(encoding="utf-8")).in_brief]
        assert missing == []

    def test_every_beat_image_on_disk_matches_a_beat_slug(self, paths):
        orphans = {}
        for images in sorted(paths.sessions.glob("*/images")):
            summary_path = images.parent / "summary.md"
            if not summary_path.exists():
                continue
            doc = SessionSummary.parse(summary_path.read_text(encoding="utf-8"))
            slugs = {b.slug for b in doc.beats} | {"hero"}
            stray = {p.stem for p in images.iterdir()
                     if p.suffix in (".jpg", ".jpeg", ".png", ".webp")} - slugs
            if stray:
                orphans[images.parent.name] = stray
        assert orphans == {}
