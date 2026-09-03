"""Auto-linking, and the no-link protection that used to leak."""

from truehand.site.linkify import linkify_html

MAP = {"Toz": "pc-toz.html", "Hal": "pc-hal.html", "Halruaa": "loc-halruaa.html"}


def link(html, current="index.html", link_map=None):
    return linkify_html(html, current, link_map if link_map is not None else MAP)


def test_links_a_bare_mention():
    assert link("<p>Toz waves.</p>") == \
        '<p><a class="entity-link" href="pc-toz.html">Toz</a> waves.</p>'


def test_only_the_first_mention_of_an_entity_is_linked():
    out = link("<p>Toz and Toz.</p>")
    assert out.count("entity-link") == 1


def test_the_current_page_does_not_link_to_itself():
    assert "entity-link" not in link("<p>Toz waves.</p>", current="pc-toz.html")


def test_longer_aliases_win():
    """Hal must not match inside Halruaa."""
    out = link("<p>Halruaa is far.</p>")
    assert 'href="loc-halruaa.html"' in out
    assert 'href="pc-hal.html"' not in out


def test_skips_inside_an_existing_anchor():
    html = '<p><a href="x.html">Toz</a></p>'
    assert link(html) == html


def test_skips_inside_code_and_pre():
    assert link("<p><code>Toz</code></p>") == "<p><code>Toz</code></p>"
    assert link("<pre>Toz</pre>") == "<pre>Toz</pre>"


class TestNoLink:
    def test_protects_a_simple_span(self):
        html = '<p><span class="no-link">Toz</span></p>'
        assert link(html) == html

    def test_protection_survives_a_nested_tag(self):
        """Regression: a nested </em> used to decrement the depth counter to
        zero, so everything after it in the span got linked anyway."""
        html = '<p><span class="no-link">Toz <em>the</em> Hal</span></p>'
        assert link(html) == html

    def test_protection_survives_several_nested_tags(self):
        html = ('<div class="no-link"><p>Toz</p><p><strong>Hal</strong></p>'
                '<p>Halruaa</p></div>')
        assert link(html) == html

    def test_protection_ends_at_the_right_closing_tag(self):
        html = '<p><span class="no-link">Toz</span> then Hal</p>'
        out = link(html)
        assert '<span class="no-link">Toz</span>' in out
        assert 'href="pc-hal.html"' in out

    def test_class_may_appear_in_any_position(self):
        """Regression: the old substring test only caught no-link when it was
        the whole class list or the last entry."""
        for cls in ("no-link", "no-link extra", "extra no-link",
                    "a no-link b"):
            html = f'<p><span class="{cls}">Toz</span></p>'
            assert link(html) == html, cls

    def test_a_similarly_named_class_is_not_treated_as_no_link(self):
        html = '<p><span class="no-linkage">Toz</span></p>'
        assert "entity-link" in link(html)

    def test_single_quoted_attribute(self):
        html = "<p><span class='no-link'>Toz</span></p>"
        assert link(html) == html

    def test_a_void_element_does_not_open_a_region(self):
        html = '<p><img class="no-link" src="x.png"> Toz</p>'
        assert "entity-link" in link(html)


class TestSharedPatternEquivalence:
    """The shared-pattern optimization must match the naive per-page build.

    LinkIndex compiles one alternation for most pages instead of one per page.
    That is only sound where a page's own aliases contain no other entity's
    alias — otherwise dropping the page's alias is what lets the shorter name
    match. These tests pin both halves of that.
    """

    @staticmethod
    def naive(rendered, current_href, link_map):
        """The original approach: recompile per page, excluding own aliases."""
        import re
        aliases = [a for a, h in link_map.items() if h != current_href]
        if not aliases:
            return rendered
        aliases.sort(key=lambda x: -len(x))
        pattern = re.compile(
            r"(?<![A-Za-z0-9])(" + "|".join(re.escape(a) for a in aliases)
            + r")(?![A-Za-z0-9])"
        )
        linked = set()
        parts = re.split(r"(<[^>]+>)", rendered)

        def repl(m):
            alias = m.group(1)
            href = link_map[alias]
            if href in linked:
                return alias
            linked.add(href)
            return f'<a class="entity-link" href="{href}">{alias}</a>'

        for i, part in enumerate(parts):
            if part.startswith("<") and part.endswith(">"):
                continue
            parts[i] = pattern.sub(repl, part)
        return "".join(parts)

    def test_overlapping_page_still_links_the_inner_name(self):
        """The case the optimization must NOT break: on the item's own page,
        the NPC's plain name inside the item's alias still links."""
        lm = {"Umberlee": "npc-umberlee.html",
              "Umberlee eye-coin": "item-umberlee-eye-coin.html"}
        html = "<p>The Umberlee eye-coin sat there.</p>"
        out = linkify_html(html, "item-umberlee-eye-coin.html", lm)
        assert 'href="npc-umberlee.html"' in out
        assert out == self.naive(html, "item-umberlee-eye-coin.html", lm)

    def test_matches_the_naive_implementation_on_the_real_archive(self, paths):
        """Every real page, both paths, byte-for-byte."""
        from truehand.core.entity import build_link_map
        from truehand.core.loaders import (
            load_dir_entities,
            load_pcs,
            load_quests,
            load_sessions,
        )
        entities = (load_pcs(paths)
                    + load_dir_entities("npc", paths.npcs)
                    + load_dir_entities("location", paths.locations)
                    + load_dir_entities("item", paths.items)
                    + load_quests(paths)
                    + load_sessions(paths))
        link_map = build_link_map(entities)
        sample = ("<p>The Umberlee eye-coin and the Waterdeep Wazoo, plus "
                  "Xolkin's gift and the Umberlee priestess at the Plinth. "
                  "Toz and Hal walked from Waterdeep to Nightstone.</p>")
        hrefs = ["index.html", "sessions.html"] + [e.href for e in entities]
        assert len(hrefs) > 100
        for href in hrefs:
            assert linkify_html(sample, href, link_map) == \
                self.naive(sample, href, link_map), f"diverged on {href}"
