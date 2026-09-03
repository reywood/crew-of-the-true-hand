"""Auto-linking entity names inside rendered HTML."""

import re


def linkify_html(rendered, current_href, link_map):
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
    no_link_depth = 0
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
            elif 'class="no-link"' in t or "class='no-link'" in t or ' no-link"' in t or ' no-link\'' in t:
                no_link_depth += 1
            elif no_link_depth > 0 and t.startswith("</"):
                no_link_depth -= 1
            continue
        if in_anchor or in_code or no_link_depth > 0 or not part:
            continue

        def repl(m):
            alias = m.group(1)
            href = link_map[alias]
            if href in linked:
                return alias
            linked.add(href)
            return f'<a class="entity-link" href="{href}">{alias}</a>'

        parts[i] = pattern.sub(repl, part)
    return "".join(parts)
