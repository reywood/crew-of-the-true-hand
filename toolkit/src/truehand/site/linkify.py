"""Auto-linking entity names inside rendered HTML."""

import re

#: An element opts out of auto-linking with class="no-link". Matched as a real
#: class token, so it works in any position among several classes — the earlier
#: implementation tested four fixed substrings and silently missed
#: class="no-link extra".
NO_LINK_RE = re.compile(r"""class\s*=\s*["'][^"']*(?<![\w-])no-link(?![\w-])[^"']*["']""",
                        re.IGNORECASE)

TAG_RE = re.compile(r"^<\s*(/?)\s*([A-Za-z][A-Za-z0-9-]*)")

#: Elements with no closing tag; they never open a region.
VOID_ELEMENTS = frozenset({
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
})


def _compile(aliases):
    """One alternation over *aliases*, longest first so the longest name wins."""
    return re.compile(
        r"(?<![A-Za-z0-9])("
        + "|".join(re.escape(a) for a in sorted(aliases, key=lambda x: -len(x)))
        + r")(?![A-Za-z0-9])"
    )


class LinkIndex:
    """Compiled alias patterns for one build.

    Naively, every page compiles its own alternation over all ~245 aliases
    minus its own — and that compilation dominated the build (~0.55s of 0.77s
    across ~145 pages).

    It cannot simply be replaced by one shared pattern plus a skip in the
    substitution, because dropping a page's own alias from the alternation is
    what lets a *shorter* alias match inside that span. This archive has 32
    such overlapping pairs, e.g. "Umberlee" (an NPC) sits inside "Umberlee
    eye-coin" (an item), so on the item's page the plain name must still link.

    So: pages whose own aliases contain no other entity's alias share one
    pattern compiled once, and only the genuinely overlapping pages fall back
    to compiling their own. The result is byte-identical either way.
    """

    def __init__(self, link_map):
        self.link_map = link_map
        self._full = _compile(link_map) if link_map else None
        self._per_href = {}
        self._needs_own = self._find_overlapping_hrefs()

    def _find_overlapping_hrefs(self):
        """Hrefs whose own aliases contain another entity's alias inside them.

        Tested pairwise rather than by running the full pattern over each
        alias: that pattern is longest-first, so it matches the whole alias
        and consumes it, and the inner name is never seen. The cheap ``in``
        check prunes all but a handful of pairs before the boundary regex.
        """
        overlapping = set()
        for outer, outer_href in self.link_map.items():
            if outer_href in overlapping:
                continue
            for inner, inner_href in self.link_map.items():
                if (len(inner) >= len(outer) or inner_href == outer_href
                        or inner not in outer):
                    continue
                if re.search(r"(?<![A-Za-z0-9])" + re.escape(inner)
                             + r"(?![A-Za-z0-9])", outer):
                    overlapping.add(outer_href)
                    break
        return overlapping

    def pattern_for(self, current_href):
        """(pattern, skip_current) for a page.

        When ``skip_current`` is true the pattern still contains the page's own
        aliases and the caller must leave them unlinked.
        """
        if current_href not in self._needs_own:
            return self._full, True
        pattern = self._per_href.get(current_href)
        if pattern is None:
            aliases = [a for a, h in self.link_map.items() if h != current_href]
            pattern = _compile(aliases) if aliases else False
            self._per_href[current_href] = pattern
        return (pattern or None), False


#: Memo for the process-wide convenience wrapper below. The link map is built
#: once per build and never mutated, so identity is a sound cache key.
_INDEX = None


def index_for(link_map):
    global _INDEX
    if _INDEX is None or _INDEX.link_map is not link_map:
        _INDEX = LinkIndex(link_map)
    return _INDEX


def linkify_html(rendered, current_href, link_map):
    """Link the first mention of each entity, skipping protected regions.

    Regions skipped: inside an existing <a>, inside <code>/<pre>, and inside
    any element carrying class="no-link" — the last tracked by actual element
    nesting, so a nested <em> or <strong> no longer ends the protection early.
    """
    pattern, skip_current = index_for(link_map).pattern_for(current_href)
    if pattern is None:
        return rendered

    linked = set()
    parts = re.split(r"(<[^>]+>)", rendered)
    in_anchor = False
    in_code = False
    open_tags = []          # names of currently open elements
    no_link_depth = None    # len(open_tags) of the no-link element, if inside one

    def repl(m):
        alias = m.group(1)
        href = link_map[alias]
        if href in linked:
            return alias
        if skip_current and href == current_href:
            return alias
        linked.add(href)
        return f'<a class="entity-link" href="{href}">{alias}</a>'

    for i, part in enumerate(parts):
        if part.startswith("<") and part.endswith(">"):
            t = part.lower()
            if t.startswith("<a "):
                in_anchor = True
            elif t == "</a>":
                in_anchor = False
            elif t.startswith("<code") or t.startswith("<pre"):
                in_code = True
            elif t in ("</code>", "</pre>"):
                in_code = False

            m = TAG_RE.match(part)
            if m:
                closing = m.group(1) == "/"
                name = m.group(2).lower()
                if closing:
                    if open_tags:
                        if no_link_depth == len(open_tags):
                            no_link_depth = None
                        open_tags.pop()
                elif name not in VOID_ELEMENTS and not part.rstrip().endswith("/>"):
                    open_tags.append(name)
                    if no_link_depth is None and NO_LINK_RE.search(part):
                        no_link_depth = len(open_tags)
            continue

        if in_anchor or in_code or no_link_depth is not None or not part:
            continue
        parts[i] = pattern.sub(repl, part)
    return "".join(parts)
