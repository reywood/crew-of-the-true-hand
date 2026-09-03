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


def linkify_html(rendered, current_href, link_map):
    """Link the first mention of each entity, skipping protected regions.

    Regions skipped: inside an existing <a>, inside <code>/<pre>, and inside
    any element carrying class="no-link" — the last tracked by actual element
    nesting, so a nested <em> or <strong> no longer ends the protection early.
    """
    aliases = [a for a, h in link_map.items() if h != current_href]
    if not aliases:
        return rendered
    aliases.sort(key=lambda x: -len(x))
    pattern = re.compile(
        r"(?<![A-Za-z0-9])(" + "|".join(re.escape(a) for a in aliases) + r")(?![A-Za-z0-9])"
    )
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
